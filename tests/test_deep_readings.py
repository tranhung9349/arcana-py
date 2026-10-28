from copy import deepcopy
from itertools import product
import json
from pathlib import Path
from random import Random
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from jsonschema import Draft202012Validator

from randomyst.bazi import analyze
from randomyst.bazi_reading import REASONS
from randomyst.engine import NumberEngine
from randomyst.interpretation import ExplanationRepository
from randomyst.maihoa import TRIGRAMS
from randomyst.models import DrawRequest, SourceExplanation
from randomyst.sampling import state_of
from randomyst.time_engine import STEMS, STEMS_ZH, BRANCHES, BRANCHES_ZH

ROOT=Path(__file__).resolve().parents[1]


class DeepReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=NumberEngine()
        cls.repository=ExplanationRepository(cls.engine.iching)
        request=DrawRequest.model_validate(json.loads((ROOT/'examples/draw_request.json').read_text()))
        cls.draw=cls.engine.draw(request,rng=Random(1102))

    def test_v2_requires_two_bound_modules_and_retains_v1_compatibility(self):
        result=self.repository.explain(self.draw)
        self.assertEqual(result['schema_version'],'source-explanation-v2')
        SourceExplanation.model_validate(result)
        for slot,kind in [('bazi','BAZI'),('maihoa','MAIHOA')]:
            reading=result['readings'][slot]
            self.assertEqual(reading['module'],kind)
            self.assertGreaterEqual(len(reading['sections']),5)
            ids={row['evidence_id'] for row in reading['evidence']}
            self.assertTrue(all(set(row['references'])<=ids for row in reading['sections']))
        changed=deepcopy(result);changed['readings']=None
        with self.assertRaises(ValidationError):SourceExplanation.model_validate(changed)
        changed=deepcopy(result);changed['readings']['bazi']['sections'][0]['references']=['missing']
        with self.assertRaises(ValidationError):SourceExplanation.model_validate(changed)
        changed=deepcopy(result);changed['readings']['maihoa']['evidence'][0]['url']='javascript:alert(1)'
        with self.assertRaises(ValidationError):SourceExplanation.model_validate(changed)
        archived=deepcopy(result)
        archived['schema_version']='source-explanation-v1'
        archived.pop('readings')
        SourceExplanation.model_validate(archived)
        schema=json.loads((ROOT/'schemas/source_explanation.schema.json').read_text())
        validator=Draft202012Validator(schema)
        validator.validate(result);validator.validate(archived)

    def test_reading_never_recasts_recalculates_calendar_or_mutates_snapshot(self):
        before=deepcopy(self.draw)
        with (patch.object(self.engine,'draw',side_effect=AssertionError('No draw')),
             patch.object(self.repository.iching,'calculate',side_effect=AssertionError('No new chart')),
             patch.object(self.repository.iching,'calculate_source',side_effect=AssertionError('No new source chart')),
             patch('randomyst.maihoa_service.resolve_maihoa',side_effect=AssertionError('No new calendar')),
             patch('randomyst.maihoa_service.solar_month',side_effect=AssertionError('No new month'))):
            result=self.repository.explain(self.draw)
        self.assertEqual(self.draw,before)
        self.assertFalse(result['model_called'])
        result['readings']['maihoa']['facts']['chart']['original']['lines_bottom_to_top'][0]^=1
        self.assertEqual(self.draw,before)

    def test_casting_season_changes_only_maihoa_reading_not_birth_reading(self):
        before=self.repository.explain(self.draw)['readings']
        changed=deepcopy(self.draw)
        changed['trace']['casting_solar_month'].update(month_branch_index=2,month_branch='Dần')
        after=self.repository.explain(changed)['readings']
        self.assertEqual(before['bazi'],after['bazi'])
        self.assertNotEqual(before['maihoa']['facts']['season'],after['maihoa']['facts']['season'])
        self.assertEqual(after['bazi']['facts']['birth_month_branch'],self.draw['trace']['bazi']['natal']['pillars'][1]['branch'])

    def test_override_and_unknown_structure_do_not_rewrite_natal_interpretation(self):
        changed=deepcopy(self.draw)
        changed['trace']['bazi'].update(primary_used='Kim',overridden=True,structure='Sát Cách')
        reading=self.repository.explain(changed)['readings']['bazi']
        self.assertEqual(reading['facts']['primary_used'],'Kim')
        self.assertEqual(reading['facts']['primary_calculated'],self.draw['trace']['bazi']['primary_dung_than'])
        self.assertTrue(any('chưa có mục khớp chính xác' in section['text'] for section in reading['sections']))
        self.assertTrue(any('bạn chọn Kim' in section['text'] for section in reading['sections']))

    def test_all_64_hexagrams_and_six_moving_positions_use_saved_geometry(self):
        for upper,lower,moving in product(range(1,9),range(1,9),range(1,7)):
            with self.subTest(upper=upper,lower=lower,moving=moving):
                bits=TRIGRAMS[lower][2]+TRIGRAMS[upper][2]
                changed_bits=list(bits);changed_bits[moving-1]^=1
                body,use=(upper,lower) if moving<=3 else (lower,upper)
                def trigram(number):
                    name,element,_=TRIGRAMS[number]
                    return {'trigram':number,'name':name,'element':element}
                saved=deepcopy(self.draw)
                core=saved['trace']['maihoa']
                core.update(upper=upper,lower=lower,moving_line=moving,original=self.repository.iching.metadata(bits),
                            the=trigram(body),dung=trigram(use),state=state_of(TRIGRAMS[body][1],TRIGRAMS[use][1]))
                core['display_hexagrams'].update(mutual=self.repository.iching.metadata(bits[1:4]+bits[2:5]),
                                                 changed=self.repository.iching.metadata(changed_bits))
                reading=self.repository.explain(saved)['readings']['maihoa']
                chart=reading['facts']['chart']
                self.assertEqual(chart['original'],core['original'])
                self.assertEqual(chart['changed'],core['display_hexagrams']['changed'])
                self.assertEqual(chart['the']['trigram'],body)
                self.assertEqual(len(reading['facts']['findings']),4)

    def test_pure_legacy_mutual_and_archived_calendar_are_not_upgraded(self):
        saved=deepcopy(self.draw)
        core=self.repository.iching.calculate({'Y':1,'M':1,'D':6,'H':8})
        source=self.repository.iching.calculate_source(core['variables'])
        self.assertNotEqual(source['display_hexagrams']['mutual'],core['display_hexagrams']['mutual'])
        saved['trace']['maihoa']=core
        reading=self.repository.explain(saved)['readings']['maihoa']
        self.assertEqual(reading['facts']['chart']['mutual'],core['display_hexagrams']['mutual'])
        self.assertEqual(reading['facts']['chart']['mutual_basis'],'ORIGINAL')
        archived=json.loads((ROOT/'docs/archive/draw_response_v3.json').read_text())
        old=self.repository.explain(archived)['readings']['maihoa']
        self.assertEqual(old['facts']['season']['provider'],archived['trace']['casting_solar_month']['provider'])

    def test_missing_auxiliary_chart_is_disclosed_and_inconsistent_chart_rejected(self):
        saved=deepcopy(self.draw)
        saved['trace']['maihoa']['display_hexagrams'].update(mutual=None,changed=None)
        reading=self.repository.explain(saved)['readings']['maihoa']
        self.assertEqual(len(reading['facts']['findings']),1)
        self.assertEqual(len(reading['facts']['missing_phases']),2)
        saved=deepcopy(self.draw)
        saved['trace']['maihoa']['the']['element']='Mộc'
        with self.assertRaises(ValueError):self.repository.explain(saved)
        saved=deepcopy(self.draw)
        saved['trace']['maihoa']['display_hexagrams']['mutual']['lines_bottom_to_top'][0]^=1
        with self.assertRaises(ValueError):self.repository.explain(saved)

    def test_all_reachable_bazi_branches_have_a_specific_reading(self):
        rng=Random(38);seen=set()
        for _ in range(15000):
            gans=[rng.randrange(10) for _ in range(4)]
            zhis=[rng.randrange(12) for _ in range(4)]
            numeric=analyze(gans,zhis)
            code=numeric['reason_code']
            if code in seen:continue
            seen.add(code)
            saved=deepcopy(self.draw)
            saved['trace']['bazi'].update(numeric,primary_used=numeric['primary_dung_than'],overridden=False)
            natal=saved['trace']['bazi']['natal']
            natal.update(gans=gans,zhis=zhis)
            for row,gan,zhi in zip(natal['pillars'],gans,zhis):
                row.update(stem=STEMS[gan],stem_zh=STEMS_ZH[gan],branch=BRANCHES[zhi],branch_zh=BRANCHES_ZH[zhi])
            reading=self.repository.explain(saved)['readings']['bazi']
            self.assertEqual(reading['facts']['reason_code'],code)
            self.assertIn(REASONS[code][0],[section['title'] for section in reading['sections']])
            if seen==set(REASONS):break
        self.assertEqual(seen,set(REASONS))
