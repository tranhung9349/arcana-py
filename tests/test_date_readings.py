"""Selected-date explanations stay bound to saved engine results, not model guesses."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from tests.browser_client import TestClient
from jsonschema import Draft202012Validator

from randomyst.api import create_app
from randomyst.ai_service import AIReadingResult
from randomyst.date_ai_context import date_context
from randomyst.date_consultations import DateConsultation
from research_tools.date_interpretation_prompt import build_date_messages, load_date_pack
from tests.test_ai_readings import CONFIG, FakeAI
from tests.test_date_activity_expansion import request

ROOT = Path(__file__).resolve().parents[1]


class DateReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "dates.sqlite3"
        self.fake = FakeAI()
        self.app = create_app(self.path, CONFIG, self.fake)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def save(self, activity="BUSINESS_OPENING", date="2026-10-13", search=None):
        payload = {"request_id": str(uuid4()), "search": search or request(activity, date)}
        response = self.client.post('/api/v2/auspicious-dates/consultations', json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return payload, response.json()

    def test_explanation_matches_search_and_scope_without_changing_scores(self):
        payload, saved = self.save()
        DateConsultation.model_validate(saved)
        base = self.client.post('/api/v2/auspicious-dates/search', json=payload['search']).json()
        self.assertEqual(saved['result'], base)
        self.assertEqual(base['days'][0]['grade'], 'GOOD')
        self.assertIn('đạt mức Ngày Đẹp', saved['explanation']['summary'])
        self.assertTrue(any(w['start_at'] == saved['explanation']['focus_start_at'] and w['grade'] == 'GOOD' for w in base['days'][0]['windows']))
        self.assertEqual(self.fake.calls, 0)
        self.assertEqual(self.client.get('/api/v1/history').json(), {'draws': []})

    def test_snapshot_retry_read_and_ai_do_not_recompute_or_send_birth_data(self):
        payload, saved = self.save()
        ai_request = {'method': 'DATE', 'consultation_id': saved['request_id']}
        self.assertIsNone(self.client.post('/api/v1/ai/readings/lookup', json=ai_request).json())
        with patch.object(self.app.state.date_engine, 'search', side_effect=AssertionError('No fresh date computation')), \
             patch('randomyst.date_engine.analyze', side_effect=AssertionError('No natal recalculation')):
            self.assertEqual(self.client.post('/api/v2/auspicious-dates/consultations', json=payload).json(), saved)
            result = self.client.post('/api/v1/ai/readings', json=ai_request)
            self.assertEqual(result.status_code, 200, result.text)
            AIReadingResult.model_validate(result.json())
            self.assertEqual(self.client.post('/api/v1/ai/readings', json=ai_request).json(), result.json())
            self.assertEqual(self.client.get('/api/v2/auspicious-dates/consultations/'+saved['request_id']).json(), saved)
        self.assertEqual(self.fake.calls, 1)
        context_text = json.dumps(self.fake.contexts[-1], ensure_ascii=False)
        for forbidden in ('1994-10-08', 'civil_datetime', 'natal_branches', 'clashing_natal_branch_indices', 'person_0'):
            self.assertNotIn(forbidden, context_text)
        self.assertEqual(self.fake.contexts[-1]['method'], 'DATE_SELECTION')
        with TestClient(create_app(self.path, CONFIG, FakeAI()), storage=self.client.storage) as restarted:
            self.assertEqual(restarted.post('/api/v1/ai/readings/lookup', json=ai_request).json(), result.json())

    def test_day_only_two_profiles_are_separate_and_no_hours_are_recommended(self):
        _, saved = self.save('BETROTHAL_NACAI', '2026-10-02')
        day = saved['result']['days'][0]
        self.assertEqual(day['recommended_windows'], [])
        self.assertTrue(any('chưa chọn giờ đẹp' in c for c in saved['explanation']['cautions']))
        self.assertTrue(any('không lấy trung bình' in r for r in saved['explanation']['reasons']))
        ctx = date_context(saved)
        personal = json.loads(next(f.text for f in ctx.facts if f.id == 'date:personal'))
        self.assertEqual(len(personal), 2)
        self.assertEqual({p['role'] for p in personal}, set(saved['result']['activity_spec']['subject_roles']))
        focus = json.loads(next(f.text for f in ctx.facts if f.id == 'date:focus'))
        self.assertNotIn('hour_activity_status', focus)
        self.assertIn('DAY_ONLY', ctx.signals)
        self.assertNotIn('giờ đẹp được chọn', build_date_messages(ctx)['messages'][0]['content'])

    def test_blocked_and_unresolved_dates_do_not_become_recommendations(self):
        _, saved = self.save(date='2026-10-01')
        self.assertEqual(saved['result']['days'][0]['grade'], 'BAD')
        self.assertIn('chưa có', saved['explanation']['summary'])
        self.assertTrue(any('Không cộng bù' in c for c in saved['explanation']['cautions']))
        q = request('BUSINESS_OPENING', '2026-10-13')
        q['subjects'][0]['birth'] = {'civil_datetime': '2026-10-08T13:29:17+07:00', 'clock_uncertainty_seconds': 2}
        _, unresolved = self.save(search=q)
        self.assertIsNone(unresolved['result']['days'][0]['grade'])
        self.assertIn('chưa đủ dữ liệu', unresolved['explanation']['summary'])
        self.assertTrue(any('Điểm thô' in c for c in unresolved['explanation']['cautions']))
        self.assertIn('UNRESOLVED', date_context(unresolved).signals)

    def test_invalid_multi_day_filtered_duplicate_and_client_facts_are_rejected(self):
        payload, saved = self.save()
        bad = deepcopy(payload)
        bad['request_id']=str(uuid4()); bad['search']['date_range']['end'] = '2026-10-14'
        self.assertEqual(self.client.post('/api/v2/auspicious-dates/consultations', json=bad).status_code, 422)
        bad = deepcopy(payload); bad['request_id']=str(uuid4()); bad['search']['allowed_weekdays'] = [0]
        self.assertEqual(self.client.post('/api/v2/auspicious-dates/consultations', json=bad).status_code, 422)
        bad = deepcopy(payload); bad['search']['subjects'][0]['birth']['override_dung_than'] = 'Kim'
        self.assertEqual(self.client.post('/api/v2/auspicious-dates/consultations', json=bad).status_code, 409)
        self.assertEqual(self.client.post('/api/v1/ai/readings', json={'method':'DATE','consultation_id':str(uuid4())}).status_code, 422)
        for extra in ({'facts': []}, {'analysis_context': {'topic': 'DOCUMENT'}}, {'bazi_reading_id': str(uuid4())}):
            self.assertEqual(self.client.post('/api/v1/ai/readings', json={'method':'DATE','consultation_id':saved['request_id'], **extra}).status_code, 422)
        self.assertEqual(self.fake.calls, 0)

    def test_date_pack_gates_state_mode_and_keeps_untrusted_prose_out_of_system(self):
        manifest, cases = load_date_pack()
        self.assertEqual(len(cases), manifest['case_count'])
        for case in cases:
            from randomyst.date_ai_context import DateReadingContext
            ctx = DateReadingContext.model_validate(case['context'])
            before = ctx.model_dump_json()
            messages = build_date_messages(ctx)
            self.assertEqual(ctx.model_dump_json(), before)
            for case_id in messages['case_ids']:
                example = next(c for c in cases if c['id'] == case_id)
                for group in ({'DAY_ONLY','DAY_AND_HOUR'}, {'GOOD','NORMAL','BAD','UNRESOLVED'}):
                    self.assertEqual(set(example['context']['signals']) & group, set(ctx.signals) & group)
            poisoned = ctx.model_copy(update={'question': 'TRUSTED_OVERRIDE_XYZ'})
            result = build_date_messages(poisoned)
            self.assertNotIn('TRUSTED_OVERRIDE_XYZ', result['messages'][0]['content'])
            self.assertIn('TRUSTED_OVERRIDE_XYZ', result['messages'][-1]['content'])

    def test_public_date_schema_accepts_actual_snapshot(self):
        _, saved = self.save()
        schema = json.loads((ROOT/'schemas/date_consultation_response.schema.json').read_text())
        Draft202012Validator(schema).validate(saved)


if __name__ == '__main__':
    unittest.main()
