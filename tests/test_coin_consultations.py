from collections import Counter
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
from randomyst.coins_models import CoinRequest, CoinResponse
from randomyst.coins_service import CoinService, cast_bits
from randomyst.interpretation import ExplanationRepository

ROOT = Path(__file__).resolve().parents[1]


def payload(totals=(7, 8, 9, 8, 7, 6)):
    return {'request_id': str(uuid4()), 'question': 'Việc hợp tác tôi đang chuẩn bị cần cân nhắc điều gì?',
            'source': 'MANUAL', 'casting': {'mode': 'CUSTOM', 'custom_timestamp': '2026-10-26T09:00:00+07:00'},
            'throws_bottom_to_top': [['BACK'] * (v-6) + ['INSCRIPTION'] * (9-v) for v in totals]}


class CoinCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = CoinService(ExplanationRepository())

    def test_face_counts_and_exhaustive_4096_states(self):
        counts = Counter(sum(3 if face else 2 for face in faces) for faces in product((0, 1), repeat=3))
        self.assertEqual(counts, {6: 1, 7: 3, 8: 3, 9: 1})
        pairs, originals, moving_counts = set(), set(), set()
        for totals in product((6, 7, 8, 9), repeat=6):
            bits, moving, changed = cast_bits(totals)
            self.assertEqual([i for i in range(1, 7) if bits[i-1] != changed[i-1]], moving)
            source, target = (self.service.iching.by_bits[v]['id'] for v in (bits, changed))
            pairs.add((source, target)); originals.add(source); moving_counts.add(len(moving))
        self.assertEqual((len(originals), len(pairs), moving_counts), (64, 4096, set(range(7))))

    def test_all_64_hexagrams_and_384_reference_lines(self):
        for bits in product((0, 1), repeat=6):
            request = CoinRequest.model_validate(payload([7 if bit else 8 for bit in bits]))
            data = self.service.consult(request)
            self.assertEqual(data['original']['chart']['lines_bottom_to_top'], list(bits))
            self.assertEqual(data['moving_lines'], [])
            self.assertIsNone(data['changed'])
            self.assertEqual(len(data['original']['reference_lines']), 6)
            self.assertNotIn('động', ' '.join(c['title'] for c in data['original']['reference_lines']))
            CoinResponse.model_validate(data)
        catalog = self.service.catalog()['hexagrams']
        self.assertEqual([row['hexagram_id'] for row in catalog], list(range(1, 65)))
        self.assertEqual(len({tuple(row['lines_bottom_to_top']) for row in catalog}), 64)

    def test_known_orientation_and_multiple_moving_lines(self):
        for totals, expected, moving, changed in [
            ((7,)*6, 1, [], None), ((8,)*6, 2, [], None),
            ((7,8,7,8,7,8), 63, [], None), ((8,7,8,7,8,7), 64, [], None),
            ((9,)*6, 1, [1,2,3,4,5,6], 2), ((6,)*6, 2, [1,2,3,4,5,6], 1),
            ((7,8,9,8,7,6), 63, [3,6], 42),
        ]:
            data = self.service.consult(CoinRequest.model_validate(payload(totals)))
            self.assertEqual(data['original']['chart']['hexagram_id'], expected)
            self.assertEqual(data['moving_lines'], moving)
            self.assertEqual(data['changed']['chart']['hexagram_id'] if data['changed'] else None, changed)
        both = self.service.consult(CoinRequest.model_validate(payload((9,)*6)))
        self.assertIn('Nguyên văn tham khảo 用九: 见群龙无首，吉。', both['reading_guide'])
        kun = self.service.consult(CoinRequest.model_validate(payload((6,)*6)))
        self.assertIn('Nguyên văn tham khảo 用六: 利永贞。', kun['reading_guide'])

    def test_all_eight_palaces_world_response_against_classical_lists(self):
        palaces = {
            'Càn': [1,44,33,12,20,23,35,14], 'Đoài': [58,47,45,31,39,15,62,54],
            'Ly': [30,56,50,64,4,59,6,13], 'Chấn': [51,16,40,32,46,48,28,17],
            'Tốn': [57,9,37,42,25,21,27,18], 'Khảm': [29,60,3,63,49,55,36,7],
            'Cấn': [52,22,26,41,38,10,61,53], 'Khôn': [2,24,19,11,34,43,5,8],
        }
        for name, ids in palaces.items():
            for number, world in zip(ids, [6,1,2,3,4,5,4,3]):
                bits = self.service.explanations.by_id[number]['array']
                chart = self.service.najia.chart(bits, bits, [], {'gans':[0,0,0,0], 'zhis':[0,0,0,0]})
                self.assertEqual((chart['palace'], chart['world_line']), (name, world))
                self.assertEqual(abs(chart['world_line'] - chart['response_line']), 3)
                self.assertEqual(sum(row['is_world'] for row in chart['lines_bottom_to_top']), 1)
                self.assertEqual(sum(row['is_response'] for row in chart['lines_bottom_to_top']), 1)

    def test_najia_qian_and_changed_relatives_use_original_palace(self):
        result = self.service.consult(CoinRequest.model_validate(payload((9,)*6)))
        rows = result['najia']['lines_bottom_to_top']
        self.assertEqual([row['branch'] for row in rows], ['Tý','Dần','Thìn','Ngọ','Thân','Tuất'])
        self.assertEqual([row['stem'] for row in rows], ['Giáp']*3 + ['Nhâm']*3)
        self.assertEqual([row['relative'] for row in rows], ['Tử tôn','Thê tài','Phụ mẫu','Quan quỷ','Huynh đệ','Phụ mẫu'])
        self.assertEqual([row['changed_branch'] for row in rows], ['Mùi','Tỵ','Mão','Sửu','Hợi','Dậu'])
        self.assertEqual([row['changed_relative'] for row in rows], ['Phụ mẫu','Quan quỷ','Thê tài','Phụ mẫu','Tử tôn','Huynh đệ'])

    def test_ten_day_stem_spirits_and_six_xun_voids(self):
        first = ['Thanh Long','Thanh Long','Chu Tước','Chu Tước','Câu Trần','Đằng Xà','Bạch Hổ','Bạch Hổ','Huyền Vũ','Huyền Vũ']
        for day in range(60):
            chart = self.service.najia.chart((1,)*6, (1,)*6, [], {'gans':[0,0,day%10,0], 'zhis':[0,0,day%12,0]})
            self.assertEqual(chart['lines_bottom_to_top'][0]['spirit'], first[day%10])
            self.assertEqual(len({row['spirit'] for row in chart['lines_bottom_to_top']}), 6)
            self.assertEqual(chart['void_branches'], [['Tuất','Hợi'],['Thân','Dậu'],['Ngọ','Mùi'],['Thìn','Tỵ'],['Dần','Mão'],['Tý','Sửu']][day//10])

    def test_random_uses_18_independent_coin_bits(self):
        request = payload(); request['source'] = 'RANDOM'; del request['throws_bottom_to_top']
        with patch('randomyst.coins_service.secrets.randbits', side_effect=[1]*18) as rng:
            data = self.service.consult(CoinRequest.model_validate(request))
        self.assertEqual(rng.call_count, 18)
        self.assertEqual(data['casting']['totals_bottom_to_top'], [9]*6)
        self.assertEqual(data['casting']['randomness'], 'SYSTEM_SECRETS')

    def test_calendar_uses_single_timezone_conversion_and_day_boundary(self):
        request = payload()
        request['casting']['custom_timestamp'] = '2026-10-26T21:59:59+07:00'
        before = self.service.consult(CoinRequest.model_validate(request))
        request['casting']['custom_timestamp'] = '2026-10-26T22:00:00+07:00'
        after = self.service.consult(CoinRequest.model_validate(request))
        self.assertEqual(after['calendar']['beijing_datetime'], '2026-10-26T23:00:00+08:00')
        self.assertNotEqual(before['calendar']['pillars'][2], after['calendar']['pillars'][2])
        self.assertEqual(before['original'], after['original'])
        self.assertEqual(before['changed'], after['changed'])
        self.assertNotEqual(before['najia']['lines_bottom_to_top'][0]['spirit'], after['najia']['lines_bottom_to_top'][0]['spirit'])

    def test_response_rejects_mismatched_coin_provenance(self):
        result = self.service.consult(CoinRequest.model_validate(payload()))
        bad = deepcopy(result); bad['casting']['totals_bottom_to_top'][0] = 6
        with self.assertRaises(ValidationError): CoinResponse.model_validate(bad)
        bad = deepcopy(result); bad['moving_lines'] = [1]
        with self.assertRaises(ValidationError): CoinResponse.model_validate(bad)
        bad = deepcopy(result); bad['changed'] = None
        with self.assertRaises(ValidationError): CoinResponse.model_validate(bad)


class CoinApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name) / 'test.sqlite3')
        self.app = create_app(self.path)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close(); self.directory.cleanup()

    def test_idempotency_snapshot_replay_conflict_and_history_isolation(self):
        request = payload()
        first = self.client.post('/api/v1/coins/consultations', json=request)
        self.assertEqual(first.status_code, 200, first.text)
        with patch.object(self.app.state.coins, 'consult', side_effect=AssertionError('must not recompute')):
            self.assertEqual(first.json(), self.client.post('/api/v1/coins/consultations', json=request).json())
            self.assertEqual(first.json(), self.client.get('/api/v1/coins/consultations/' + request['request_id']).json())
        changed = deepcopy(request); changed['question'] += ' đổi'
        self.assertEqual(self.client.post('/api/v1/coins/consultations', json=changed).status_code, 409)
        changed = deepcopy(request); changed['throws_bottom_to_top'][0][0] = 'INSCRIPTION'
        self.assertEqual(self.client.post('/api/v1/coins/consultations', json=changed).status_code, 409)
        reopened = TestClient(create_app(self.path), storage=self.client.storage)
        self.assertEqual(first.json(), reopened.get('/api/v1/coins/consultations/' + request['request_id']).json()); reopened.close()
        self.assertEqual(len(self.client.get('/api/v1/coins/history').json()['consultations']), 1)
        self.assertEqual(self.client.get('/api/v1/history').json()['draws'], [])
        self.assertEqual(self.client.get('/api/v1/maihoa/history').json()['consultations'], [])

    def test_concurrent_random_retries_sample_once(self):
        request = payload(); request['source'] = 'RANDOM'; del request['throws_bottom_to_top']
        with patch('randomyst.coins_service.secrets.randbits', return_value=1) as rng:
            with ThreadPoolExecutor(max_workers=6) as pool:
                responses = list(pool.map(lambda _: self.client.post('/api/v1/coins/consultations', json=request), range(6)))
        self.assertTrue(all(r.status_code == 200 for r in responses))
        self.assertTrue(all(r.json() == responses[0].json() for r in responses))
        self.assertEqual(rng.call_count, 18)

    def test_catalog_read_only_and_missing_32_commentary_is_explicit(self):
        self.assertEqual(len(self.client.get('/api/v1/coins/hexagrams').json()['hexagrams']), 64)
        result = self.client.get('/api/v1/coins/hexagrams/32')
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()['text']['source_gaps'])
        self.assertEqual(self.client.get('/api/v1/coins/history').json()['consultations'], [])
        for number in ['0','65','abc']:
            self.assertEqual(self.client.get('/api/v1/coins/hexagrams/' + number).status_code, 422)
        self.assertEqual(self.client.get('/api/v1/coins/consultations/' + str(uuid4())).status_code, 404)
        self.assertEqual(self.client.get('/api/v1/coins/history?limit=0').status_code, 422)

    def test_input_validation_and_html_are_integrated(self):
        invalids = []
        for field, value in [('source','OTHER'), ('question','    '), ('throws_bottom_to_top',None), ('throws_bottom_to_top',[]), ('request_id','bad')]:
            request = payload(); request[field] = value; invalids.append(request)
        for rows in [[['BACK']*3]*5, [['BACK']*2]*6, [['YANG']*3]*6, [[True]*3]*6]:
            request = payload(); request['throws_bottom_to_top'] = rows; invalids.append(request)
        request = payload(); request['source'] = 'RANDOM'; invalids.append(request)
        request = payload(); request['casting']['custom_timestamp'] = '2026-10-26T09:00:00'; invalids.append(request)
        request = payload(); request['casting']['custom_timestamp'] = '2031-01-01T09:00:00+07:00'; invalids.append(request)
        for request in invalids:
            response = self.client.post('/api/v1/coins/consultations', json=request)
            self.assertEqual(response.status_code, 422, response.text)
        html = self.client.get('/').text
        self.assertIn('id="show-coins"', html)
        self.assertIn('/static/coins.js', html)
        self.assertEqual(self.client.get('/static/coins.js').status_code, 200)


if __name__ == '__main__': unittest.main()
