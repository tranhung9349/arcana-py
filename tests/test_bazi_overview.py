"""Exercise the signed natal overview route with a local provider fixture."""
from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from randomyst.ai_client import AIConfig, CompatibleAIClient
from randomyst.api import create_app
from randomyst.bazi_pipeline import ANALYST_MAX_TOKENS, INTERPRETER_MAX_TOKENS, WHOLE_LIFE_INTERPRETER_PROMPT
from tests.bazi_pipeline_fixtures import analysis_for, prose_for


class OverviewTests(unittest.TestCase):
    def setUp(self):
        self.opener = Mock()
        self.config = AIConfig("https://example.test/v1", "other-workflows", "test-token")
        self.app = create_app(ai_config=self.config, ai_client=CompatibleAIClient(self.config, self.opener))
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        request_id = str(uuid4())
        response = self.client.post("/api/v1/bazi/consultations", json={
            "request_id": request_id, "birth": {"civil_datetime": "1990-01-03T18:00:00+07:00", "gender": "male"},
            "display_name": "PROFILE-NAME-FIXTURE", "question": "QUESTION-FIXTURE", "topic": "CAREER", "target_year": 2026})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["model_called"])
        self.opener.open.assert_not_called()
        self.request = {"method": "BAZI", "bazi_scope": "OVERVIEW", "consultation_id": request_id,
                        "consultation": {"kind": "BAZI", "data": response.json(), "signature": response.headers["X-Arcana-Signature"]}}

    def provider_returns(self, request, **kwargs):
        messages = json.loads(request.data)["messages"]
        input_data = json.loads(messages[-1]["content"])
        if input_data["stage"] == "BAZI_STRUCTURAL_ANALYST":
            value = analysis_for(input_data["verified_context"], whole_life=True)
        else:
            value = prose_for(input_data["analysis_result"])
        reply = {"model": "gpt-5.6-terra", "choices": [{"message": {"content": json.dumps(value)}, "finish_reason": "stop"}]}
        body = BytesIO(json.dumps(reply).encode())
        body.headers = {"Content-Type": "application/json"}
        return body

    def test_uses_the_original_whole_life_pipeline_on_terra_even_when_started_from_career(self):
        self.opener.open.side_effect = self.provider_returns
        status = self.client.get("/api/v1/ai/status").json()
        self.assertEqual(status["model"], "other-workflows")
        self.assertEqual(status["bazi_overview"]["model"], "gpt-5.6-terra")
        route = "/api/v1/ai/readings/"
        self.assertIn("event: missing", self.client.post(route + "stream", json=self.request).text)
        response = self.client.post(route + "start", json=self.request)
        self.assertIn("event: result", response.text)
        result = json.loads(response.text.split("event: result\ndata: ")[-1])
        schema = Path(__file__).resolve().parents[1] / "schemas/ai_reading_response.schema.json"
        Draft202012Validator(json.loads(schema.read_text())).validate(result)
        self.assertEqual(result["generation_passes"], 2)
        self.assertEqual(result["model_requested"], "gpt-5.6-terra")
        self.assertEqual(result["pipeline"]["analyst_model"], "gpt-5.6-terra")
        self.assertEqual(result["pipeline"]["interpreter_model"], "gpt-5.6-terra")
        portrait = result["reading"]["whole_life"]
        self.assertEqual([area["area"] for area in portrait["areas"]], ["CAREER", "FINANCES", "RELATIONSHIPS"])
        cycles = self.request["consultation"]["data"]["engine"]["result"]["luck_cycles"]
        self.assertEqual([(p["start_year"], p["end_year"]) for p in portrait["periods"]],
                         [(cycles[a]["start"], cycles[b]["end"]) for a, b in [(0, 1), (2, 4), (5, 6)]])
        self.assertNotIn('"bazi_analysis"', response.text)
        self.assertIn(result["reading_id"], self.client.post(route + "stream", json=self.request).text)
        self.assertEqual(self.opener.open.call_count, 2)
        analyst, writer = [json.loads(call.args[0].data) for call in self.opener.open.call_args_list]
        self.assertEqual(json.loads(analyst["messages"][-1]["content"])["reading_scope"], "WHOLE_LIFE")
        self.assertTrue(writer["messages"][0]["content"].startswith(WHOLE_LIFE_INTERPRETER_PROMPT.read_text()))
        for payload, limit in [(analyst, ANALYST_MAX_TOKENS), (writer, INTERPRETER_MAX_TOKENS)]:
            self.assertEqual(payload["model"], "gpt-5.6-terra")
            self.assertEqual(payload["reasoning_effort"], "low")
            self.assertEqual(payload["max_completion_tokens"], limit)
            self.assertNotIn("temperature", payload)
            self.assertNotIn("max_tokens", payload)
            for private_value in ("1990-01-03", "18:00:00", "gender_used_for_cycles", "PROFILE-NAME-FIXTURE", "QUESTION-FIXTURE"):
                self.assertNotIn(private_value, payload["messages"][-1]["content"])
