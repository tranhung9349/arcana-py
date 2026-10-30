"""Internal JSON is valid model input, but must never be accepted as reading prose."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tests.browser_client import TestClient

from randomyst.api import create_app
from randomyst.reading_display import (readable_prose, VerboseReading, JargonReading,
                                      validate_reading_brevity, validate_bazi_language, validate_liuyao_language)
from research_tools.interpretation_prompt import Response
from tests.test_ai_readings import CONFIG, FakeAI
from tests.test_bazi_consultations import payload
from tests.test_maihoa_consultations import payload as maihoa_payload
from tests.test_coin_consultations import payload as coin_payload


class ReadingDisplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = FakeAI()
        self.app = create_app(Path(self.tmp.name) / "app.sqlite3", CONFIG, self.fake)
        self.client = TestClient(self.app)
        self.saved = self.client.post("/api/v1/maihoa/consultations", json=maihoa_payload()).json()
        self.request = {"method": "MAIHOA", "consultation_id": self.saved["request_id"]}

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
        self.assertEqual(self.client.get("/api/v1/maihoa/consultations/" + self.saved["request_id"]).json(), self.saved)

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

    def test_length_budget_checks_each_section_and_total_without_truncating(self):
        context = {"context_id": "length-test", "facts": [{"id": "f1"}], "evidence": [{"id": "e1"}],
                   "limitations": ["Chưa có thời điểm cụ thể."]}
        raw, _ = FakeAI().complete([{"content": json.dumps(context)}])
        reading = Response.model_validate(raw)
        self.assertIs(validate_reading_brevity(reading), reading)
        for field, index, limit in (("summary", None, 50), ("analysis", 0, 70),
                                    ("practical_options", 0, 35), ("limits", 0, 30)):
            value = reading.model_copy(deep=True)
            def set_text(text):
                if field == "limits":
                    value.limits[index] = text
                elif index is None:
                    value.summary.text = text
                else:
                    getattr(value, field)[index].text = text
            set_text(" ".join(["từ"] * limit))
            validate_reading_brevity(value)
            set_text(" ".join(["từ"] * (limit + 1)))
            before = value.model_dump()
            with self.assertRaises(VerboseReading):
                validate_reading_brevity(value)
            self.assertEqual(value.model_dump(), before)
        value = reading.model_copy(deep=True)
        value.analysis.append(value.analysis[0])
        with self.assertRaises(VerboseReading):
            validate_reading_brevity(value)
        value = reading.model_copy(deep=True)
        value.summary.text = "từ " * 50
        for claim in value.analysis:
            claim.text = "từ " * 70
        value.practical_options = [value.practical_options[0].model_copy(deep=True) for _ in range(2)]
        for option in value.practical_options:
            option.text = "từ " * 35
        value.limits = ["từ " * 30, "từ " * 10]
        validate_reading_brevity(value)  # Exactly 300 words.
        value.limits[1] += "từ"
        with self.assertRaises(VerboseReading) as caught:
            validate_reading_brevity(value)
        self.assertIn({"field": "reading", "max_words": 300, "actual_words": 301}, caught.exception.fields)

    def test_verbose_generation_is_rewritten_once_with_length_hints(self):
        original = self.fake.complete
        def repair(messages):
            result, meta = original(messages)
            if self.fake.calls == 1:
                result["summary"]["text"] = "Lời dài " * 30
            else:
                self.assertIn('READING_TOO_LONG', messages[0]['content'])
                self.assertIn('max_words', messages[0]['content'])
                self.assertIn('actual_words', messages[0]['content'])
                self.assertEqual(len(messages),3)
                draft=json.loads(messages[1]['content'])
                self.assertEqual(draft['editorial_draft']['summary']['text'],"Lời dài "*30)
                self.assertEqual(draft['editing_goal'],'SHORTEN_WITHOUT_CHANGING_CONDITIONS_OR_REFERENCES')
                self.assertEqual(json.loads(messages[-1]['content'])['context_id'],result['context_id'])
            return result, meta
        self.fake.complete = repair
        response = self.client.post("/api/v1/ai/readings", json=self.request)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["generation_passes"], 2)
        self.assertEqual(response.json()["usage"]["total_tokens"], 200)
        self.assertNotIn("Lời dài", response.text)

    def test_liuyao_section_headroom_still_enforces_the_short_article_total(self):
        raw=self.client.post('/api/v1/ai/readings',json=self.request).json()['reading']
        reading=Response.model_validate(raw)
        reading.summary.text='từ '*52;reading.analysis[0].text='từ '*81
        with self.assertRaises(VerboseReading):validate_reading_brevity(reading)
        validate_reading_brevity(reading,section_limit_factor=1.5)
        reading.analysis[1].text='từ '*105
        reading.practical_options[0].text='từ '*52
        reading.limits=['từ '*20]
        with self.assertRaises(VerboseReading) as caught:
            validate_reading_brevity(reading,section_limit_factor=1.5)
        self.assertIn('reading',{row['field'] for row in caught.exception.fields})

    def test_bazi_jargon_gets_one_rewrite_and_does_not_change_the_saved_chart(self):
        saved = self.client.post("/api/v1/bazi/consultations", json=payload()).json()
        request = {"method": "BAZI", "consultation_id": saved["request_id"]}
        original = self.fake.complete
        def repair(messages):
            result, meta = original(messages)
            if self.fake.calls == 2:
                result["overview"] = "Nhật chủ có khí thế vượng, cần xét phù ức."
            elif self.fake.calls == 3:
                self.assertIn('LIFE_READING_TOO_MUCH_JARGON', messages[0]['content'])
            return result, meta
        self.fake.complete = repair
        response = self.client.post("/api/v1/ai/readings", json=request)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["generation_passes"], 3)
        self.assertNotIn("khí thế vượng", response.json()["reading"]["overview"]["text"])
        self.assertEqual(self.client.get("/api/v1/bazi/consultations/" + saved["request_id"]).json(), saved)

    def test_bazi_language_allows_brief_definitions_and_ordinary_observation(self):
        raw = self.client.post("/api/v1/ai/readings", json=self.request).json()["reading"]
        reading = Response.model_validate(raw)
        reading.practical_options[0].text = "Bạn có thể quan sát lỗi còn mắc khi tự làm bài."
        reading.analysis[0].text = "Nhật chủ là ký hiệu ngày sinh được lấy làm điểm so sánh."
        reading.analysis[1].text = "Tàng can là các ký hiệu nằm trong phần nhánh của mỗi cột."
        validate_bazi_language(reading)
        reading.analysis[1].text += " Thập Thần gọi tên các quan hệ giữa ký hiệu."
        before = reading.model_dump()
        with self.assertRaises(JargonReading):
            validate_bazi_language(reading)
        self.assertEqual(reading.model_dump(), before)
        reading.analysis[1].text = "Phần còn lại chưa đủ rõ để kết luận."
        reading.summary.text = "Dụng thần cần được xét cùng Nhật chủ."
        with self.assertRaises(JargonReading):
            validate_bazi_language(reading)

    def test_repeated_verbose_output_is_neither_displayed_nor_cached(self):
        original = self.fake.complete
        def verbose(messages):
            result, meta = original(messages)
            result["practical_options"][0]["text"] = "Lời dài " * 20
            return result, meta
        self.fake.complete = verbose
        response = self.client.post("/api/v1/ai/readings", json=self.request)
        self.assertEqual(response.status_code, 502, response.text)
        self.assertEqual(self.fake.calls, 2)
        self.assertNotIn("Lời dài", response.text)
        self.assertIsNone(self.client.post("/api/v1/ai/readings/lookup", json=self.request).json())

    def test_liuyao_jargon_repairs_once_and_repeated_jargon_is_not_cached(self):
        coin = self.client.post('/api/v1/coins/consultations', json=coin_payload()).json()
        analysis = self.client.post('/api/v1/coins/consultations/'+coin['request_id']+'/analysis', json={'topic':'CAREER'}).json()
        request = {'method':'LIUYAO', 'consultation_id':coin['request_id'], 'analysis_context':analysis['context'],
                   'analysis_rules_sha256':analysis['rules_sha256']}
        original = self.fake.complete
        def repair(messages):
            result, meta = original(messages)
            if self.fake.calls == 1:
                result['summary']['text'] = 'Quan quỷ sinh phù nhưng Dụng thần gặp Tuần Không.'
            else:
                self.assertIn('LIUYAO_TOO_MUCH_JARGON', messages[0]['content'])
            return result, meta
        self.fake.complete = repair
        response = self.client.post('/api/v1/ai/readings', json=request)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['generation_passes'], 2)
        self.assertEqual(self.client.get('/api/v1/coins/consultations/'+coin['request_id']).json(), coin)
        self.assertEqual(self.client.get('/api/v1/coins/consultations/'+coin['request_id']+'/analysis').json(), analysis)
        self.app.state.ai._cache.clear()
        self.client.storage[:] = [r for r in self.client.storage if r['kind'] != 'AI']
        for field in ('summary', 'analysis', 'practical_options', 'limits'):
            def jargon(messages):
                result, meta = original(messages)
                value = 'Dụng thần gặp Tuần Không và Nguyệt Phá.'
                if field == 'summary': result[field]['text'] = value
                elif field == 'limits': result[field][0] = value
                else: result[field][0]['text'] = value
                return result, meta
            self.fake.complete = jargon
            before = self.fake.calls
            response = self.client.post('/api/v1/ai/readings', json=request)
            self.assertEqual(response.status_code, 502, response.text)
            self.assertEqual(self.fake.calls-before, 2)
            self.assertIsNone(self.client.post('/api/v1/ai/readings/lookup', json=request).json())

    def test_liuyao_reader_keeps_technical_definitions_and_line_numbers_in_evidence_only(self):
        raw = self.client.post('/api/v1/ai/readings', json=self.request).json()['reading']
        reading = Response.model_validate(raw)
        reading.summary.text = 'Chưa xác định được bạn có tiếp tục công việc trong tháng 12/2026 hay còn làm bao lâu.'
        reading.limits = ['Chưa xác định thời điểm cụ thể.']
        reading.analysis[0].text = 'Dấu hiệu công việc có cả điều kiện nâng đỡ và trở ngại.'
        self.assertIs(validate_liuyao_language(reading), reading)
        for text in ('Dụng thần là dấu hiệu đại diện công việc.', 'Hai hào 2 và 5 đang có khí thế vượng.',
                     'Hai hào động gây cản trở.', 'L2 là dấu hiệu công việc.',
                     'Có hợp trói và biến hào chưa rõ hiệu lực.', 'Động biến còn điều kiện.'):
            reading.analysis[1].text = text
            with self.assertRaises(JargonReading): validate_liuyao_language(reading)
        reading.analysis[1].text = 'Bạn có thể kiểm tra kế hoạch công việc; không suy ra thành tích hay sự tự hào của bạn.'
        validate_liuyao_language(reading)
        reading.summary.text = 'Nhật - Nguyệt đang hỗ trợ.'
        with self.assertRaises(JargonReading): validate_liuyao_language(reading)

    def test_liuyao_repair_receives_all_issues_and_the_rejected_draft_together(self):
        coin=self.client.post('/api/v1/coins/consultations',json=coin_payload()).json()
        analysis=self.client.post('/api/v1/coins/consultations/'+coin['request_id']+'/analysis',json={'topic':'CAREER'}).json()
        request={'method':'LIUYAO','consultation_id':coin['request_id'],'analysis_context':analysis['context'],
                 'analysis_rules_sha256':analysis['rules_sha256']}
        original=self.fake.complete
        def repair(messages):
            result,meta=original(messages)
            if self.fake.calls==1:
                result['summary']['fact_refs']=['invented:reference']
                result['analysis'][0]['text']='Hợp trói và biến hào. '*25
            else:
                for code in ('CONTEXT_OR_REFERENCE_MISMATCH','LIUYAO_TOO_MUCH_JARGON','READING_TOO_LONG'):
                    self.assertIn(code,messages[0]['content'])
                draft=json.loads(messages[1]['content'])['editorial_draft']
                self.assertEqual(draft['summary']['fact_refs'],['invented:reference'])
                self.assertIn('Hợp trói',draft['analysis'][0]['text'])
                self.assertNotIn('editorial_draft',json.loads(messages[-1]['content']))
            return result,meta
        self.fake.complete=repair
        response=self.client.post('/api/v1/ai/readings',json=request)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['generation_passes'],2)
        self.assertEqual(self.fake.calls,2)

    def test_readable_historical_cache_is_not_rejected_or_cut_by_new_length_budget(self):
        first = self.client.post("/api/v1/ai/readings", json=self.request).json()
        legacy = deepcopy(first)
        legacy["reading"]["summary"]["text"] = "Bài luận cũ vẫn đọc được. " * 15
        import time
        self.app.state.ai._cache[first['reading_id']] = (time.monotonic()+900, json.dumps(legacy))
        self.client.storage[:] = [r for r in self.client.storage if r['kind'] != 'AI']
        response = self.client.post("/api/v1/ai/readings/lookup", json=self.request)
        self.assertEqual(response.json(), legacy)
        self.assertEqual(self.fake.calls, 1)

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
