"""Internal JSON is valid model input, but must never be accepted as reading prose."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tests.browser_client import TestClient

from randomyst.api import create_app
from randomyst.reading_display import readable_prose
from tests.test_ai_readings import CONFIG, FakeAI
from tests.test_bazi_consultations import payload


class ReadingDisplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = FakeAI()
        self.app = create_app(Path(self.tmp.name) / "app.sqlite3", CONFIG, self.fake)
        self.client = TestClient(self.app)
        self.saved = self.client.post("/api/v1/bazi/consultations", json=payload()).json()
        self.request = {"method": "BAZI", "consultation_id": self.saved["request_id"]}

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def test_plain_language_and_primary_text_are_allowed_but_data_notation_is_rejected(self):
        for text in ("Thể sinh Dụng: cần thêm nguồn lực.", "元亨利貞。", "Ngày 13/10 · 08:00–10:00 · 75/100"):
            self.assertTrue(readable_prose(text))
        for text in ('{"strength":"STRONG"}', '["Mộc","Hỏa"]', "{'type': 'object'}",
                     'Kết quả: {"required":[]}', '```json\n{}\n```', 'schema_version: v1',
                     'facts:distribution', 'reading:anchors', '[object Object]', '<html>Error</html>',
                     'Các hành: ["Hỏa","Kim"].', 'Số: [[1,2]].', 'type: object\nproperties:\n  title: string'):
            self.assertFalse(readable_prose(text), text)

    def test_machine_notation_in_each_prose_section_is_neither_returned_nor_cached(self):
        original = self.fake.complete
        for part in ("summary", "analysis", "practical_options", "limits"):
            def poisoned(messages):
                result, meta = original(messages)
                if part == "limits":
                    result[part][0] = 'schema_version: backend-v1'
                elif part == "summary":
                    result[part]["text"] = '{"properties":{"secret":{"type":"string"}}}'
                else:
                    result[part][0]["text"] = 'Dữ kiện: {"internal_field": 42}'
                return result, meta
            self.fake.complete = poisoned
            before = self.fake.calls
            response = self.client.post("/api/v1/ai/readings", json=self.request)
            self.assertEqual(response.status_code, 502, response.text)
            self.assertEqual(response.json()["error"]["code"], "AI_RESPONSE_UNBOUND")
            self.assertNotIn("internal_field", response.text)
            self.assertNotIn("properties", response.text)
            self.assertEqual(self.fake.calls - before, 2)
            self.assertIsNone(self.client.post("/api/v1/ai/readings/lookup", json=self.request).json())
        self.assertEqual(self.client.get("/api/v1/bazi/consultations/" + self.saved["request_id"]).json(), self.saved)

    def test_single_repair_accepts_prose_after_a_machine_notation_failure(self):
        original = self.fake.complete
        def repair(messages):
            result, meta = original(messages)
            if self.fake.calls == 1:
                result["analysis"][0]["text"] = 'line:L2 có activity: DARK_ACTIVE'
            else:
                self.assertIn('PROSE_CONTAINS_INTERNAL_NOTATION', messages[0]['content'])
                self.assertIn('không chèn JSON', messages[0]['content'])
            return result, meta
        self.fake.complete = repair
        response = self.client.post("/api/v1/ai/readings", json=self.request)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["generation_passes"], 2)
        self.assertEqual(self.fake.calls, 2)
        self.assertTrue(readable_prose(response.json()["reading"]["analysis"][0]["text"]))

    def test_legacy_unreadable_cache_is_hidden_and_an_explicit_retry_can_replace_it(self):
        first = self.client.post("/api/v1/ai/readings", json=self.request).json()
        poisoned = deepcopy(first)
        poisoned["reading"]["summary"]["text"] = '{"schema_version":"internal-v1"}'
        import time
        self.app.state.ai._cache[first['reading_id']] = (time.monotonic()+900, json.dumps(poisoned))
        self.client.storage[:] = [r for r in self.client.storage if r['kind'] != 'AI']
        self.assertIsNone(self.client.post("/api/v1/ai/readings/lookup", json=self.request).json())
        self.assertEqual(self.fake.calls, 1)
        retry = self.client.post("/api/v1/ai/readings", json=self.request)
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual(self.fake.calls, 2)
        self.assertEqual(retry.json()["reading_id"], first["reading_id"])
        self.assertEqual(self.client.post("/api/v1/ai/readings/lookup", json=self.request).json(), retry.json())
