"""Timezone and boundary integration fixtures; published dates are from HKO.

These checks do not establish independent astronomical accuracy over all years.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from random import Random
import tempfile
import unittest
from uuid import uuid4

from tests.browser_client import TestClient
from jsonschema import Draft202012Validator, ValidationError

from randomyst.api import create_app
from randomyst.engine import NumberEngine
from randomyst.models import DrawRequest
from randomyst.time_engine import beijing_clock, pillars, resolve_maihoa

ROOT = Path(__file__).resolve().parents[1]


def request_at(timestamp):
    return {'request_id': str(uuid4()), 'birth': {'civil_datetime': '1994-10-08T05:00:00+07:00'},
            'casting': {'mode': 'CUSTOM', 'custom_timestamp': timestamp}}


class BeijingCalendarTests(unittest.TestCase):
    def test_ten_vietnam_is_eleven_beijing_and_ngo_hour(self):
        civil = datetime.fromisoformat('2026-10-11T10:00:00.123456+07:00')
        clock = beijing_clock(civil)
        result = resolve_maihoa(civil)
        self.assertEqual(clock['beijing_datetime'], '2026-10-11T11:00:00.123456+08:00')
        self.assertEqual(datetime.fromisoformat(clock['beijing_datetime']), civil)
        self.assertEqual(result['maihoa_inputs'], {'Y': 7, 'M': 9, 'D': 2, 'H': 7})
        engine = NumberEngine()
        drawn = engine.draw(DrawRequest.model_validate(request_at(civil.isoformat())), rng=Random(34))
        self.assertEqual(drawn['trace']['maihoa']['variables'], result['maihoa_inputs'])
        self.assertEqual(drawn['trace']['maihoa']['original']['hexagram_id'], 43)
        self.assertEqual(drawn['trace']['maihoa']['moving_line'], 1)

    def test_chinese_new_year_rolls_all_ymd_at_midnight_beijing(self):
        # HKO 2024 calendar: Feb 9 = lunar 12/30; Feb 10 = 1/1.
        before = resolve_maihoa(datetime.fromisoformat('2024-02-09T22:59:59+07:00'))
        at = resolve_maihoa(datetime.fromisoformat('2024-02-09T23:00:00+07:00'))
        self.assertEqual(before['maihoa_inputs'], {'Y': 4, 'M': 12, 'D': 30, 'H': 1})
        self.assertEqual(at['maihoa_inputs'], {'Y': 5, 'M': 1, 'D': 1, 'H': 1})
        self.assertEqual(at['effective_date'], '2024-02-10')

    def test_23_beijing_changes_hour_without_advancing_lunar_date(self):
        # Direct civil-date lookup: no leftover TST+1h or double timezone addition.
        before = resolve_maihoa(datetime.fromisoformat('2024-02-09T21:59:59+07:00'))
        at = resolve_maihoa(datetime.fromisoformat('2024-02-09T22:00:00+07:00'))
        self.assertEqual(before['maihoa_inputs']['H'], 12)
        self.assertEqual(at['maihoa_inputs']['H'], 1)
        self.assertEqual([at['maihoa_inputs'][k] for k in ('Y', 'M', 'D')], [4, 12, 30])

    def test_leap_month_keeps_month_number(self):
        # HKO 2025: June 25 starts month 6; July 25 starts the second month 6.
        normal = resolve_maihoa(datetime.fromisoformat('2025-06-25T10:00:00+07:00'))
        leap = resolve_maihoa(datetime.fromisoformat('2025-07-25T10:00:00+07:00'))
        self.assertEqual((normal['lunar']['month'], normal['lunar']['day'], normal['lunar']['is_leap_month']), (6, 1, False))
        self.assertEqual((leap['lunar']['month'], leap['lunar']['day'], leap['lunar']['is_leap_month']), (6, 1, True))
        self.assertEqual(leap['maihoa_inputs']['M'], 6)

    def test_every_hour_branch_boundary_uses_beijing_clock(self):
        vn = timezone(timedelta(hours=7))
        for hour in range(0, 24, 2):
            at = datetime(2026, 10, 11, hour, 0, 0, tzinfo=vn)
            before = resolve_maihoa(at-timedelta(seconds=1))['maihoa_inputs']['H']
            after = resolve_maihoa(at)['maihoa_inputs']['H']
            expected = ((hour+2)//2) % 12 + 1
            self.assertEqual(after, expected)
            self.assertEqual(before, (expected-2) % 12 + 1)

    def test_input_range_uses_vn_year_before_beijing_year_overflow(self):
        with tempfile.TemporaryDirectory() as directory, TestClient(create_app(Path(directory)/'draws.sqlite3')) as client:
            data = request_at('2030-12-31T23:55:00+07:00')
            data['birth']['civil_datetime'] = '1950-01-01T00:05:00+07:00'
            response = client.post('/api/v1/draw', json=data)
            self.assertEqual(response.status_code, 200, response.text)
            trace = response.json()['trace']
            self.assertEqual(trace['casting_calendar']['effective_date'], '2031-01-01')
            self.assertEqual(trace['birth_calendar']['lunar']['year'], 1949)
            data['request_id'] = str(uuid4())
            data['casting']['custom_timestamp'] = '2031-01-01T00:00:00+07:00'
            self.assertEqual(client.post('/api/v1/draw', json=data).status_code, 422)

    def test_same_instant_keeps_bazi_and_clock_even_with_other_offset(self):
        instant = datetime.fromisoformat('2026-10-11T10:00:00+07:00')
        self.assertEqual(pillars(instant), pillars(instant.astimezone(timezone.utc)))
        a, b = beijing_clock(instant), beijing_clock(instant.astimezone(timezone.utc))
        self.assertEqual(a['beijing_datetime'], b['beijing_datetime'])

    def test_clock_boundary_uncertainty_only_no_location_or_eot_error(self):
        instant = datetime.fromisoformat('2026-10-11T22:59:58+07:00')
        clock = beijing_clock(instant, 3)
        self.assertEqual(clock['boundary']['status'], 'BOUNDARY')
        self.assertEqual(clock['boundary']['distance_to_calendar_day_boundary_seconds'], 2)
        self.assertEqual(clock['boundary']['missing_components'], [])
        self.assertNotIn('longitude_used', clock)
        self.assertFalse(clock['true_solar_time_applied'])

    def test_v4_interpretation_context_requires_beijing_contract(self):
        schema = json.loads((ROOT/'schemas/interpretation_context.schema.json').read_text())
        validator = Draft202012Validator(schema)
        old = json.loads((ROOT/'schemas/examples/interpretation_context.example.json').read_text())
        validator.validate(old)
        new = deepcopy(old)
        new['rules_version'] = 'mvp1-logic-2026-10-11-v4'
        with self.assertRaises(ValidationError):
            validator.validate(new)
        new['computed_facts']['time_context'] = {
            'civil_datetime': '2026-10-11T01:30:00+07:00', 'actual_utc_instant': '2026-10-10T18:30:00Z',
            'beijing_datetime': '2026-10-11T02:30:00+08:00', 'effective_date': '2026-10-11',
            'calendar_algorithm_id': '6tail-chinese-utc8-v1', 'calendar_validation_status': 'INTEGRATION_TESTED',
            'boundary_status': 'UNKNOWN_UNCERTAINTY', 'true_solar_time_applied': False}
        validator.validate(new)
        new['computed_facts']['time_context']['true_solar_time_applied'] = True
        with self.assertRaises(ValidationError):
            validator.validate(new)

    def test_idempotency_preserves_historical_v3_result(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(Path(directory)/'draws.sqlite3')
            data = json.loads((ROOT/'docs/archive/draw_request_v3.json').read_text())
            request = DrawRequest.model_validate(data)
            old = json.loads((ROOT/'docs/archive/draw_response_v3.json').read_text())
            with TestClient(app) as client:
                client.storage.append({'kind':'DRAW','key':old['request_id'],'data':old,'signature':app.state.signer.sign('DRAW',old),'identity':data})
                replay = client.post('/api/v1/draw', json=data)
                self.assertEqual(replay.status_code, 200, replay.text)
                self.assertEqual(replay.json(), old)
                self.assertEqual(client.get('/api/v1/history').json()['draws'][0]['rules_version'], old['rules_version'])
                data['request_id'] = str(uuid4())
                self.assertEqual(client.post('/api/v1/draw', json=data).json()['rules_version'], 'mvp1-logic-2026-10-26-v6')

    def test_v5_interpretation_accepts_expanded_pool_with_beijing_clock(self):
        schema=json.loads((ROOT/'schemas/interpretation_context.schema.json').read_text())
        validator=Draft202012Validator(schema)
        data=json.loads((ROOT/'schemas/examples/interpretation_context.example.json').read_text())
        data['rules_version']='mvp1-logic-2026-10-26-v5'
        data['computed_facts']['number_result']['numbers']=['00','46','57','68','79','99']
        with self.assertRaises(ValidationError):
            validator.validate(data)
        data['computed_facts']['time_context']={
            'civil_datetime':'2026-10-11T01:30:00+07:00','actual_utc_instant':'2026-10-10T18:30:00Z',
            'beijing_datetime':'2026-10-11T02:30:00+08:00','effective_date':'2026-10-11',
            'calendar_algorithm_id':'6tail-chinese-utc8-v1','calendar_validation_status':'INTEGRATION_TESTED',
            'boundary_status':'UNKNOWN_UNCERTAINTY','true_solar_time_applied':False}
        validator.validate(data)
        data['rules_version']='mvp1-logic-2026-10-26-v6'
        data['computed_facts']['number_result']['threshold']=80
        validator.validate(data)
        data['computed_facts']['number_result']['numbers'][-1]='100'
        with self.assertRaises(ValidationError):
            validator.validate(data)
        data['computed_facts']['number_result']['numbers'][-1]='99'
        data['rules_version']='mvp1-logic-2026-10-11-v4'
        with self.assertRaises(ValidationError):
            validator.validate(data)
