from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.browser_client import TestClient
from jsonschema import Draft202012Validator
from lunar_python import Solar
from pydantic import ValidationError

from randomyst.api import create_app
from randomyst.date_engine import DateEngine, analyze, pillars
from randomyst.date_models import DateRules, DateSearchRequest, DateSearchResponse
from randomyst.date_rules import activity_status
from randomyst.time_engine import BEIJING

ROOT = Path(__file__).resolve().parents[1]


def payload(activity="BUSINESS_OPENING", start="2026-10-12", end="2026-10-12", details=True):
    subjects = [{"subject_id": "a", "birth": {"civil_datetime": "1994-10-08T05:00:00+07:00"}}]
    if activity == "MARRIAGE":
        subjects.append({"subject_id": "b", "birth": {"civil_datetime": "1990-06-15T09:30:00+07:00"}})
    return {"activity": activity, "subjects": subjects, "date_range": {"start": start, "end": end}, "include_details": details}


class DateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = DateEngine()

    def search(self, data):
        result = self.engine.search(DateSearchRequest.model_validate(data))
        DateSearchResponse.model_validate(result)
        return result

    def test_rules_schema_and_invalid_effect_unknown_fact(self):
        rules = json.loads((ROOT / 'config/mvp2_date_rules.json').read_text())
        Draft202012Validator(json.loads((ROOT / 'schemas/mvp2_date_rules.schema.json').read_text())).validate(rules)
        DateRules.model_validate(rules)
        for mutation in ('points', 'fact', 'target', 'source'):
            bad = deepcopy(rules)
            if mutation == 'points': bad['rules'][0]['effect'] = 'BLOCK'
            if mutation == 'fact': bad['rules'][0]['when']['fact'] = '__unknown__'
            if mutation == 'target': bad['month_tables']['sat_chu'][0] = 12
            if mutation == 'source': bad['rules'][0]['source_id'] = 'absent'
            with self.assertRaises(ValidationError): DateRules.model_validate(bad)

    def test_activity_status_missing_global_and_conflicting_tokens(self):
        cases = [(['嫁娶'], [], 'SUPPORTED'), ([], ['嫁娶'], 'AVOID'), (['无'], ['无'], 'NOT_LISTED'),
                 (['嫁娶'], ['嫁娶'], 'UNRESOLVED'), (['嫁娶'], ['诸事不宜'], 'UNRESOLVED'),
                 (['祭祀', '馀事勿取'], ['无'], 'AVOID'), (['嫁娶','馀事勿取'], ['无'], 'SUPPORTED')]
        for yi,ji,expected in cases: self.assertEqual(activity_status(yi,ji,'嫁娶'),expected)

    def test_all_candidate_month_tables_and_distinct_triple_support(self):
        evaluator = self.engine.evaluator
        for fact, table, rule_id in [('sat_chu', evaluator.config.month_tables.sat_chu, 'SAT_CHU'),
                                      ('tho_tu', evaluator.config.month_tables.tho_tu, 'THO_TU'),
                                      ('nguyet_pha', evaluator.config.month_tables.nguyet_pha, 'NGUYET_PHA')]:
            for month, target in enumerate(table):
                rows, values = evaluator.evaluate({'gans':(0,0,0,0), 'zhis':(0,month,target,0), 'calendar_class':'HOANG_DAO'}, 'MARRIAGE')
                self.assertTrue(values[fact])
                self.assertIn(rule_id, [r['rule_id'] for r in rows if r['effect']=='BLOCK'])
        for branches, expected in [((8,0,4,0),'FULL'), ((4,0,4,0),'PAIR'), ((4,4,4,0),'NONE')]:
            _, values = evaluator.evaluate({'gans':(0,0,0,0), 'zhis':branches, 'calendar_class':'HOANG_DAO'}, 'TRAVEL')
            self.assertEqual(values['ambient_support'], expected)

    def test_two_twelve_systems_and_penalty_dedupe(self):
        rows = list(self.engine.calendar.data['days'].values())
        self.assertEqual(len({d['day_officer'] for d in rows}),12)
        for kind in ('黄道','黑道'):
            self.assertEqual(len({d['tian_shen'] for d in rows if d['tian_shen_type']==kind}),6)
        evaluator = self.engine.evaluator
        first = evaluator.config.rules[0]
        duplicate = first.model_copy(update={'rule_id':'DUPLICATE_FOR_TEST'})
        config = evaluator.config.model_copy(update={'rules':[*evaluator.config.rules,duplicate]})
        with patch.object(evaluator,'config',config):
            matches,_ = evaluator.evaluate({'gans':(0,0,0,0),'zhis':(0,0,0,0),'calendar_class':'HAC_DAO'},'TRAVEL')
        self.assertEqual(len([r for r in matches if r['dedupe_group']==first.dedupe_group]),1)

    def test_full_93_day_request_initializes_two_profiles_only_once(self):
        data = payload('MARRIAGE', '2026-10-12', '2027-01-12', False)
        with patch('randomyst.date_engine.analyze', wraps=analyze) as a, patch('randomyst.date_engine.pillars', wraps=pillars) as p:
            result = self.search(data)
        self.assertEqual((a.call_count,p.call_count),(2,2))
        self.assertEqual(len(result['days']),93)
        self.assertGreaterEqual(result['personal_comparisons'],2418)
        self.assertEqual(result['natal_analysis_count'],2)
        self.assertEqual(result['disabled_rules'],['TAM_NUONG'])
        self.assertTrue(all(d['assessment_state']=='COMPLETE' for d in result['days']))
        self.assertTrue(all(len(d['windows'])<=3 for d in result['days']))

    def test_all_recommended_intervals_survive_summary_limit_and_boundaries(self):
        # Isolate aggregation from scoring: every genuine calendar interval is GOOD.
        original_window = self.engine.window
        def good_window(*args):
            row = original_window(*args)
            row.update(grade='GOOD', score=80, raw_score=80, assessment_state='COMPLETE', hard_exclusions=[])
            return row
        for day in ('2026-10-08', '2030-12-31'):
            data = payload(start=day, end=day, details=False)
            with patch.object(self.engine, 'window', side_effect=good_window):
                summary = self.search(data)['days'][0]
                data['include_details'] = True
                full = self.search(data)['days'][0]
            self.assertEqual(len(summary['windows']), 3)
            self.assertGreater(len(summary['recommended_windows']), 3)
            expected = [{key: w[key] for key in ('start_at', 'end_at', 'hour_branch')} for w in full['windows']]
            self.assertEqual(summary['recommended_windows'], expected)
            self.assertEqual(full['recommended_windows'], expected)
            self.assertEqual(summary['recommended_minutes'], 1440)
            self.assertEqual(expected[-1]['end_at'], str(datetime.fromisoformat(day)+timedelta(days=1)).replace(' ', 'T')+'+07:00')
            for row in expected:
                dt = datetime.fromisoformat(row['start_at']).astimezone(BEIJING)
                self.assertEqual(row['hour_branch'], Solar.fromYmdHms(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second).getLunar().getTimeZhi())
            if day == '2026-10-08':
                self.assertIn('2026-10-08T13:29:17+07:00', [r['start_at'] for r in expected])

    def test_recommendations_only_include_good_windows_and_respect_filters(self):
        data = payload(start='2026-12-29', end='2026-12-29', details=True)
        data['subjects'][0]['birth']['override_dung_than'] = 'Thổ'
        data['allowed_hours'] = {'start':'08:30', 'end':'20:15'}
        full = self.search(data)
        data['include_details'] = False
        compact = self.search(data)
        self.assertGreater(len(full['days'][0]['recommended_windows']), 3)
        for d, brief in zip(full['days'], compact['days']):
            expected = [{key: w[key] for key in ('start_at','end_at','hour_branch')} for w in d['windows'] if w['grade']=='GOOD']
            self.assertEqual(d['recommended_windows'], expected)
            self.assertEqual(brief['recommended_windows'], expected)
            self.assertEqual(d['recommended_minutes'], sum((datetime.fromisoformat(r['end_at'])-datetime.fromisoformat(r['start_at'])).total_seconds()/60 for r in expected))
            self.assertTrue(all(r['start_at'][11:] >= '08:30:00+07:00' and r['end_at'][11:] <= '20:15:00+07:00' for r in expected))
        data['date_range'] = {'start':'2026-10-13','end':'2026-10-13'}
        data['allowed_weekdays'] = [0]  # Tuesday is filtered out.
        self.assertEqual(self.search(data)['days'][0]['recommended_windows'], [])

    def test_repetition_and_subject_order_keep_scores_and_decisions(self):
        data = payload('MARRIAGE','2026-10-12','2026-10-14')
        first = self.search(data)
        self.assertEqual(first,self.search(data))
        data['subjects'].reverse()
        second = self.search(data)
        for da,db in zip(first['days'],second['days']):
            self.assertEqual((da['grade'],da['score']),(db['grade'],db['score']))
            for a,b in zip(da['windows'],db['windows']):
                self.assertEqual((a['score'],a['hard_exclusions']),(b['score'],b['hard_exclusions']))

    def test_interval_partition_timezone_boundaries_and_last_year(self):
        for day in ('2026-10-12','2026-10-08','2030-12-31'):
            result = self.search(payload(start=day,end=day))
            rows = result['days'][0]['windows']
            self.assertEqual(sum(w['duration_seconds'] for w in rows),86400)
            for a,b in zip(rows,rows[1:]): self.assertEqual(a['end_at'],b['start_at'])
            self.assertTrue(all(w['start_at'].endswith('+07:00') for w in rows))
        rows = self.search(payload())['days'][0]['windows']
        at22 = next(w for w in rows if 'T22:00:' in w['start_at'])
        at23 = next(w for w in rows if 'T23:00:' in w['start_at'])
        self.assertNotEqual(at22['civil_day_ganzhi'],at22['bazi_day_ganzhi'])
        self.assertEqual(at23['civil_day_ganzhi'],at23['bazi_day_ganzhi'])

    def test_exact_jie_split_and_corpus_changes_month_earlier(self):
        result = self.search(payload(start='2026-10-08',end='2026-10-08'))
        rows = result['days'][0]['windows']
        after = next(i for i,w in enumerate(rows) if w['start_at']=='2026-10-08T13:29:17+07:00')
        self.assertNotEqual(rows[after-1]['month_ganzhi_exact'],rows[after]['month_ganzhi_exact'])
        for point in ('2026-10-07T22:59:59+07:00','2026-10-07T23:00:00+07:00'):
            dt=datetime.fromisoformat(point);facts=self.engine.calendar.at(dt)
            self.assertEqual(facts['civil_day']['month_gan_zhi'],Solar.fromYmdHms(*[getattr(dt.astimezone(BEIJING),x) for x in ('year','month','day','hour','minute','second')]).getLunar().getMonthInGanZhi())

    def test_full_raw_corpus_day_hour_integrity_and_provider_spot_checks(self):
        cal = self.engine.calendar
        self.assertEqual(len(cal.data['days']),2558)
        self.assertEqual(sum(len(d['hours']) for d in cal.data['days'].values()),33254)
        for point in ('2024-02-09T23:00:00+07:00','2025-07-25T10:00:00+07:00','2026-10-12T22:00:00+07:00','2030-12-31T23:59:59+07:00'):
            dt=datetime.fromisoformat(point);bj=dt.astimezone(BEIJING)
            l=Solar.fromYmdHms(bj.year,bj.month,bj.day,bj.hour,bj.minute,bj.second).getLunar()
            facts=cal.at(dt)
            self.assertEqual((facts['civil_day']['yi'],facts['civil_day']['ji']),(l.getDayYi(1),l.getDayJi(1)))
            self.assertEqual((facts['civil_hour']['yi'],facts['civil_hour']['ji']),(l.getTimeYi(),l.getTimeJi()))

    def test_no_point_total_overrides_a_block_or_unknown_activity(self):
        result=self.search(payload(start='2026-10-01',end='2026-10-31'))
        blocked=[w for d in result['days'] for w in d['windows'] if w['hard_exclusions'] and w['assessment_state']=='COMPLETE']
        self.assertTrue(blocked)
        self.assertTrue(all(w['grade']=='BAD' and w['score']==0 for w in blocked))
        for d in result['days']:
            for w in d['windows']:
                if w['grade']=='GOOD': self.assertEqual(w['day_activity_status'],'SUPPORTED')
                if w['score'] is not None:self.assertTrue(0<=w['score']<=100)

    def test_same_day_activity_and_natal_override_are_distinct(self):
        marriage=self.search(payload('MARRIAGE'))['days'][0]['windows'][0]
        opening=self.search(payload())['days'][0]['windows'][0]
        self.assertEqual(marriage['day_activity_status'],'SUPPORTED')
        self.assertEqual(opening['day_activity_status'],'AVOID')
        data=payload();data['subjects'][0]['birth']['override_dung_than']='Kim'
        result=self.search(data)
        self.assertEqual(result['subject_summaries'][0]['primary'],'Kim')
        profile=self.engine.profile(DateSearchRequest.model_validate(data).subjects[0])
        profile['ky']=('Kim',)
        facts=self.engine.calendar.at(datetime.fromisoformat('2026-10-12T22:00:00+07:00'))
        p=self.engine.personal(profile,facts)
        self.assertEqual(p['element_bands'][0],'PRIMARY')  # Canh/Metal wins its manual override

    def test_birth_uncertainty_checks_exact_jie_even_away_from_hour(self):
        data=payload();data['subjects'][0]['birth']={'civil_datetime':'1994-10-08T05:00:00+07:00','clock_uncertainty_seconds':0}
        p=self.engine.profile(DateSearchRequest.model_validate(data).subjects[0])
        self.assertEqual(p['birth_boundary'],'CLEAR_WITHIN_BOUND')
        data['subjects'][0]['birth']={'civil_datetime':'2026-10-08T13:29:17+07:00','clock_uncertainty_seconds':2}
        result=self.search(data)
        self.assertEqual(result['subject_summaries'][0]['birth_boundary'],'UNSTABLE')
        self.assertTrue(all(w['grade'] is None for w in result['days'][0]['windows']))

    def test_request_constraints_and_weekday_hour_clipping(self):
        for bad in [payload('MARRIAGE'),payload(start='2026-01-01',end='2026-04-04')]:
            if bad['activity']=='MARRIAGE':bad['subjects'].pop()
            with self.assertRaises(ValidationError):DateSearchRequest.model_validate(bad)
        data=payload();data['allowed_hours']={'start':'07:15:00','end':'09:45:00'}
        rows=self.search(data)['days'][0]['windows']
        self.assertEqual(rows[0]['start_at'],'2026-10-12T07:15:00+07:00')
        self.assertEqual(rows[-1]['end_at'],'2026-10-12T09:45:00+07:00')
        self.assertEqual(sum(w['duration_seconds'] for w in rows),9000)
        data['allowed_weekdays']=[6]
        self.assertEqual(self.search(data)['days'][0]['assessment_state'],'FILTERED')

    def test_api_contract_and_no_draw_storage_or_generator_calls(self):
        with tempfile.TemporaryDirectory() as tmp,TestClient(create_app(Path(tmp)/'draws.sqlite3')) as client:
            before=client.get('/api/v1/history').json()
            with patch.object(client.app.state.engine,'draw',side_effect=AssertionError('No draw allowed')):
                response=client.post('/api/v2/auspicious-dates/search',json=payload('MARRIAGE'))
            self.assertEqual(response.status_code,200,response.text)
            Draft202012Validator(json.loads((ROOT/'schemas/date_search_response.schema.json').read_text())).validate(response.json())
            self.assertEqual(before,client.get('/api/v1/history').json())
            bad=payload();bad['subjects']=[]
            self.assertEqual(client.post('/api/v2/auspicious-dates/search',json=bad).status_code,422)


if __name__=='__main__':unittest.main()
