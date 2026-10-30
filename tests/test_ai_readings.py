"""Shared AI transport, immutable input, paid-call deduplication and API coverage."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
from threading import Event
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from uuid import uuid4

from tests.browser_client import TestClient

from randomyst.ai_client import AIConfig, CompatibleAIClient, NoRedirect
from randomyst.ai_context import maihoa_context, liuyao_context
from randomyst.ai_service import AIReadingRequest, AIReadingResult
from randomyst.api import create_app
from randomyst.engine import EngineError
from tests.test_bazi_consultations import payload as bazi_payload
from tests.test_coin_consultations import payload as coin_payload
from tests.test_maihoa_consultations import payload as maihoa_payload

ROOT = Path(__file__).resolve().parents[1]
CONFIG = AIConfig("https://example.test/v1", "test-model", "private-test-key", 10)


class FakeAI:
    def __init__(self):
        self.calls = 0
        self.contexts = []
        self.malformed = False
        self.fail_first = False
        self.started = None
        self.release = None

    def complete(self, messages):
        self.calls += 1
        payload = json.loads(messages[-1]["content"])
        context = payload.get("verified_context", payload.get("analysis_result", payload))
        self.contexts.append(context)
        if self.started:
            self.started.set()
            if not self.release.wait(5): raise RuntimeError("test gate timeout")
        if payload.get("stage") in ("BAZI_STRUCTURAL_ANALYST", "BAZI_LIFE_INTERPRETER"):
            from tests.bazi_pipeline_fixtures import analysis_for, life_for, prose_for
            if payload["stage"] == "BAZI_STRUCTURAL_ANALYST":
                output = analysis_for(context, whole_life=payload.get('reading_scope')=='WHOLE_LIFE')
                if self.malformed or (self.fail_first and self.calls == 1):
                    output["patterns"][0]["basis"][0]["fact_refs"] = ["invented:fact"]
            else:
                output = prose_for(context) if context.get('whole_life') else life_for(context)
            return output, {"model": "test-model-returned", "usage": {"total_tokens": 100}}
        claim = {"label": "AI_INTERPRETATION", "text": "Dữ kiện được giữ nguyên để giải thích theo câu hỏi.",
                 "fact_refs": [context["facts"][0]["id"]], "evidence_refs": [context["evidence"][0]["id"]]}
        output = {"schema_version": "plain-reading-response-v2", "context_id": context["context_id"],
                  "summary": deepcopy(claim), "analysis": [deepcopy(claim), deepcopy(claim)],
                  "practical_options": [{"kind": "MODERN_APPLICATION", "text": "Bạn có thể kiểm tra điều kiện thực tế của việc đang hỏi.", "fact_refs": claim["fact_refs"]}],
                  "limits": [context["limitations"][0]]}
        if self.malformed or (self.fail_first and self.calls==1): output["summary"]["fact_refs"] = ["invented:fact"]
        return output, {"model": "test-model-returned", "usage": {"total_tokens": 100}}


class AITransportTests(unittest.TestCase):
    def test_private_config_environment_precedence_and_safe_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.env"
            path.write_text("RANDOMYST_AI_API_KEY=sentinel-secret\nRANDOMYST_AI_BASE_URL=https://example.test/v1\nRANDOMYST_AI_MODEL=one\n")
            config = AIConfig.load(path, {"RANDOMYST_AI_MODEL": "two"})
            self.assertTrue(config.configured)
            self.assertEqual(config.model, "two")
            self.assertNotIn("sentinel-secret", repr(config))
            self.assertNotIn("sentinel-secret", json.dumps(config.public_status()))
            self.assertEqual(AIConfig.load(path, {"RANDOMYST_AI_TIMEOUT_SECONDS":"180"}).timeout,180)
            with self.assertRaises(ValueError):AIConfig.load(path, {"RANDOMYST_AI_TIMEOUT_SECONDS":"181"})
            for url in ("http://example.test/v1", "https://key@example.test/v1", "https://example.test/v1?key=bad"):
                with self.assertRaises(ValueError):
                    AIConfig.load(path, {"RANDOMYST_AI_BASE_URL": url})

    def test_compatible_post_uses_configured_endpoint_and_json_mode(self):
        response = {"model": "returned-model", "choices": [{"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 12, "total_tokens": 14, "secret_extra": "not exposed"}}
        opener = Mock()
        opener.open.return_value = BytesIO(json.dumps(response).encode())
        result, metadata = CompatibleAIClient(CONFIG, opener).complete([{"role": "user", "content": "sample"}])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer private-test-key")
        self.assertEqual(json.loads(request.data)["response_format"], {"type": "json_object"})
        self.assertEqual(json.loads(request.data)["max_tokens"], 12000)
        self.assertEqual(result, {"ok": True})
        self.assertEqual(metadata["usage"], {"prompt_tokens": 12, "total_tokens": 14})
        self.assertIsNone(NoRedirect().redirect_request(request, None, 302, "", {}, "https://other.test"))

    def test_reasoning_effort_is_sent_only_when_configured_without_temperature(self):
        opener=Mock();opener.open.return_value=BytesIO(json.dumps({'choices':[{'message':{'content':'{}'}}]}).encode())
        CompatibleAIClient(replace(CONFIG,reasoning_effort='low'),opener).complete([])
        body=json.loads(opener.open.call_args.args[0].data)
        self.assertEqual(body['reasoning_effort'],'low');self.assertNotIn('temperature',body)

    def test_timeout_and_auth_errors_do_not_echo_remote_body_or_retry_uncertain_call(self):
        opener = Mock()
        for failure, expected in [(URLError("private-test-key"), "AI_CONNECTION_FAILED"),
                                  (HTTPError("https://example.test", 401, "private-test-key", {}, BytesIO(b"private-test-key")), "AI_AUTH_FAILED")]:
            opener.reset_mock();opener.open.side_effect = failure
            with self.assertRaises(EngineError) as caught:
                CompatibleAIClient(CONFIG, opener).complete([])
            self.assertEqual(caught.exception.code, expected)
            self.assertNotIn("private-test-key", str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)

    def test_truncated_or_invalid_content_is_not_accepted(self):
        for choice in [{"message": {"content": "{}"}, "finish_reason": "length"},
                       {"message": {"content": "not json"}, "finish_reason": "stop"}]:
            opener = Mock();opener.open.return_value = BytesIO(json.dumps({"choices": [choice]}).encode())
            with self.assertRaises(EngineError): CompatibleAIClient(CONFIG, opener).complete([])

    def test_transient_http_retries_are_bounded(self):
        opener = Mock()
        opener.open.side_effect = [HTTPError("", 503, "", {}, BytesIO()),
                                  BytesIO(json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode())]
        with patch("randomyst.ai_client.time.sleep"):
            CompatibleAIClient(CONFIG, opener).complete([])
        self.assertEqual(opener.open.call_count, 2)


class AIReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = FakeAI()
        self.path = Path(self.tmp.name) / "app.sqlite3"
        self.app = create_app(self.path, CONFIG, self.fake)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close();self.tmp.cleanup()

    def natal(self):
        response = self.client.post("/api/v1/bazi/consultations", json=bazi_payload())
        self.assertEqual(response.status_code, 200)
        data = response.json()
        return data, {"method": "BAZI", "consultation_id": data["request_id"]}

    def test_bazi_cache_replay_survives_restart_without_altering_snapshot(self):
        saved, request = self.natal()
        self.assertIsNone(self.client.post("/api/v1/ai/readings/lookup", json=request).json())
        self.assertEqual(self.fake.calls, 0)
        first = self.client.post("/api/v1/ai/readings", json=request)
        self.assertEqual(first.status_code, 200, first.text)
        AIReadingResult.model_validate(first.json())
        self.assertEqual(self.client.post("/api/v1/ai/readings", json=request).json(), first.json())
        self.assertEqual(self.fake.calls, 2)
        self.assertEqual(self.client.get('/api/v1/bazi/consultations/'+saved['request_id']).json(), saved)
        other = FakeAI()
        with TestClient(create_app(self.path, CONFIG, other), storage=self.client.storage) as c:
            self.assertEqual(c.post("/api/v1/ai/readings/lookup", json=request).json(), first.json())
        self.assertEqual(other.calls, 0)
        self.assertNotIn(CONFIG.api_key, first.text)

    def test_saved_topic_reading_and_question_are_loaded_by_owner(self):
        saved, initial = self.natal()
        reading_id = str(uuid4())
        self.client.post('/api/v1/bazi/consultations/'+saved['request_id']+'/readings',
                         json={"reading_id": reading_id, "topic": "CAREER", "question": "Tôi nên chú ý gì khi nhận việc?"}).raise_for_status()
        request = {**initial, "bazi_reading_id": reading_id}
        self.client.post('/api/v1/ai/readings', json=request).raise_for_status()
        self.assertEqual(self.fake.contexts[-1]["topic"], "CAREER")
        self.assertEqual(self.fake.contexts[-1]["question"], "Tôi nên chú ý gì khi nhận việc?")
        other, other_request = self.natal()
        self.assertEqual(self.client.post('/api/v1/ai/readings', json={**other_request, "bazi_reading_id": reading_id}).status_code, 404)
        self.assertEqual(self.fake.calls, 2)

    def test_actual_prompt_message_change_invalidates_cache_without_overwriting_prior_reading(self):
        _, request = self.natal()
        first = self.client.post('/api/v1/ai/readings', json=request).json()
        from randomyst.ai_service import prepare_analyst
        def changed(*args, **kwargs):
            result = prepare_analyst(*args, **kwargs)
            result['messages'][0]['content'] += '\nA trusted editorial change.'
            result['messages_sha256'] = 'f' * 64
            return result
        with patch('randomyst.ai_service.prepare_analyst', side_effect=changed):
            packed=self.client.enrich(request)
            self.assertIsNone(self.app.state.ai.lookup(AIReadingRequest.model_validate(packed)))
            second = self.app.state.ai.execute(AIReadingRequest.model_validate(packed))
        self.assertNotEqual(first['reading_id'], second['reading_id'])
        self.assertEqual(self.client.post('/api/v1/ai/readings/lookup', json=request).json(), first)
        self.assertEqual(self.fake.calls, 4)

    def test_source_guidance_enriches_natal_snapshot_without_new_assessment(self):
        saved, request = self.natal()
        response = self.client.post('/api/v1/ai/readings', json=request).json()
        ctx = response['context']
        self.assertTrue(any(e['id'] == 'ziping:formation' for e in ctx['evidence']))
        assessment = json.loads(next(f['text'] for f in ctx['facts'] if f['id'] == 'assessment:snapshot'))
        self.assertEqual(assessment, saved['assessment'])
        self.assertEqual(self.client.get('/api/v1/bazi/consultations/'+saved['request_id']).json(), saved)

    def test_liuyao_source_target_code_is_unambiguous_without_rewriting_saved_finding(self):
        coin = self.client.post('/api/v1/coins/consultations', json=coin_payload()).json()
        analysis = self.client.post('/api/v1/coins/consultations/'+coin['request_id']+'/analysis', json={'topic':'DOCUMENT'}).json()
        original = deepcopy(analysis)
        ctx = liuyao_context(coin, analysis)
        anchors = json.loads(next(f.text for f in ctx.facts if f.id == 'reading:anchors'))
        self.assertEqual(anchors['world_key'], 'L3')
        relation = json.loads(next(f.text for f in ctx.facts if f.id == 'relation:use_world'))
        self.assertEqual((relation['source_key'],relation['target_key'],relation['relation']), ('L4','L3','GENERATES'))
        finding = next(f for f in analysis['findings'] if f['rule']=='USE_WORLD')
        self.assertIn('Dụng L4 sinh Thế L3', next(f.text for f in ctx.findings if f.id==finding['id']))
        self.assertNotIn('Chiều Thế → Dụng', next(e.text for e in ctx.evidence if e.id=='engine:'+finding['id']))
        self.assertEqual(analysis, original)
        self.assertTrue(any(e.id=='ly:effective' for e in ctx.evidence))
        self.assertIn('WORLD_CONDITIONED', ctx.signals)
        from research_tools.interpretation_prompt import build_messages
        self.assertEqual(build_messages(ctx)['reading_plan']['primary_id'], 'liuyao-world')
        without_assessment = deepcopy(analysis)
        without_assessment['findings'] = [f for f in without_assessment['findings'] if f['rule'] != 'WORLD_CAPACITY']
        self.assertNotIn('WORLD_CONDITIONED', liuyao_context(coin, without_assessment).signals)
        self.assertIn('line:L1', {f.id for f in ctx.facts})
        for finding in ctx.findings:
            self.assertNotIn('line:L1', finding.fact_refs)
        self.assertTrue({'line:L'+str(i) for i in range(1,7)} <= {f.id for f in ctx.facts})
        provenance = json.loads(next(f.text for f in ctx.facts if f.id == 'reading:provenance'))
        self.assertEqual(set(provenance['assessed_line_keys']), {'L3','L4','L6'})

    def test_liuyao_career_question_keeps_casting_conditions_separate_from_future_duration(self):
        payload = coin_payload()
        payload['question'] = 'Tôi sẽ tiếp tục được công việc hiện tại trong tháng 12/2026 hay không và công việc của tôi sẽ kéo dài bao lâu nữa?'
        coin = self.client.post('/api/v1/coins/consultations', json=payload).json()
        analysis = self.client.post('/api/v1/coins/consultations/'+coin['request_id']+'/analysis', json={'topic':'CAREER', 'intent_mode':'COMBINED'}).json()
        before = deepcopy(analysis)
        ctx = liuyao_context(coin, analysis)
        self.assertEqual(ctx.question, payload['question'])
        self.assertEqual(ctx.topic, 'CAREER')
        self.assertIn('Chưa tính riêng', next(f.text for f in ctx.facts if f.id == 'reading:time_scope'))
        scope = next(f for f in ctx.findings if f.id == 'scope:time')
        self.assertEqual(scope.status, 'UNRESOLVED')
        self.assertEqual(scope.fact_refs, ['reading:time_scope'])
        self.assertEqual(analysis, before)
        from research_tools.interpretation_prompt import build_messages
        messages = build_messages(ctx)['messages']
        self.assertIn('summary phải trả lời đủ hai ý', messages[0]['content'])
        self.assertIn('không chuyển sang tuyển dụng', messages[0]['content'])
        self.assertIn('không đổi chúng thành', messages[0]['content'])
        self.assertEqual(json.loads(messages[-1]['content'])['question'], payload['question'])

    def test_maihoa_and_liuyao_adapters_preserve_methods_and_selected_focus(self):
        maihoa = self.client.post('/api/v1/maihoa/consultations', json=maihoa_payload()).json()
        coin = self.client.post('/api/v1/coins/consultations', json=coin_payload()).json()
        analysis = self.client.post('/api/v1/coins/consultations/'+coin['request_id']+'/analysis', json={"topic": "PARTNERSHIP"}).json()
        with patch('randomyst.time_engine.pillars', side_effect=AssertionError('No calendar recalculation')), \
             patch('randomyst.maihoa_service.MaiHoaService.consult', side_effect=AssertionError('No new casting')), \
             patch('randomyst.liuyao_analysis.LiuYaoInterpreter.analyze', side_effect=AssertionError('No fresh analysis')):
            for request in [
                {"method": "MAIHOA", "consultation_id": maihoa['request_id']},
                {"method": "LIUYAO", "consultation_id": coin['request_id'], "analysis_context": analysis['context'], "analysis_rules_sha256": analysis['rules_sha256']}]:
                response = self.client.post('/api/v1/ai/readings', json=request)
                self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([c['method'] for c in self.fake.contexts], ['MAIHOA_INTERNAL','LIUYAO_NAJIA'])
        context = self.fake.contexts[-1]
        self.assertEqual(json.loads(next(f['text'] for f in context['facts'] if f['id']=='selection')), analysis['selection'])
        self.assertTrue(any(e['kind']=='PRIMARY_TEXT' for e in context['evidence']))
        self.assertTrue(all(e['kind']=='PRODUCT_POLICY' for e in context['evidence'] if e['id'].startswith('engine:')))

    def test_bad_references_fail_without_publishing_or_overwriting_analysis(self):
        saved, request = self.natal()
        self.fake.malformed = True
        response = self.client.post('/api/v1/ai/readings', json=request)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['error']['code'], 'AI_RESPONSE_UNBOUND')
        self.assertIsNone(self.client.post('/api/v1/ai/readings/lookup', json=request).json())
        self.assertEqual(self.client.get('/api/v1/bazi/consultations/'+saved['request_id']).json(), saved)
        self.fake.malformed=False
        self.assertEqual(self.client.post('/api/v1/ai/readings', json=request).status_code, 200)

    def test_parallel_retry_does_not_duplicate_call_or_hold_database_transaction(self):
        _, request = self.natal()
        self.fake.started = Event();self.fake.release = Event()
        req = AIReadingRequest.model_validate(self.client.enrich(request))
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(self.app.state.ai.execute, req)
            self.assertTrue(self.fake.started.wait(3))
            try:
                with self.assertRaises(EngineError) as caught: self.app.state.ai.execute(req)
                self.assertEqual(caught.exception.code, 'AI_BUSY')
                self.assertTrue(self.app.state.ai_budget.lock.acquire(blocking=False))
                self.app.state.ai_budget.lock.release()
            finally:
                self.fake.release.set()
            first.result(timeout=5)
        self.assertEqual(self.fake.calls, 2)

    def test_single_reference_repair_is_bounded_and_usage_is_accumulated(self):
        _,request=self.natal();self.fake.fail_first=True
        result=self.client.post('/api/v1/ai/readings',json=request)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(self.fake.calls,3)
        self.assertEqual(result.json()['generation_passes'],3)
        self.assertEqual(result.json()['usage']['total_tokens'],300)
        self.client.post('/api/v1/ai/readings',json=request).raise_for_status()
        self.assertEqual(self.fake.calls,3)

    def test_missing_or_wrong_context_rejected_before_model_call(self):
        self.assertEqual(self.client.post('/api/v1/ai/readings', json={'method':'BAZI','consultation_id':str(uuid4())}).status_code,422)
        saved, request=self.natal()
        self.assertEqual(self.client.post('/api/v1/ai/readings', json={**request,'api_key':'do-not-accept'}).status_code,422)
        self.assertEqual(self.client.post('/api/v1/ai/readings', json={'method':'LIUYAO','consultation_id':saved['request_id']}).status_code,422)
        self.assertEqual(self.fake.calls,0)

    def test_unconfigured_service_is_explicit_and_status_never_contains_key(self):
        saved, request = self.natal()
        self.assertNotIn(CONFIG.api_key, self.client.get('/api/v1/ai/status').text)
        with TestClient(create_app(self.path, AIConfig(), self.fake), storage=[r for r in self.client.storage if r["kind"] != "AI"]) as c:
            response=c.post('/api/v1/ai/readings',json=request)
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json()['error']['code'],'AI_NOT_CONFIGURED')
        self.assertEqual(self.fake.calls,0)


if __name__ == '__main__':
    unittest.main()
