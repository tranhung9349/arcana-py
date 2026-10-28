from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import unicodedata
from unittest.mock import patch
from uuid import uuid4

from tests.browser_client import TestClient

from randomyst.api import create_app
from randomyst.coins_service import CoinService
from randomyst.engine import EngineError
from randomyst.interpretation import ExplanationRepository
from randomyst.liuyao_analysis import LiuYaoInterpreter
from randomyst.liuyao_intent import normalize
from randomyst.liuyao_models import AnalysisContext, QuestionIntent

ROOT = Path(__file__).resolve().parents[1]


class QuestionIntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = LiuYaoInterpreter(CoinService(ExplanationRepository()).najia)
        cls.recognizer = cls.engine.intent
        cls.session = json.loads((ROOT / 'examples/coin_consultation_response.json').read_text())

    def recognize(self, question, topic='GENERAL'):
        result = self.recognizer.recognize(question, topic)
        QuestionIntent.model_validate(result)
        return result

    def test_all_topics_vietnamese_accents_case_spacing_and_unicode(self):
        fixtures = [('Tôi hỏi tổng quan bản thân','GENERAL'), ('Tôi hỏi tiền bạc','WEALTH'),
                    ('Tôi muốn ứng tuyển vị trí mới','CAREER'), ('Hợp đồng lao động có được ký không?','DOCUMENT'),
                    ('Mẹ tôi đang thế nào?','PARENTS'), ('Con tôi có ổn không?','CHILDREN'),
                    ('Anh trai tôi đang thế nào?','SIBLINGS'), ('Tôi hỏi tình cảm với người ấy','PARTNERSHIP')]
        for question, topic in fixtures:
            for text in [question, question.upper(), normalize(question), unicodedata.normalize('NFD', question), question.replace(' ','  ')]:
                with self.subTest(text=text, topic=topic):
                    result = self.recognize(text, topic)
                    self.assertEqual(result['status'], 'MATCH')
                    self.assertEqual(result['suggested_topic'], topic)
                    self.assertFalse(result['needs_review'])

    def test_no_substring_or_supplied_accent_false_matches(self):
        for text in ['Tôi mệt mỏi nên muốn đi bộ', 'Trời hôm nay rất đẹp', 'Một bộ phim mới ra rạp', 'Áo màu tím rất đẹp']:
            self.assertEqual(self.recognize(text)['status'], 'UNRECOGNIZED', text)
        result = self.recognize('Tôi ưu tiên công việc, không hỏi tiền bạc', 'CAREER')
        self.assertEqual(result['status'], 'MATCH')
        self.assertEqual([c['topic'] for c in result['candidates']], ['CAREER'])

    def test_explicit_negations_and_question_final_khong(self):
        for text in ['Tôi không hỏi về tiền mà hỏi công việc', 'Toi khong hoi ve tien ma hoi cong viec',
                     'Tôi bỏ qua tiền, chỉ hỏi công việc', 'Đừng xét tiền bạc; tôi hỏi công việc']:
            result = self.recognize(text, 'CAREER')
            self.assertEqual(result['status'], 'MATCH', text)
            self.assertTrue(any(m['topic'] == 'WEALTH' and m['disposition'] == 'NEGATED' for m in result['matches']))
        self.assertEqual(self.recognize('Tôi có thu hồi khoản nợ được không?', 'WEALTH')['status'], 'MATCH')

    def test_conflicting_topic_is_a_suggestion_without_an_implicit_override(self):
        result = self.recognize('Tôi hỏi về tiền bạc trong tháng tới', 'CAREER')
        self.assertEqual(result['status'], 'CONFLICT')
        self.assertEqual(result['selected_topic'], 'CAREER')
        self.assertEqual(result['suggested_topic'], 'WEALTH')
        self.assertTrue(result['needs_review'])

    def test_multiple_questions_are_not_resolved_by_counting_keywords(self):
        result = self.recognize('Công việc và tiền bạc thu nhập lợi nhuận sắp tới thế nào?', 'CAREER')
        self.assertEqual(result['status'], 'MULTIPLE')
        self.assertIsNone(result['suggested_topic'])
        self.assertEqual({c['topic'] for c in result['candidates']}, {'WEALTH','CAREER'})
        self.assertTrue(result['needs_review'])

    def test_actor_context_and_family_questions_are_distinct(self):
        result = self.recognize('Tôi có thể vay tiền của mẹ không?', 'WEALTH')
        self.assertEqual(result['status'], 'MATCH')
        self.assertTrue(any(m['topic'] == 'PARENTS' and m['disposition'] == 'CONTEXT' for m in result['matches']))
        for text in ['Má tôi có ổn không?', 'Ma toi co on khong?', 'Mẹ tôi có ổn không?']:
            self.assertEqual(self.recognize(text, 'PARENTS')['status'], 'MATCH')

    def test_specific_subintent_terms_and_duplicate_mentions(self):
        result = self.recognize('Tôi đòi nợ, khoản nợ này có thu hồi nợ được không?', 'WEALTH')
        candidate = result['candidates'][0]
        self.assertEqual(candidate['evidence_level'], 'SPECIFIC_PHRASE')
        self.assertEqual(candidate['intent_labels'], ['Khoản nợ · thu hồi hoặc thanh toán'])
        result = self.recognize('Tôi hỏi công việc, công việc, công việc', 'CAREER')
        self.assertEqual(len(result['matches']), 1)
        session = deepcopy(self.session); session['question'] = 'Tôi có thu hồi khoản nợ được không?'
        analysis = self.engine.analyze(session, AnalysisContext(topic='WEALTH', intent_mode='COMBINED'))
        self.assertTrue(any('chứng từ' in item for item in analysis['practical_questions']))

    def test_combined_analysis_requires_review_and_respects_explicit_priority(self):
        session = deepcopy(self.session); session['question'] = 'Tôi hỏi về tiền bạc trong tháng tới'
        before = deepcopy(session)
        with self.assertRaises(EngineError) as error:
            self.engine.analyze(session, AnalysisContext(topic='CAREER', intent_mode='COMBINED'))
        self.assertEqual(error.exception.code, 'INTENT_REVIEW_REQUIRED')
        result = self.engine.analyze(session, AnalysisContext(topic='CAREER', intent_mode='COMBINED', intent_acknowledged=True))
        self.assertEqual(result['selection']['target'], 'Quan quỷ')
        self.assertEqual(result['intent']['suggested_topic'], 'WEALTH')
        wealth = self.engine.analyze(session, AnalysisContext(topic='WEALTH', intent_mode='COMBINED'))
        self.assertEqual(wealth['selection']['target'], 'Thê tài')
        self.assertTrue(any('Ý được nhận diện' in paragraph for paragraph in wealth['narrative']))
        override = self.engine.analyze(session, AnalysisContext(topic='WEALTH', intent_mode='COMBINED', use_relative='Phụ mẫu'))
        self.assertEqual(override['selection']['target'], 'Phụ mẫu')
        self.assertEqual(session, before)

    def test_legacy_mode_keeps_existing_semantics_and_unknown_intent_can_use_topic(self):
        session = deepcopy(self.session); session['question'] = 'Tôi hỏi về tiền bạc'
        legacy = self.engine.analyze(session, AnalysisContext())
        self.assertEqual(legacy['selection']['target'], 'WORLD')
        self.assertIsNone(legacy['intent'])
        session['question'] = 'Liệu việc đang dự tính có ổn không?'
        result = self.engine.analyze(session, AnalysisContext(topic='CAREER', intent_mode='COMBINED'))
        self.assertEqual(result['intent']['status'], 'UNRECOGNIZED')
        self.assertEqual(result['selection']['target'], 'Quan quỷ')


class QuestionIntentApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.path = str(Path(self.directory.name) / 'test.sqlite3')
        self.app = create_app(self.path); self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close(); self.directory.cleanup()

    def test_preview_is_read_only_and_input_is_validated(self):
        route = '/api/v1/coins/question-intent'
        result = self.client.post(route, json={'question':'Tôi có đòi được khoản nợ không?','topic':'WEALTH'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['status'], 'MATCH')
        self.assertEqual(self.client.get('/api/v1/coins/history').json()['consultations'], [])
        for bad in [{'question':'    '}, {'question':'a'*2001}, {'question':True}, {'question':'Tôi hỏi tiền','topic':'BAD'}, {'question':'Tôi hỏi tiền','extra':1}]:
            self.assertEqual(self.client.post(route, json=bad).status_code, 422)
        self.assertFalse(any(r['kind']=='LIUYAO' for r in self.client.storage))

    def test_combined_snapshot_replay_review_rejection_and_no_new_coins(self):
        request = json.loads((ROOT / 'examples/coin_consultation_request.json').read_text())
        request['request_id'] = str(uuid4()); request['question'] = 'Tôi hỏi về tiền bạc trong tháng tới'
        session = self.client.post('/api/v1/coins/consultations', json=request).json()
        route = '/api/v1/coins/consultations/' + request['request_id'] + '/analysis'
        context = {'topic':'CAREER','intent_mode':'COMBINED'}
        bad = self.client.post(route, json=context)
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(bad.json()['error']['code'], 'INTENT_REVIEW_REQUIRED')
        self.assertIsNone(self.client.get(route).json())
        context['intent_acknowledged'] = True
        with patch('randomyst.coins_service.secrets.randbits', side_effect=AssertionError('must not reroll')):
            result = self.client.post(route, json=context)
            self.assertEqual(result.status_code, 200, result.text)
        with patch.object(self.app.state.liuyao, 'analyze', side_effect=AssertionError('cached')):
            self.assertEqual(result.json(), self.client.post(route, json=context).json())
        self.assertEqual(result.json(), self.client.get(route).json())
        reopened = TestClient(create_app(self.path), storage=self.client.storage)
        self.assertEqual(result.json(), reopened.get(route).json()); reopened.close()
        self.assertEqual(session, self.client.get('/api/v1/coins/consultations/' + request['request_id']).json())
        for bad in [{'intent_mode':'AUTO'}, {'intent_acknowledged':'yes'}]:
            self.assertEqual(self.client.post(route, json=bad).status_code, 422)

    def test_frontend_scripts_and_preflight_are_integrated(self):
        html = self.client.get('/').text
        self.assertLess(html.index('/static/coin_intent.js'), html.index('/static/liuyao.js'))
        self.assertIn('id="coins-intent"', html)
        self.assertEqual(self.client.get('/static/coin_intent.js').status_code, 200)


if __name__ == '__main__': unittest.main()
