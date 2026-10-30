"""Whole-life coverage and engine-bound timing, rather than trait-only prose."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from randomyst.ai_context import natal_context
from randomyst.ai_service import AIReadingRequest
from randomyst.api import create_app
from randomyst.bazi_models import BaziRequest
from randomyst.bazi_pipeline import (StructuralAnalysis, LifeReading, prepare_analyst, life_outline,
    interpreter_messages, validate_analysis, validate_life_reading)
from randomyst.bazi_portrait import period_plan
from randomyst.bazi_service import BaziService
from research_tools.interpretation_prompt import Context
from tests.bazi_pipeline_fixtures import analysis_for, life_for, prose_for
from tests.browser_client import TestClient
from tests.test_ai_readings import CONFIG, FakeAI
from tests.test_bazi_consultations import payload


class WholeLifeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=BaziService().consult(BaziRequest.model_validate(payload()))
        cls.context=natal_context(cls.saved)

    def setUp(self):
        self.analysis=validate_analysis(analysis_for(self.context.model_dump(mode='json'),whole_life=True),self.context,require_portrait=True)
        self.reader=life_for(self.analysis.model_dump(mode='json'))

    def test_general_has_three_life_domains_and_engine_bound_periods_instead_of_trait_cards(self):
        prepared=prepare_analyst(self.context);user=json.loads(prepared['messages'][-1]['content'])
        self.assertEqual(user['reading_scope'],'WHOLE_LIFE')
        self.assertEqual(user['life_period_plan'],period_plan(self.context))
        cycles=self.saved['engine']['result']['luck_cycles']
        self.assertEqual(user['life_period_plan'][0]['start_year'],cycles[0]['start'])
        self.assertEqual(user['life_period_plan'][-1]['end_age'],cycles[6]['endAge'])
        self.assertIn('engine_interpretation',user['luck_cycles']['cycles'][0])
        self.assertIn('engine:natal_profile',user['reference_catalog']['fact_refs'])
        self.assertNotIn('civil_datetime',prepared['messages'][-1]['content'])
        outline=life_outline(self.analysis)
        self.assertEqual([row['area'] for row in outline['whole_life']['areas']],['CAREER','FINANCES','RELATIONSHIPS'])
        self.assertEqual(outline['tendencies'],[]);self.assertEqual(outline['in_life'],[])
        reader=validate_life_reading(self.reader,self.analysis)
        self.assertEqual(len(reader.whole_life.periods),3)
        writer=json.loads(interpreter_messages(self.analysis)[-1]['content'])
        self.assertEqual(writer['analysis_result']['whole_life'],self.analysis.whole_life.model_dump(mode='json'))
        self.assertNotIn('patterns',writer['analysis_result'])
        self.assertNotIn('technical_overview',writer['analysis_result'])
        self.assertNotIn('verified_context',writer)

    def test_whole_life_cannot_be_replaced_by_a_trait_only_analysis_or_duplicate_domains(self):
        with self.assertRaisesRegex(ValueError,'WHOLE_LIFE_PORTRAIT_REQUIRED'):
            validate_analysis(analysis_for(self.context.model_dump(mode='json')),self.context,require_portrait=True)
        raw=self.analysis.model_dump(mode='json');raw['whole_life']['areas'][2]['area']='CAREER'
        with self.assertRaisesRegex(ValueError,'AREA_COVERAGE'):
            validate_analysis(raw,self.context,require_portrait=True)

    def test_each_life_claim_needs_multiple_real_facts_and_a_known_source(self):
        for change in ('foreign_fact','single_fact','foreign_source'):
            raw=self.analysis.model_dump(mode='json');claim=raw['whole_life']['areas'][0]
            if change=='foreign_fact':claim['fact_refs'][0]='invented:fact'
            elif change=='single_fact':claim['fact_refs']=[claim['fact_refs'][0]]*2
            else:claim['evidence_refs']=['invented:book']
            with self.assertRaisesRegex(ValueError,'FOREIGN_OR_THIN'):
                validate_analysis(raw,self.context)

    def test_timing_cannot_invent_years_ages_cycle_indices_or_a_cycle_basis(self):
        for field,value in [('start_year',1900),('end_year',2200),('start_age',18),('end_age',95),('cycle_indices',[8,9])]:
            raw=self.analysis.model_dump(mode='json');raw['whole_life']['periods'][0][field]=value
            with self.assertRaisesRegex(ValueError,'PERIOD_NOT_IN_ENGINE'):
                validate_analysis(raw,self.context)
        raw=self.analysis.model_dump(mode='json');raw['whole_life']['periods'][0]['fact_refs']=raw['whole_life']['overview']['fact_refs']
        with self.assertRaisesRegex(ValueError,'WITHOUT_CYCLE_BASIS'):validate_analysis(raw,self.context)

    def test_reader_cannot_drop_domains_change_periods_or_add_unplanned_trait_sections(self):
        for change in ('drop_area','change_year','change_source','add_traits'):
            raw=deepcopy(self.reader)
            if change=='drop_area':raw['whole_life']['areas'].pop()
            elif change=='change_year':raw['whole_life']['periods'][0]['start_year']+=1
            elif change=='change_source':raw['whole_life']['areas'][0]['source_id']='L03'
            else:raw['contradictions']=[deepcopy(raw['overview'])]
            with self.assertRaises(ValueError):validate_life_reading(raw,self.analysis)

    def test_writer_produces_only_prose_and_server_binds_the_unchanged_periods_and_references(self):
        raw=prose_for(self.analysis.model_dump(mode='json'))
        value=validate_life_reading(raw,self.analysis,prose_only=True)
        self.assertEqual(value.whole_life.model_dump()['periods'][0]['start_year'],self.analysis.whole_life.periods[0].start_year)
        self.assertEqual(value.analysis_sha256,self.reader['analysis_sha256'])
        self.assertEqual(value.overview.pattern_refs,self.reader['overview']['pattern_refs'])
        with self.assertRaisesRegex(ValueError,'WHOLE_LIFE_PROSE_REQUIRED'):
            validate_life_reading(self.reader,self.analysis,prose_only=True)
        raw['periods'][0]['start_year']=1900
        with self.assertRaises(ValueError):validate_life_reading(raw,self.analysis,prose_only=True)
        raw=prose_for(self.analysis.model_dump(mode='json'));raw['areas'][1]['source_id']='L01'
        with self.assertRaisesRegex(ValueError,'COVERAGE_MISMATCH'):
            validate_life_reading(raw,self.analysis,prose_only=True)

    def test_private_timing_note_cannot_contaminate_public_prose_or_block_every_repair(self):
        self.analysis.whole_life.timing_note='V01: thân vượng, Dụng thần, Nhật chủ; P01.'
        value=validate_life_reading(prose_for(self.analysis.model_dump(mode='json')),self.analysis,prose_only=True)
        self.assertNotIn('V01',value.whole_life.timing_note)
        self.assertNotIn('thân vượng',value.whole_life.timing_note)

    def test_internal_notation_in_a_life_area_or_period_is_not_displayable(self):
        for section in ('areas','periods'):
            raw=deepcopy(self.reader);raw['whole_life'][section][0]['text']='V01: {"private":"data"}'
            with self.assertRaisesRegex(ValueError,'INTERNAL_NOTATION'):validate_life_reading(raw,self.analysis)

    def test_whole_life_does_not_hide_technical_metaphors_behind_a_two_term_allowance(self):
        raw=deepcopy(self.reader);raw['whole_life']['areas'][0]['text']='Thực Thần cần kênh xuất lực và thấu can.'
        with self.assertRaisesRegex(ValueError,'TOO_MUCH_JARGON') as error:validate_life_reading(raw,self.analysis)
        issue=next(i for i in error.exception.issues if i['type']=='LIFE_READING_TOO_MUCH_JARGON')
        self.assertEqual(issue['max_terms'],0)
        self.assertIn('kênh xuất lực',issue['terms'])

    def test_verified_structure_keeps_two_distinct_clash_locations_and_visible_wealth(self):
        saved=BaziService().consult(BaziRequest.model_validate(payload('1994-09-01T07:00:00+07:00')))
        context=natal_context(saved)
        analysis=validate_analysis(analysis_for(context.model_dump(mode='json'),whole_life=True),context)
        self.assertEqual([r['pillars'] for r in analysis.verified_structure['branch_clashes']],
                         [['pillar:year','pillar:hour'],['pillar:month','pillar:day']])
        self.assertEqual(analysis.verified_structure['visible_stems'][0]['ten_god'],'Thiên Tài')
        raw=analysis.model_dump(mode='json');raw['verified_structure']['branch_clashes'][0]['pillars']=['pillar:month','pillar:day']
        with self.assertRaisesRegex(ValueError,'STRUCTURE_FACTS_CHANGED'):validate_analysis(raw,context)

    def test_missing_luck_cycles_keeps_three_domains_but_does_not_fabricate_a_timeline(self):
        raw_context=self.context.model_dump(mode='json')
        raw_context['facts']=[f for f in raw_context['facts'] if f['id']!='engine:luck_cycles']
        context=Context.model_validate(raw_context)
        analysis=validate_analysis(analysis_for(raw_context,whole_life=True),context,require_portrait=True)
        reader=validate_life_reading(life_for(analysis.model_dump(mode='json')),analysis)
        self.assertEqual(reader.whole_life.timing_status,'NOT_AVAILABLE')
        self.assertEqual(reader.whole_life.periods,[]);self.assertEqual(len(reader.whole_life.areas),3)

    def test_focused_readings_keep_their_topic_specific_plan(self):
        raw=self.context.model_dump(mode='json');raw['topic']='STUDY';context=Context.model_validate(raw)
        prepared=prepare_analyst(context)
        self.assertEqual(prepared['reading_scope'],'FOCUSED')
        analysis=validate_analysis(analysis_for(raw),context)
        self.assertEqual(len(life_outline(analysis)['tendencies']),3)
        self.assertIsNone(validate_life_reading(life_for(analysis.model_dump(mode='json')),analysis).whole_life)

    def test_streamed_general_reading_publishes_whole_life_and_keeps_intermediate_private(self):
        fake=FakeAI();app=create_app(ai_config=CONFIG,ai_client=fake)
        with TestClient(app) as client:
            saved=client.post('/api/v1/bazi/consultations',json=payload()).json()
            request={'method':'BAZI','consultation_id':saved['request_id']}
            enriched=client.enrich(request)
            response=client.post('/api/v1/ai/readings/start',json=enriched)
            self.assertEqual(response.status_code,200);self.assertIn('event: result',response.text)
            self.assertNotIn('"bazi_analysis"',response.text)
            result=app.state.ai.lookup(AIReadingRequest.model_validate(enriched))
            self.assertEqual(len(result['reading']['whole_life']['areas']),3)
            self.assertEqual(result['reading']['tendencies'],[])
            self.assertEqual(fake.calls,2)

    def test_validation_diagnostics_do_not_log_exception_text(self):
        app=create_app(ai_config=CONFIG,ai_client=FakeAI())
        with TestClient(app) as client:
            saved=client.post('/api/v1/bazi/consultations',json=payload()).json()
            request=client.enrich({'method':'BAZI','consultation_id':saved['request_id']})
            with patch('randomyst.ai_service.validate_life_reading',side_effect=ValueError('private-birth-key-sentinel')):
                with self.assertLogs('arcana.ai',level='WARNING') as log:
                    response=client.post('/api/v1/ai/readings',json=request)
            self.assertEqual(response.status_code,502)
            self.assertNotIn('private-birth-key-sentinel',' '.join(log.output))
            self.assertNotIn('private-birth-key-sentinel',response.text)


if __name__=='__main__':unittest.main()
