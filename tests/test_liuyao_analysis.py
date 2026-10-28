from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from tests.browser_client import TestClient
from pydantic import ValidationError

from randomyst.api import create_app
from randomyst.coins_models import CoinRequest
from randomyst.coins_service import CoinService, cast_bits
from randomyst.engine import EngineError
from randomyst.interpretation import ExplanationRepository
from randomyst.liuyao import BRANCHES, BRANCH_ELEMENTS
from randomyst.liuyao_analysis import LiuYaoInterpreter, element_relation
from randomyst.liuyao_models import AnalysisContext, LiuYaoAnalysis


def payload(totals=(7, 8, 9, 8, 7, 6)):
    return {'request_id': str(uuid4()), 'question': 'Việc hợp tác sắp tới cần cân nhắc điều gì?', 'source': 'MANUAL',
            'casting': {'mode': 'CUSTOM', 'custom_timestamp': '2026-10-26T09:00:00+07:00'},
            'throws_bottom_to_top': [['BACK']*(v-6) + ['INSCRIPTION']*(9-v) for v in totals]}


class LiuYaoCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coins = CoinService(ExplanationRepository())
        cls.engine = LiuYaoInterpreter(cls.coins.najia)

    def session(self, number=63, moving=(3, 6), month=None, day=None, stem=0):
        bits = self.coins.explanations.by_id[number]['array']
        data = self.coins.consult(CoinRequest.model_validate(payload([9 if bit and i in moving else 6 if not bit and i in moving else 7 if bit else 8 for i, bit in enumerate(bits, 1)])))
        if month is not None:
            data['calendar']['zhis'][1] = month
        if day is not None:
            data['calendar']['zhis'][2] = day; data['calendar']['gans'][2] = stem
        changed = [bit ^ (i in moving) for i, bit in enumerate(bits, 1)]
        data['najia'] = self.coins.najia.chart(bits, changed, list(moving), data['calendar'])
        return data

    def test_element_direction_and_seasonal_states(self):
        self.assertEqual(element_relation('Thủy', 'Mộc'), 'GENERATES')
        self.assertEqual(element_relation('Kim', 'Mộc'), 'CONTROLS')
        self.assertEqual(element_relation('Hỏa', 'Mộc'), 'DRAINS')
        self.assertEqual(element_relation('Thổ', 'Mộc'), 'CONSUMES')
        self.assertEqual(element_relation('Mộc', 'Mộc'), 'SAME')
        row = {'position': 1, 'branch': 'Dần', 'element': 'Mộc', 'relative': 'Thê tài', 'moving': False}
        for month, expected in [(2,'Vượng'), (0,'Tướng'), (5,'Hưu'), (4,'Tù'), (8,'Tử')]:
            result = self.engine.line_state(row, {'zhis':[0,month,4]}, [])
            self.assertEqual(result['seasonal_state'], expected)

    def test_same_coins_different_topic_does_not_mutate_snapshot(self):
        session = self.session(); before = deepcopy(session)
        wealth = self.engine.analyze(session, AnalysisContext(topic='WEALTH'))
        career = self.engine.analyze(session, AnalysisContext(topic='CAREER'))
        self.assertEqual(wealth['selection']['target'], 'Thê tài')
        self.assertEqual(career['selection']['target'], 'Quan quỷ')
        self.assertNotEqual(wealth['selection']['selected_key'], career['selection']['selected_key'])
        self.assertEqual(session, before)
        self.assertEqual(wealth['snapshot_sha256'], career['snapshot_sha256'])

    def test_classical_heng_to_daguo_advance_and_dark_activity(self):
        # Tăng San, Tiến/Thoái: Thân month, Quý Mão day, Hằng -> Đại Quá.
        session = self.session(32, (5,), month=8, day=3, stem=9)
        result = self.engine.analyze(session, AnalysisContext(topic='CAREER'))
        self.assertEqual(session['changed']['chart']['hexagram_id'], 28)
        self.assertEqual(result['selection']['selected_key'], 'L3')
        self.assertEqual(result['selection']['status'], 'PROVISIONAL')
        self.assertEqual(result['lines'][2]['branch'], 'Dậu')
        self.assertEqual(result['lines'][2]['activity'], 'DARK_ACTIVE')
        self.assertEqual(result['lines'][4]['branch'], 'Thân')
        self.assertIn('ADVANCE', result['lines'][4]['transformation'])
        self.assertEqual(session['moving_lines'], [5])
        self.assertEqual(session['original']['chart']['lines_bottom_to_top'][2], session['changed']['chart']['lines_bottom_to_top'][2])

    def test_dark_motion_and_weak_day_clash_are_distinct(self):
        row = {'position':1,'branch':'Dậu','element':'Kim','relative':'Huynh đệ','moving':False}
        strong = self.engine.line_state(row, {'zhis':[0,8,3]}, [])
        weak = self.engine.line_state(row, {'zhis':[0,6,3]}, [])
        self.assertEqual(strong['activity'], 'DARK_ACTIVE')
        self.assertEqual(weak['activity'], 'DAY_CLASH_WEAK')
        self.assertEqual(self.engine.line_state(row, {'zhis':[0,8,3]}, [], hidden=True)['activity'], 'STATIC')

    def test_hidden_wealth_in_gou_and_flying_support(self):
        # Cấu has no visible wealth; Càn's Dần Mộc lies under Hợi Thủy at line 2.
        result = self.engine.analyze(self.session(44, (), month=0, day=4), AnalysisContext(topic='WEALTH'))
        self.assertTrue(result['selection']['hidden'])
        self.assertEqual(result['selection']['selected_key'], 'H2')
        hidden = next(r for r in result['lines'] if r['key'] == 'H2')
        self.assertEqual((hidden['branch'], hidden['element']), ('Dần', 'Mộc'))
        fly = next(f for f in result['findings'] if f['rule'] == 'FLY_HIDDEN')
        self.assertIn('sinh hào', fly['explanation'])
        self.assertNotEqual(result['tendency'], 'SUPPORT_WITH_CONDITIONS')
        self.assertTrue(any(t['kind'] == 'REVEAL_HIDDEN' for t in result['timing_conditions']))

    def test_void_visible_use_is_not_replaced_by_hidden_and_calendar_representation_is_explicit(self):
        # Giáp Tý day: Tuất/Hợi void; Càn parents still use visible Tuất/Thìn.
        result = self.engine.analyze(self.session(1, (), month=0, day=0), AnalysisContext(topic='DOCUMENT', focus_line=6))
        self.assertFalse(result['selection']['hidden'])
        self.assertEqual(result['selection']['selected_key'], 'L6')
        self.assertIn('VOID', result['lines'][5]['flags'])
        self.assertTrue(any(f['rule'] == 'VOID' for f in result['findings']))
        result = self.engine.analyze(self.session(44, (), month=2, day=4), AnalysisContext(topic='WEALTH'))
        self.assertIn('Nguyệt Dần · Thê tài', result['selection']['calendar_representatives'])

    def test_multiple_candidates_are_ambiguous_without_an_implicit_winner(self):
        result = self.engine.analyze(self.session(1, (), month=11, day=6), AnalysisContext(topic='DOCUMENT'))
        self.assertEqual(result['selection']['candidate_keys'], ['L3', 'L6'])
        # Parents line 6 holds Thế, so explicit provisional priority is applied.
        self.assertEqual(result['selection']['status'], 'PROVISIONAL')
        # Khôn has two brothers, neither Thế, neither moving nor directly at Nhật/Nguyệt.
        result = self.engine.analyze(self.session(2, (), month=11, day=6), AnalysisContext(topic='SIBLINGS'))
        self.assertEqual(result['selection']['status'], 'AMBIGUOUS')
        self.assertIsNone(result['selection']['selected_key'])
        self.assertEqual(result['tendency'], 'UNRESOLVED')
        result = self.engine.analyze(self.session(2, (), month=11, day=6), AnalysisContext(topic='SIBLINGS', focus_line=4))
        self.assertEqual(result['selection']['selected_key'], 'L4')
        self.assertEqual(result['selection']['status'], 'SELECTED')
        with self.assertRaises(EngineError): self.engine.analyze(self.session(2), AnalysisContext(topic='SIBLINGS', focus_line=2))

    def test_return_generation_control_advance_retreat_and_changed_conditions(self):
        row = {'position':1,'branch':'Dậu','element':'Kim','relative':'Huynh đệ','moving':True,
               'changed_branch':'Tỵ','changed_element':'Hỏa'}
        result = self.engine.line_state(row, {'zhis':[0,11,2]}, ['Tỵ','Ngọ'])
        self.assertIn('RETURN_CONTROLS', result['transformation'])
        self.assertIn('CHANGED_VOID', result['transformation'])
        self.assertIn('CHANGED_MONTH_CLASH', result['transformation'])
        row.update(changed_branch='Thìn', changed_element='Thổ')
        self.assertIn('RETURN_GENERATES', self.engine.line_state(row, {'zhis':[0,11,2]}, [])['transformation'])
        for a, b in self.engine.config['advances']:
            row.update(branch=BRANCHES[a], element=BRANCH_ELEMENTS[a], changed_branch=BRANCHES[b], changed_element=BRANCH_ELEMENTS[b])
            self.assertIn('ADVANCE', self.engine.line_state(row, {'zhis':[0,11,2]}, [])['transformation'])
            row.update(branch=BRANCHES[b], element=BRANCH_ELEMENTS[b], changed_branch=BRANCHES[a], changed_element=BRANCH_ELEMENTS[a])
            self.assertIn('RETREAT', self.engine.line_state(row, {'zhis':[0,11,2]}, [])['transformation'])

    def test_all_64_hexagrams_all_topics_and_all_4096_motion_patterns(self):
        topics = list(self.engine.config['topics'])
        for number in range(1, 65):
            data = self.session(number, ())
            for topic in topics:
                result = self.engine.analyze(data, AnalysisContext(topic=topic))
                LiuYaoAnalysis.model_validate(result)
                self.assertTrue(result['selection']['candidate_keys'])
                self.assertEqual(len([r for r in result['lines'] if r['visibility'] == 'VISIBLE']), 6)
        # Use one text snapshot with freshly generated charts; text doesn't drive this engine.
        data = self.session()
        for totals in product((6,7,8,9), repeat=6):
            bits, moving, changed = cast_bits(totals)
            data['najia'] = self.coins.najia.chart(bits, changed, moving, data['calendar'])
            result = self.engine.analyze(data, AnalysisContext())
            self.assertEqual([r['position'] for r in result['lines'] if r['activity'] == 'MOVING'], moving)
            self.assertEqual(result['selection']['selected_key'], 'L' + str(data['najia']['world_line']))

    def test_sources_and_trace_reject_invalid_selection(self):
        result = self.engine.analyze(self.session(), AnalysisContext())
        self.assertTrue(all(f['evidence'] and f['source_ids'] for f in result['findings']))
        result['selection']['selected_key'] = 'H6'
        with self.assertRaises(ValidationError): LiuYaoAnalysis.model_validate(result)

    def test_conditional_adversary_and_generation_chain_are_not_cancelled_or_counted_as_certain(self):
        result = self.engine.analyze(self.session(), AnalysisContext(topic='WEALTH'))
        interaction = next(f for f in result['findings'] if f['rule'] == 'LINE_INTERACTION' and f['evidence'][0] == 'L3')
        self.assertIn('RETURN_CONTROLS', interaction['evidence'])
        self.assertEqual(interaction['effect'], 'CONDITION')
        result = self.engine.analyze(self.session(63, (2,4)), AnalysisContext())
        self.assertTrue(any(f['rule'] == 'GENERATION_CHAIN' for f in result['findings']))
        self.assertNotEqual(result['tendency'], 'SUPPORT_WITH_CONDITIONS')
        # With moving lines present, this profile doesn't invent actions from other static lines.
        for finding in result['findings']:
            if finding['rule'] == 'LINE_INTERACTION':
                source = next(row for row in result['lines'] if row['key'] == finding['evidence'][0])
                self.assertIn(source['activity'], ('MOVING', 'DARK_ACTIVE'))

    def test_supported_career_use_does_not_hide_void_world_capacity(self):
        result = self.engine.analyze(self.session(48, (6,)), AnalysisContext(topic='CAREER'))
        self.assertEqual(result['selection']['selected_key'], 'L3')
        self.assertEqual(result['lines'][2]['calendar_state'], 'SUPPORTED')
        self.assertIn('VOID', result['lines'][4]['flags'])
        self.assertTrue(any(f['rule'] == 'WORLD_CAPACITY' for f in result['findings']))
        self.assertEqual(result['tendency'], 'MIXED')


class LiuYaoApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.path = str(Path(self.directory.name) / 'test.sqlite3')
        self.app = create_app(self.path); self.client = TestClient(self.app)
        self.request = payload(); self.session = self.client.post('/api/v1/coins/consultations', json=self.request).json()
        self.base = '/api/v1/coins/consultations/' + self.request['request_id'] + '/analysis'

    def tearDown(self):
        self.client.close(); self.directory.cleanup()

    def test_old_sessions_reanalysis_persistence_and_no_reroll(self):
        self.assertIsNone(self.client.get(self.base).json())
        with patch('randomyst.coins_service.secrets.randbits', side_effect=AssertionError('must not reroll')):
            first = self.client.post(self.base, json={'topic':'WEALTH'})
            self.assertEqual(first.status_code, 200, first.text)
            second = self.client.post(self.base, json={'topic':'CAREER'})
            self.assertEqual(second.status_code, 200, second.text)
        self.assertNotEqual(first.json()['selection']['target'], second.json()['selection']['target'])
        self.assertEqual(second.json(), self.client.get(self.base).json())
        with patch.object(self.app.state.liuyao, 'analyze', side_effect=AssertionError('cached')):
            self.assertEqual(first.json(), self.client.post(self.base, json={'topic':'WEALTH'}).json())
        reopened = TestClient(create_app(self.path), storage=self.client.storage)
        self.assertEqual(first.json(), reopened.get(self.base).json()); reopened.close()
        self.assertEqual(self.session, self.client.get('/api/v1/coins/consultations/' + self.request['request_id']).json())
        self.assertEqual(len(self.client.get('/api/v1/coins/history').json()['consultations']), 1)

    def test_rule_hash_invalidates_cache_but_old_snapshot_stays_readable(self):
        first = self.client.post(self.base, json={}).json()
        self.app.state.liuyao.rules_sha256 = 'f'*64
        self.assertEqual(self.client.get(self.base).json(), first)
        second = self.client.post(self.base, json={}).json()
        self.assertNotEqual(first['rules_sha256'], second['rules_sha256'])
        self.assertEqual(sum(r['kind']=='LIUYAO' for r in self.client.storage), 2)

    def test_concurrent_analysis_computes_once_and_input_validation(self):
        original = self.app.state.liuyao.analyze
        with patch.object(self.app.state.liuyao, 'analyze', wraps=original) as builder:
            with ThreadPoolExecutor(max_workers=6) as pool:
                rows = list(pool.map(lambda _: self.client.post(self.base, json={'topic':'PARTNERSHIP'}), range(6)))
            self.assertTrue(all(r.status_code == 200 for r in rows))
            self.assertTrue(all(r.json() == rows[0].json() for r in rows))
            self.assertEqual(builder.call_count, 1)
        for context in [{'topic':'UNKNOWN'}, {'focus_line':0}, {'focus_line':7}, {'focus_line':True}, {'focus_line':'3'}, {'use_relative':'wealth'}, {'question':'different'}]:
            response = self.client.post(self.base, json=context); self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.post(self.base, json={'topic':'WEALTH','focus_line':1}).status_code, 422)
        missing = '/api/v1/coins/consultations/' + str(uuid4()) + '/analysis'
        self.assertEqual(self.client.get(missing).status_code, 404)
        self.assertEqual(self.client.post(missing, json={}).status_code, 404)

    def test_rules_and_frontend_integration(self):
        rules = self.client.get('/api/v1/coins/analysis-rules').json()
        self.assertEqual(len(rules['topics']), 8)
        self.assertEqual(len(rules['rules_sha256']), 64)
        html = self.client.get('/').text
        self.assertLess(html.index('/static/liuyao.js'), html.index('/static/coins.js'))
        self.assertIn('id="coins-topic"', html)
        self.assertEqual(self.client.get('/static/liuyao.js').status_code, 200)


if __name__ == '__main__': unittest.main()
