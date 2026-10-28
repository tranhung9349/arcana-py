from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from itertools import product
import json
from pathlib import Path
from random import Random
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import patch

from tests.browser_client import TestClient
from lunar_python import Solar
from pydantic import ValidationError

from randomyst.api import create_app
from randomyst.bazi import analyze, star_bonuses
from randomyst.engine import EngineError, NumberEngine
from randomyst.maihoa import IchingRepository, TRIGRAMS
from randomyst.models import DrawRequest, DrawResponse, Location
from randomyst.sampling import ELEMENTS, Configuration, Distribution, configurations, element_of, select_context, validate_sample
from randomyst.time_engine import BEIJING, beijing_clock, pillars, resolve_maihoa, solar_month

ROOT = Path(__file__).resolve().parents[1]

def payload():
    return {'request_id':str(uuid4()),'birth':{'civil_datetime':'1994-10-08T05:00:00+07:00','location':{'longitude':105.85,'latitude':21.03,'source':'MANUAL'}},
            'casting':{'mode':'CUSTOM','custom_timestamp':'2026-10-11T01:30:00+07:00','location':{'longitude':106.66,'latitude':10.78,'source':'MANUAL'}}}


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=NumberEngine()

    def test_all_64_hexagrams_and_384_changes(self):
        repository=IchingRepository()
        seen=set()
        for upper,lower in product(range(1,9),repeat=2):
            bits=TRIGRAMS[lower][2]+TRIGRAMS[upper][2]
            original=repository.metadata(bits)
            seen.add(original['hexagram_id'])
            for position in range(1,7):
                changed=list(bits);changed[position-1]^=1
                found=repository.metadata(changed)
                self.assertEqual(sum(a!=b for a,b in zip(bits,found['lines_bottom_to_top'])),1)
        self.assertEqual(len(seen),64)
        example=repository.calculate({'Y':7,'M':9,'D':2,'H':2})
        self.assertEqual((example['original']['hexagram_id'],example['moving_line'],example['display_hexagrams']['mutual']['hexagram_id'],example['display_hexagrams']['changed']['hexagram_id']),(17,2,53,58))
        with self.assertRaises(ValueError):repository.calculate({'Y':7,'M':9,'D':2,'H':2,'seconds':1})
        thirty_two=next(bits for bits,row in repository.by_bits.items() if row['id']==32)
        self.assertNotIn('iching__32',repository.tuan)

    def test_library_jie_changes_at_beijing_instant(self):
        boundary=datetime.fromisoformat('2026-02-04T03:02:08+07:00')
        before,after=boundary-timedelta(seconds=1),boundary
        self.assertEqual(solar_month(before)['month_branch_index'],1)
        self.assertEqual(solar_month(after)['month_branch_index'],2)
        self.assertEqual(pillars(before)['zhis'][0],5)
        self.assertEqual(pillars(after)['zhis'][0],6)
        # Mai Hoa's lunar year still waits for Chinese New Year.
        self.assertEqual(resolve_maihoa(before)['maihoa_inputs']['Y'],6)
        self.assertEqual(resolve_maihoa(after)['maihoa_inputs']['Y'],6)

    def test_bazi_day_rollover_at_23_beijing_and_maihoa_midnight(self):
        civil=datetime.fromisoformat('1994-10-08T21:59:59+07:00')
        before=pillars(civil)
        after=pillars(civil+timedelta(seconds=1))
        midnight=pillars(civil+timedelta(hours=1,seconds=1))
        self.assertEqual((before['zhis'][3],after['zhis'][3],midnight['zhis'][3]),(11,0,0))
        self.assertEqual(after['gans'][2:],midnight['gans'][2:])
        self.assertEqual(after['effective_date'],'1994-10-09')
        maihoa=resolve_maihoa(civil+timedelta(seconds=1),kind='birth')
        self.assertEqual(maihoa['effective_date'],'1994-10-08')

    def test_clock_metadata_has_no_solar_correction(self):
        civil=datetime.fromisoformat('2026-10-11T10:00:00+07:00')
        metadata=beijing_clock(civil)
        self.assertEqual(metadata['beijing_datetime'],'2026-10-11T11:00:00+08:00')
        self.assertFalse(metadata['true_solar_time_applied'])
        self.assertEqual(metadata['boundary']['missing_components'],['clock_uncertainty'])
        self.assertNotIn('eot_minutes',metadata)

    def test_natal_stars_dedup_multi_element_and_casting_month(self):
        # At day-stem Yi, Thien At matches both Shen/Metal and Zi/Water once.
        result=star_bonuses([0,0,1,0],[8,0,8,0],2)
        self.assertEqual(result['delta_by_element']['Kim'],.2)
        self.assertEqual(result['delta_by_element']['Thủy'],.2)
        self.assertEqual(len(result['active_stars']),1)
        # Casting Dan -> stem Dinh; match natal stems, not arbitrary converted branches.
        hit=star_bonuses([3,0,1,0],[8,0,8,0],2)
        self.assertEqual(hit['delta_by_element']['Hỏa'],.2)
        self.assertEqual(len(hit['active_stars']),2)

    def test_draw_output_and_frozen_retry(self):
        request=DrawRequest.model_validate(payload())
        found_retry=False
        for seed in range(10):
            result=self.engine.draw(request,rng=Random(seed))
            self.assertEqual(len(set(result['numbers'])),6)
            self.assertTrue(all(len(n)==2 and 0<=int(n)<=99 for n in result['numbers']))
            self.assertEqual([row['number'] for row in result['trace']['weights']], [f'{n:02d}' for n in range(100)])
            self.assertEqual(result['status'],'OPTIMAL')
            self.assertLessEqual(result['attempts'],2)
            history=result['trace']['attempt_history']
            self.assertTrue(all(row['g_cap']==result['trace']['g_cap'] for row in history))
            if len(history)>1:
                found_retry=True
                self.assertEqual(sum(int(n)%2==0 for n in result['numbers']),3)
        self.assertTrue(found_retry)

    def test_pool_endpoints_and_new_numbers_can_be_sampled(self):
        context,_=select_context('Mộc','Kim','Kim')
        numbers=(0,46,57,68,79,99)
        configs=configurations(context,pool=numbers)
        sampled,_=Distribution(configs,{n:1 for n in numbers}).sample(Random(42))
        self.assertEqual(sampled,numbers)
        self.assertTrue(validate_sample(sampled,context))
        self.assertFalse(validate_sample((0,46,57,68,79,100),context))

    def test_response_accepts_full_two_digit_range_and_rejects_invalid_formats(self):
        result=self.engine.draw(DrawRequest.model_validate(payload()),rng=Random(0))
        result['numbers']=['00','46','57','68','79','99']
        DrawResponse.model_validate(result)
        for invalid in ('-1','100','9','９９'):
            with self.subTest(number=invalid):
                changed=deepcopy(result)
                changed['numbers'][-1]=invalid
                with self.assertRaises(ValidationError):
                    DrawResponse.model_validate(changed)

    def test_all_125_runtime_contexts_hard_rules_and_retry_cap(self):
        rng=Random(4321)
        for primary,the,dung in product(ELEMENTS,repeat=3):
            context,_=select_context(primary,the,dung)
            self.assertEqual(context.threshold,85 if context.state=='DAI_HUNG' else 80)
            first=configurations(context)
            cap=max(c.raw_units for c in first)
            retry=[c for c in configurations(context,retry=True) if c.meets(cap,context.threshold)]
            self.assertTrue(retry)
            weights={n:1 for n in self.engine.pool if context.allowed(element_of(n))}
            for distribution,is_retry in ((Distribution(first,weights),False),(Distribution(retry,weights),True)):
                for _ in range(3):
                    numbers,configuration=distribution.sample(rng)
                    self.assertTrue(validate_sample(numbers,context,retry=is_retry))
                    if is_retry:self.assertTrue(configuration.meets(cap,context.threshold))

    def test_threshold_80_is_an_actual_unrounded_acceptance_gate(self):
        counts=(3,3,0,0,0,0,0,0,0,0)
        self.assertFalse(Configuration(counts,199,0,3).meets(300,80))
        self.assertTrue(Configuration(counts,200,0,3).meets(300,80))

    def test_legacy_locations_do_not_change_calendar_or_numbers(self):
        data=payload()
        baseline=self.engine.draw(DrawRequest.model_validate(data),rng=Random(34))
        data['birth'].pop('location')
        data['casting']['location']={'longitude':-150,'source':'DEVICE','accuracy_m':2000,'latitude':80,'acquired_at':'2020-01-01T00:00:00Z'}
        changed=self.engine.draw(DrawRequest.model_validate(data),rng=Random(34))
        for key in ('numbers','score','threshold'):
            self.assertEqual(baseline[key],changed[key])
        for key in ('bazi','maihoa','birth_time','casting_time','weights'):
            self.assertEqual(baseline['trace'][key],changed['trace'][key])
        self.assertFalse(changed['trace']['legacy_location_fields_used'])

    def test_suboptimal_fallback_keeps_best_valid_set_after_five(self):
        request=DrawRequest.model_validate(payload())
        def restricted(context, retry=False, **kwargs):
            choices=configurations(context,retry=retry)
            if retry:
                return (min(choices,key=lambda c:c.raw_units),)
            return (max((c for c in choices if c.even_count in (1,5)),key=lambda c:c.raw_units),)
        # Simulate a future restricted feasible space without changing the scoring rules.
        with patch('randomyst.engine.configurations',side_effect=restricted):
            result=self.engine.draw(request,rng=Random(12))
        self.assertEqual(result['status'],'SUB_OPTIMAL')
        self.assertEqual(result['attempts'],5)
        self.assertEqual(result['selected_attempt'],1)
        self.assertEqual(len(set(result['numbers'])),6)
        self.assertLess(result['score'],result['threshold'])

    def test_display_hexagrams_cannot_change_numbers_weights_or_score(self):
        request=DrawRequest.model_validate(payload())
        baseline=self.engine.draw(request,rng=Random(77))
        original_calculate=self.engine.iching.calculate
        def altered(variables):
            result=original_calculate(variables)
            result['display_hexagrams']['mutual']=None
            result['display_hexagrams']['changed']=None
            return result
        with patch.object(self.engine.iching,'calculate',side_effect=altered):
            changed=self.engine.draw(request,rng=Random(77))
        self.assertEqual(baseline['numbers'],changed['numbers'])
        self.assertEqual(baseline['score'],changed['score'])
        self.assertEqual(baseline['trace']['weights'],changed['trace']['weights'])
        self.assertEqual(baseline['trace']['g_cap'],changed['trace']['g_cap'])

    def test_pillars_match_6tail_converted_beijing_clock(self):
        # Integration comparison, not independent proof of the library calendar.
        rng=Random(443)
        for _ in range(100):
            civil=datetime(rng.randrange(1950,2027),rng.randrange(1,13),rng.randrange(10,20),rng.randrange(24),17,tzinfo=timezone(timedelta(hours=7)))
            mine=pillars(civil)
            utc8=civil.astimezone(BEIJING)
            chart=Solar.fromYmdHms(utc8.year,utc8.month,utc8.day,utc8.hour,utc8.minute,utc8.second).getLunar().getEightChar()
            chart.setSect(1)
            expected=[chart.getYear(),chart.getMonth(),chart.getDay(),chart.getTime()]
            self.assertEqual([p['stem_zh']+p['branch_zh'] for p in mine['pillars']],expected)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.client=TestClient(create_app(Path(self.directory.name)/'draws.sqlite3'))

    def tearDown(self):
        self.client.close();self.directory.cleanup()

    def test_api_idempotency_history_and_conflicting_payload(self):
        data=payload()
        first=self.client.post('/api/v1/draw',json=data)
        self.assertEqual(first.status_code,200,first.text)
        second=self.client.post('/api/v1/draw',json=data)
        self.assertEqual(first.json(),second.json())
        self.assertEqual(len(self.client.get('/api/v1/history').json()['draws']),1)
        changed=deepcopy(data);changed['birth']['override_dung_than']='Kim'
        self.assertEqual(self.client.post('/api/v1/draw',json=changed).status_code,409)
        self.assertEqual(self.client.get('/api/v1/health').json()['set_size'],6)
        self.assertEqual(self.client.get('/').status_code,200)

    def test_api_draw_and_history_support_expanded_pool(self):
        health=self.client.get('/api/v1/health').json()
        self.assertEqual(health['pool'],[0,99])
        self.assertEqual(health['rules_version'],'mvp1-logic-2026-10-26-v6')
        data=payload()
        engine=self.client.app.state.engine
        draw=engine.draw
        with patch.object(engine,'draw',side_effect=lambda request,received:draw(request,received,rng=Random(0))):
            response=self.client.post('/api/v1/draw',json=data)
        self.assertEqual(response.status_code,200,response.text)
        result=response.json()
        self.assertTrue(any(int(n)>45 for n in result['numbers']))
        self.assertEqual(self.client.get('/api/v1/draw/'+data['request_id']).json(),result)
        self.assertEqual(self.client.post('/api/v1/draw',json=data).json(),result)
        self.assertEqual(self.client.get('/api/v1/history').json()['draws'][0]['numbers'],result['numbers'])

    def test_concurrent_same_request_creates_one_result(self):
        data=payload()
        with ThreadPoolExecutor(max_workers=3) as pool:
            responses=list(pool.map(lambda _:self.client.post('/api/v1/draw',json=data),range(3)))
        self.assertTrue(all(r.status_code==200 for r in responses))
        self.assertEqual(responses[0].json(),responses[1].json())
        self.assertEqual(responses[0].json(),responses[2].json())
        self.assertEqual(len(self.client.get('/api/v1/history').json()['draws']),1)

    def test_invalid_input_timezone_range_and_multiple_sets_parameter(self):
        for edit in ('timezone','year','quantity'):
            data=payload()
            if edit=='timezone':data['birth']['civil_datetime']='1994-10-08T05:00:00+08:00'
            elif edit=='year':data['birth']['civil_datetime']='1949-10-08T05:00:00+07:00'
            else:data['quantity']=2
            response=self.client.post('/api/v1/draw',json=data)
            self.assertEqual(response.status_code,422)
            self.assertEqual(response.json()['error']['code'],'VALIDATION_FAILED')

    def test_current_click_timestamp_preserved_with_clock_warning(self):
        data=payload();data['casting']={'mode':'CURRENT','clicked_at':'2026-10-11T01:30:00+07:00','location':{'longitude':105,'source':'DEFAULT'}}
        response=self.client.post('/api/v1/draw',json=data)
        self.assertEqual(response.status_code,200,response.text)
        result=response.json()
        self.assertEqual(result['trace']['casting_time']['civil_datetime'],data['casting']['clicked_at'])
        self.assertIn('CLIENT_CLOCK_SKEW',[w['code'] for w in result['warnings']])
        self.assertEqual(result['trace']['casting_time']['beijing_datetime'],'2026-10-11T02:30:00+08:00')
        self.assertEqual(self.client.get('/api/v1/location').status_code,404)


if __name__=='__main__':unittest.main()
