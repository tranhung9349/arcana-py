"""SSE transport, worker ownership, signed replay and spend limits."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
import json
from threading import Event
import time
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from randomyst.ai_client import CompatibleAIClient
from randomyst.ai_jobs import ReadingJob, reading_events
from randomyst.ai_service import AIReadingRequest
from randomyst.api import create_app
from randomyst.engine import EngineError
from randomyst.security import SecurityConfig
from tests.bazi_pipeline_fixtures import analysis_for, life_for, prose_for
from tests.test_ai_readings import CONFIG, FakeAI
from tests.test_bazi_consultations import payload
from tests.test_coin_consultations import payload as coin_payload
from tests.browser_client import TestClient as BrowserClient


def provider_stream(value, *, finish="stop", done=True):
    text = json.dumps(value, ensure_ascii=False)
    rows = [b": provider heartbeat\r\n\r\n"]
    for i in range(0, len(text), 41):
        delta = {"content": text[i:i+41], "reasoning_content": "private-reasoning-sentinel"}
        rows.append(("data: " + json.dumps({"model": "stream-model", "choices": [{"index": 0, "delta": delta}]}, ensure_ascii=False) + "\r\n\r\n").encode())
    rows.append(("data: " + json.dumps({"choices": [{"index": 0, "delta": {}, "finish_reason": finish}]}) + "\n\n").encode())
    rows.append(b'data: {"choices":[],"usage":{"total_tokens":42,"prompt_tokens":20,"private":"ignored"}}\n\n')
    if done:
        rows.append(b"data: [DONE]\n\n")
    return BytesIO(b"".join(rows))


def wait_finished(job):
    deadline = time.monotonic() + 5
    while job.snapshot()[2] is None and time.monotonic() < deadline:
        time.sleep(0.005)
    if job.snapshot()[2] is None:
        raise AssertionError("Worker did not finish")
    return job.snapshot()


class StreamingTransportTests(unittest.TestCase):
    def test_json_is_assembled_from_sse_content_only_and_usage_is_not_double_counted(self):
        opener = Mock();opener.open.return_value = provider_stream({"text": "Nạp âm Sơn Đầu Hỏa"})
        reserve = Mock()
        result, metadata = CompatibleAIClient(CONFIG, opener, reserve).complete([], stream=True)
        self.assertEqual(result, {"text": "Nạp âm Sơn Đầu Hỏa"})
        self.assertEqual(metadata, {"model": "stream-model", "usage": {"total_tokens": 42, "prompt_tokens": 20}})
        request = opener.open.call_args.args[0]
        body = json.loads(request.data)
        self.assertTrue(body["stream"]);self.assertEqual(body["stream_options"], {"include_usage": True})
        self.assertEqual(request.get_header("Accept"), "text/event-stream")
        reserve.assert_called_once()

    def test_eof_length_errors_and_invalid_frames_never_publish_partial_json_or_retry(self):
        for response in [provider_stream({"valid": True}, done=False), provider_stream({}, finish="length"),
                         BytesIO(b'data: {"error":{"message":"private-sentinel"}}\n\n'),
                         BytesIO(b'data: invalid-private-sentinel\n\n'), BytesIO(b"data: " + b"x"*1_048_577)]:
            opener = Mock();opener.open.return_value = response
            with self.assertRaises(EngineError) as caught:
                CompatibleAIClient(CONFIG, opener).complete([], stream=True)
            self.assertNotIn("private-sentinel", str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)

    def test_idle_failure_after_a_chunk_is_not_automatically_billed_twice(self):
        response = Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.headers={}
        response.readline.side_effect=[b'data: {"choices":[{"delta":{"content":"{"}}]}\n', b'\n', TimeoutError("private-sentinel")]
        opener=Mock();opener.open.return_value=response
        with self.assertRaises(EngineError) as caught:
            CompatibleAIClient(CONFIG, opener).complete([], stream=True)
        self.assertEqual(caught.exception.code,"AI_CONNECTION_FAILED");self.assertEqual(opener.open.call_count,1)

    def test_total_deadline_stops_even_a_provider_sending_only_heartbeats(self):
        opener=Mock();opener.open.return_value=BytesIO(b": heartbeat\n\n"*20)
        with patch("randomyst.ai_client.time.monotonic", side_effect=[0, 0, 1, 601]):
            with self.assertRaises(EngineError) as caught:
                CompatibleAIClient(CONFIG, opener).complete([], stream=True)
        self.assertEqual(caught.exception.code,"AI_CONNECTION_FAILED")

    def test_gateway_returning_json_despite_stream_true_does_not_cause_a_second_call(self):
        response=BytesIO(b'{"choices":[{"message":{"content":"{}"},"finish_reason":"stop"}]}')
        response.headers={"Content-Type":"application/json"}
        opener=Mock();opener.open.return_value=response
        result,_=CompatibleAIClient(CONFIG,opener).complete([],stream=True)
        self.assertEqual(result,{});self.assertEqual(opener.open.call_count,1)


class ReadingJobTests(unittest.TestCase):
    def setUp(self):
        self.fake=FakeAI()
        self.app=create_app(ai_config=CONFIG,ai_client=self.fake,security_config=SecurityConfig(signing_key=b"s"*32))
        self.client=TestClient(self.app)
        saved=self.client.post('/api/v1/bazi/consultations',json=payload())
        self.request={"method":"BAZI","consultation_id":saved.json()["request_id"],
            "consultation":{"kind":"BAZI","data":saved.json(),"signature":saved.headers["x-arcana-signature"]}}
        self.model=AIReadingRequest.model_validate(self.request)

    def tearDown(self):
        if self.fake.release:
            self.fake.release.set()
        for job in self.app.state.ai._jobs.values():
            wait_finished(job)
        self.client.close()

    def test_observing_missing_job_is_read_only_and_rejects_modified_snapshots(self):
        response=self.client.post('/api/v1/ai/readings/stream',json=self.request)
        self.assertEqual(response.status_code,200);self.assertIn('event: missing',response.text)
        self.assertEqual(response.headers['x-accel-buffering'],'no')
        self.assertEqual(response.headers['cache-control'],'no-store')
        bad=deepcopy(self.request);bad['consultation']['signature']='0'*64
        for endpoint in ('start','stream'):
            self.assertEqual(self.client.post('/api/v1/ai/readings/'+endpoint,json=bad).status_code,422)
        self.assertEqual(self.fake.calls,0);self.assertEqual(self.app.state.ai_budget.attempts,0)

    def test_disconnect_only_closes_observer_and_reconnect_joins_one_paid_worker(self):
        self.fake.started=Event();self.fake.release=Event()
        job=self.app.state.ai.subscribe(self.model,generate=True)
        self.assertTrue(self.fake.started.wait(3))
        async def disconnect():
            observer=reading_events(job,heartbeat=0,poll=0)
            self.assertIn('ANALYZING',await anext(observer))
            self.assertEqual(await anext(observer),': keep-alive\n\n')
            await observer.aclose()
        asyncio.run(disconnect())
        self.assertIs(self.app.state.ai.subscribe(self.model),job)
        self.assertIs(self.app.state.ai.subscribe(self.model,generate=True),job)
        with self.assertRaises(EngineError) as caught:self.app.state.ai.execute(self.model)
        self.assertEqual(caught.exception.code,'AI_BUSY')
        self.fake.release.set();snapshot=wait_finished(job)
        self.assertIsNone(snapshot[4]);self.assertEqual(self.fake.calls,2)
        response=self.client.post('/api/v1/ai/readings/stream',json=self.request)
        self.assertIn('event: result',response.text)
        self.assertNotIn('bazi_analysis',response.text);self.assertNotIn('technical_overview',response.text)
        self.assertEqual(self.fake.calls,2);self.assertEqual(self.app.state.ai_budget.attempts,2)

    def test_real_streaming_transport_runs_both_roles_and_validates_before_final_event(self):
        requests=[]
        class Opener:
            def open(_,request,**kwargs):
                body=json.loads(request.data);requests.append(body)
                incoming=json.loads(body['messages'][-1]['content'])
                result=(analysis_for(incoming['verified_context'],whole_life=incoming.get('reading_scope')=='WHOLE_LIFE') if incoming['stage']=='BAZI_STRUCTURAL_ANALYST'
                        else prose_for(incoming['analysis_result']) if incoming['analysis_result'].get('whole_life') else life_for(incoming['analysis_result']))
                return provider_stream(result)
        self.app.state.ai.client=CompatibleAIClient(CONFIG,Opener(),self.app.state.ai_budget.reserve)
        response=self.client.post('/api/v1/ai/readings/start',json=self.request)
        self.assertEqual(response.status_code,200);self.assertIn('event: result',response.text)
        self.assertEqual([row['max_tokens'] for row in requests],[24000,12000])
        self.assertTrue(all(row['stream'] for row in requests))
        self.assertEqual(self.app.state.ai_budget.attempts,2)
        result=self.app.state.ai.lookup(self.model)
        self.assertEqual(result['usage']['total_tokens'],84)
        self.assertNotIn('private-reasoning-sentinel',response.text)

    def test_worker_error_is_terminal_until_an_explicit_new_start_and_contains_no_raw_exception(self):
        original=self.fake.complete
        self.fake.complete=Mock(side_effect=RuntimeError('private-birth-key-sentinel'))
        job=self.app.state.ai.subscribe(self.model,generate=True);wait_finished(job)
        for _ in range(2):
            response=self.client.post('/api/v1/ai/readings/stream',json=self.request)
            self.assertIn('event: error',response.text);self.assertIn('AI_FAILED',response.text)
            self.assertNotIn('private-birth-key-sentinel',response.text)
        self.assertEqual(self.fake.complete.call_count,1)
        self.fake.complete=original
        self.assertIn('event: result',self.client.post('/api/v1/ai/readings/start',json=self.request).text)
        self.assertEqual(self.fake.calls,2)

    def test_two_invalid_analyses_emit_only_error_and_leave_no_partial_result(self):
        self.fake.malformed=True
        response=self.client.post('/api/v1/ai/readings/start',json=self.request)
        self.assertIn('event: error',response.text);self.assertNotIn('event: result',response.text)
        self.assertNotIn('technical_overview',response.text)
        self.assertEqual(self.fake.calls,2);self.assertIsNone(self.app.state.ai.lookup(self.model))

    def test_completed_job_cannot_bypass_cache_revalidation_or_ttl(self):
        job=self.app.state.ai.subscribe(self.model,generate=True);wait_finished(job)
        key=next(iter(self.app.state.ai._cache))
        expiry,raw=self.app.state.ai._cache[key]
        bad=json.loads(raw);bad['bazi_analysis']['context_id']='wrong'
        self.app.state.ai._cache[key]=(expiry,json.dumps(bad))
        self.assertIsNone(self.app.state.ai.subscribe(self.model))
        job.finished_at=time.monotonic()-901
        self.assertIsNone(self.app.state.ai.subscribe(self.model));self.assertEqual(len(self.app.state.ai._jobs),0)
        self.assertEqual(self.fake.calls,2)

    def test_concurrency_limit_includes_detached_workers(self):
        self.fake.started=Event();self.fake.release=Event()
        first=self.app.state.ai.subscribe(self.model,generate=True);self.assertTrue(self.fake.started.wait(3))
        models=[]
        for _ in range(2):
            saved=self.client.post('/api/v1/bazi/consultations',json=payload())
            models.append(AIReadingRequest.model_validate({"method":"BAZI","consultation_id":saved.json()['request_id'],
                "consultation":{"kind":"BAZI","data":saved.json(),"signature":saved.headers['x-arcana-signature']}}))
        second=self.app.state.ai.subscribe(models[0],generate=True)
        with self.assertRaises(EngineError) as caught:self.app.state.ai.subscribe(models[1],generate=True)
        self.assertEqual(caught.exception.code,'AI_RATE_LIMITED')
        self.fake.release.set();wait_finished(first);wait_finished(second)
        self.assertEqual(self.fake.calls,4)

    def test_observations_do_not_consume_the_hourly_start_limit(self):
        app=create_app(ai_config=CONFIG,ai_client=FakeAI(),security_config=replace(self.app.state.security,ai_per_hour=1))
        with TestClient(app) as client:
            self.assertIn('event: result',client.post('/api/v1/ai/readings/start',json=self.request).text)
            for _ in range(3):self.assertEqual(client.post('/api/v1/ai/readings/stream',json=self.request).status_code,200)
            self.assertEqual(client.post('/api/v1/ai/readings/start',json=self.request).status_code,429)


class LiuYaoStreamingTests(unittest.TestCase):
    def setUp(self):
        self.fake=FakeAI();self.requests=[]
        owner=self
        class Opener:
            def open(_,request,**kwargs):
                body=json.loads(request.data);owner.requests.append(body)
                output,_=owner.fake.complete(body['messages'])
                return provider_stream(output)
        self.app=create_app(ai_config=CONFIG,ai_client=CompatibleAIClient(CONFIG,Opener()),
                            security_config=SecurityConfig(signing_key=b's'*32))
        self.client=BrowserClient(self.app)
        saved=self.client.post('/api/v1/coins/consultations',json=coin_payload()).json()
        analysis=self.client.post('/api/v1/coins/consultations/'+saved['request_id']+'/analysis',json={'topic':'CAREER'}).json()
        self.request=self.client.enrich({'method':'LIUYAO','consultation_id':saved['request_id'],
            'analysis_context':analysis['context'],'analysis_rules_sha256':analysis['rules_sha256']})

    def tearDown(self):
        self.client.close()

    def test_liuyao_sse_entrypoint_sends_stream_true_with_grounded_context(self):
        response=self.client.post('/api/v1/ai/readings/start',json=self.request)
        self.assertEqual(response.status_code,200)
        self.assertIn('event: result',response.text)
        self.assertEqual(len(self.requests),1)
        self.assertIs(self.requests[0]['stream'],True)
        context=json.loads(self.requests[0]['messages'][-1]['content'])
        self.assertIn('chart:original',{f['id'] for f in context['facts']})
        self.assertTrue(any(e['id'].startswith('iching__') for e in context['evidence']))

    def test_legacy_json_entrypoint_also_consumes_upstream_stream_and_propagates_errors(self):
        self.fake.malformed=True
        with self.assertLogs('arcana.ai',level='WARNING') as logs:
            response=self.client.post('/api/v1/ai/readings',json=self.request)
        self.assertEqual(response.status_code,502)
        self.assertEqual(response.json()['error']['code'],'AI_RESPONSE_UNBOUND')
        self.assertEqual(len(self.requests),2)
        self.assertTrue(all(r['stream'] for r in self.requests))
        self.assertTrue(any('REFERENCE_MISMATCH' in row for row in logs.output))
        self.assertTrue(any('stream=True' in row for row in logs.output))
        self.assertNotIn('Việc hợp tác',' '.join(logs.output))

    def test_single_repair_keeps_stream_true_and_failed_articles_are_not_cached(self):
        self.fake.fail_first=True
        response=self.client.post('/api/v1/ai/readings/start',json=self.request)
        self.assertIn('event: result',response.text)
        self.assertEqual(len(self.requests),2)
        self.assertTrue(all(r['stream'] for r in self.requests))
        self.assertEqual(self.app.state.ai.lookup(AIReadingRequest.model_validate(self.request))['generation_passes'],2)


if __name__ == '__main__':unittest.main()
