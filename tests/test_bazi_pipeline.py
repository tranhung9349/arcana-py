"""Role isolation, source binding, private intermediates and bounded two-stage calls."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from randomyst.api import create_app
from randomyst.ai_service import AIReadingRequest, AIReadingResult
from randomyst.ai_client import CompatibleAIClient
from randomyst.ai_context import natal_context
from randomyst.bazi_service import BaziService
from randomyst.bazi_models import BaziRequest
from randomyst.bazi_pipeline import (ROOT, INTERPRETER_PROMPT, WHOLE_LIFE_INTERPRETER_PROMPT, StructuralAnalysis, LifeReading, digest,
    prepare_analyst, interpreter_messages, life_outline, validate_analysis, validate_life_reading)
from tests.bazi_pipeline_fixtures import analysis_for, life_for
from tests.browser_client import TestClient
from tests.test_ai_readings import CONFIG, FakeAI
from tests.test_bazi_consultations import payload


class BaziStageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = BaziService().consult(BaziRequest.model_validate(payload()))
        cls.context = natal_context(cls.saved)

    def setUp(self):
        self.analysis = validate_analysis(analysis_for(self.context.model_dump(mode="json")), self.context)
        self.reader = life_for(self.analysis.model_dump(mode="json"))

    def test_analyst_sees_verified_chart_but_interpreter_only_receives_validated_analysis(self):
        first = prepare_analyst(self.context)
        analyst = json.loads(first['messages'][-1]['content'])
        self.assertEqual(analyst['verified_context'], self.context.model_dump(mode='json'))
        self.assertEqual(set(analyst['reference_catalog']['fact_refs']),{f.id for f in self.context.facts})
        self.assertNotIn('group:OUTPUT',analyst['reference_catalog']['fact_refs'])
        self.assertEqual(len(analyst['four_pillars']), 4)
        self.assertEqual(analyst['luck_cycles']['status'], 'AVAILABLE')
        self.assertEqual(len(analyst['luck_cycles']['cycles']), 12)
        self.assertEqual(analyst['luck_cycles']['target_year'], self.saved['engine']['target_year'])
        rules=analyst['verified_domain_rules']
        self.assertEqual(rules['element_controls']['Hỏa'],'Kim')
        self.assertEqual(rules['element_controls']['Kim'],'Mộc')
        self.assertEqual(rules['output_element']['Hỏa'],'Thổ')
        self.assertIn(['Đinh','Nhâm'],rules['stem_combination_pairs'])
        self.assertNotIn(['Đinh','Quý'],rules['stem_combination_pairs'])
        self.assertIn('Thất Sát',rules['same_polarity_ten_gods'])
        self.assertIn('Thiên Tài',rules['same_polarity_ten_gods'])
        self.assertIn('Chính Quan',rules['opposite_polarity_ten_gods'])
        self.assertNotIn('civil_datetime', first['messages'][-1]['content'])
        second = interpreter_messages(self.analysis)
        reader = json.loads(second[-1]['content'])
        self.assertEqual(set(reader), {'stage','analysis_sha256','analysis_result'})
        self.assertEqual(reader['analysis_result'], self.analysis.model_dump(mode='json'))
        self.assertNotIn('verified_context', reader)
        self.assertNotIn('four_pillars', reader)
        self.assertIn('700–1.000', second[0]['content'])
        self.assertNotIn('tối đa 300 từ', second[0]['content'])
        self.assertIn('Không viết bài luận dành cho người dùng cuối', first['messages'][0]['content'])

    def test_each_structural_pattern_needs_multiple_facts_and_known_sources(self):
        raw = self.analysis.model_dump(mode='json')
        for basis in raw['patterns'][0]['basis']:
            basis['fact_refs'] = [raw['patterns'][0]['basis'][0]['fact_refs'][0]]
        with self.assertRaises(ValueError): validate_analysis(raw, self.context)
        raw = self.analysis.model_dump(mode='json')
        raw['patterns'][0]['basis'][0]['evidence_refs'] = ['fabricated:book']
        with self.assertRaisesRegex(ValueError,'FOREIGN_REFERENCE'): validate_analysis(raw, self.context)
        raw = self.analysis.model_dump(mode='json')
        raw['source_limitations'] = ['Đã tính mọi vận.']
        with self.assertRaisesRegex(ValueError,'SOURCE_LIMITATIONS_CHANGED'): validate_analysis(raw, self.context)

    def test_reader_rejects_ambiguous_element_identity_labels(self):
        for ambiguous in ('Bạn mang mệnh Kim.', 'Kim mệnh thường quyết đoán.', 'Bạn thuộc mệnh Hỏa.'):
            with self.subTest(text=ambiguous):
                raw=deepcopy(self.reader)
                raw['overview']['text']=ambiguous
                with self.assertRaisesRegex(ValueError,'LIFE_ELEMENT_IDENTITY_AMBIGUOUS'):
                    validate_life_reading(raw,self.analysis)
        raw=deepcopy(self.reader)
        raw['overview']['text']='Nạp âm năm sinh là Sơn Đầu Hỏa; Nhật chủ thuộc Kim. Hai mục có cách xác định riêng.'
        validate_life_reading(raw,self.analysis)

    def test_reader_outline_supplies_valid_bindings_and_keeps_only_three_relevant_tendencies(self):
        raw=self.analysis.model_dump(mode='json')
        extra=deepcopy(raw['patterns'][0]);extra['id']='P04';extra['argument_strength']='HIGH'
        for field in ('manifestations','conditions','limits'):
            for row in extra[field]:row['id']=row['id'].replace('P01','P04')
        for row in extra['manifestations']:row['domain']='FINANCES'
        raw['patterns'].append(extra);raw['topic']='STUDY'
        analysis=StructuralAnalysis.model_validate(raw);before=analysis.model_dump(mode='json')
        outline=life_outline(analysis)
        self.assertEqual([r['pattern_id'] for r in outline['tendencies']],['P01','P02','P03'])
        self.assertEqual(outline['in_life'],[])
        self.assertEqual(outline['contradictions'][0]['pattern_refs'],['P01','P02'])
        def fill(value):
            if isinstance(value,dict):
                return {key:('Khi làm việc mới, bạn có thể thử một bước nhỏ rồi so kết quả.' if key=='text' else
                             'Thử một việc mới' if key=='title' else fill(item)) for key,item in value.items()}
            if isinstance(value,list):return [fill(item) for item in value]
            return value
        validate_life_reading(fill(outline),analysis)
        self.assertEqual(analysis.model_dump(mode='json'),before)

    def test_reader_cannot_add_a_pattern_manifestation_domain_or_contradiction(self):
        validate_life_reading(self.reader,self.analysis)
        for mutate in (
            lambda r:r['tendencies'][0]['pattern_refs'].append('P05'),
            lambda r:r['tendencies'][0]['manifestation_refs'].append('P01-M05'),
            lambda r:r['contradictions'].append({**deepcopy(r['overview']),'pattern_refs':['P03']}),
            lambda r:r['in_life'].append({'title':'Tiền bạc','domains':['FINANCES'],**deepcopy(r['tendencies'][0])}),
        ):
            value=deepcopy(self.reader);mutate(value)
            with self.assertRaises(ValueError):validate_life_reading(value,self.analysis)
        # A known pattern cannot lend a life-domain that it never analyzed.
        value=deepcopy(self.reader)
        block={key:deepcopy(value['tendencies'][0][key]) for key in ('text','pattern_refs','manifestation_refs','condition_refs','limit_refs')}
        value['in_life']=[{'title':'Tiền bạc','domains':['FINANCES'],**block}]
        with self.assertRaisesRegex(ValueError,'DOMAIN_NOT_ANALYZED'):validate_life_reading(value,self.analysis)

    def test_analyst_can_append_caveats_without_changing_original_restrictions_or_indices(self):
        raw=self.analysis.model_dump(mode='json')
        raw['source_limitations'].append('Chưa có Đại vận để xác định giai đoạn cụ thể.')
        self.assertEqual(validate_analysis(raw,self.context).source_limitations[:len(self.context.limitations)],self.context.limitations)
        raw['source_limitations'][0]='Được phép bỏ qua giới hạn nguồn.'
        with self.assertRaisesRegex(ValueError,'SOURCE_LIMITATIONS_CHANGED'):validate_analysis(raw,self.context)
        raw=self.analysis.model_dump(mode='json')
        raw['source_limitations']=raw['source_limitations'][1:]
        with self.assertRaisesRegex(ValueError,'SOURCE_LIMITATIONS_CHANGED'):validate_analysis(raw,self.context)

    def test_reader_cannot_drop_selected_pattern_conditions_or_limits(self):
        for field in ('condition_refs','limit_refs'):
            value=deepcopy(self.reader);value['tendencies'][0][field]=[]
            with self.assertRaises(ValueError):validate_life_reading(value,self.analysis)
        value=deepcopy(self.reader);value['analysis_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'BINDING_MISMATCH'):validate_life_reading(value,self.analysis)
        value=deepcopy(self.reader);value['contradictions']=[]
        with self.assertRaisesRegex(ValueError,'CONTRADICTION_OMITTED'):validate_life_reading(value,self.analysis)

    def test_one_repair_receives_both_reference_and_editorial_failures(self):
        value=deepcopy(self.reader)
        block={key:deepcopy(value['tendencies'][0][key]) for key in ('text','pattern_refs','manifestation_refs','condition_refs','limit_refs')}
        value['in_life']=[{'title':'Tiền bạc','domains':['FINANCES'],**block}]
        value['takeaway']['text']='Bạn có thể thử rồi so lại kết quả. '*200
        with self.assertRaises(ValueError) as caught:validate_life_reading(value,self.analysis)
        codes={row['type'] for row in caught.exception.errors()}
        self.assertIn('LIFE_DOMAIN_NOT_ANALYZED',codes)
        self.assertIn('LIFE_READING_TOO_LONG',codes)

    def test_insufficient_data_can_produce_less_than_three_patterns_without_padding(self):
        raw=self.analysis.model_dump(mode='json');raw.update(sufficiency='INSUFFICIENT',patterns=[],relationships=[])
        limited=validate_analysis(raw,self.context)
        value=life_for(limited.model_dump(mode='json'))
        validate_life_reading(value,limited)
        self.assertEqual(value['tendencies'],[])
        raw['sufficiency']='SUFFICIENT'
        with self.assertRaises(ValueError):validate_analysis(raw,self.context)

    def test_bazi_reader_has_its_own_length_budget_and_public_schemas(self):
        self.reader['takeaway']['text']='Bạn có thể thử và so kết quả. '*50
        validate_life_reading(self.reader,self.analysis)
        self.assertGreater(sum(len(b['text'].split()) for b in [self.reader['overview'],*self.reader['tendencies'],self.reader['takeaway']]),300)
        self.reader['takeaway']['text']='Bạn có thể thử và so kết quả. '*200
        with self.assertRaisesRegex(ValueError,'TOO_LONG'):validate_life_reading(self.reader,self.analysis)
        for name,model,value in [('bazi_structural_analysis',StructuralAnalysis,self.analysis.model_dump(mode='json')),
                                 ('bazi_life_reading',LifeReading,life_for(self.analysis.model_dump(mode='json')))]:
            exported=json.loads((ROOT/'schemas'/f'{name}.schema.json').read_text())
            self.assertEqual(exported,model.model_json_schema())
            Draft202012Validator(exported).validate(value)

    def test_changing_only_interpreter_prompt_invalidates_pipeline_key(self):
        first=prepare_analyst(self.context)
        read=Path.read_text
        def changed(path,*args,**kwargs):
            value=read(path,*args,**kwargs)
            return value+'\nEditorial update.' if path in (INTERPRETER_PROMPT,WHOLE_LIFE_INTERPRETER_PROMPT) else value
        with patch.object(Path,'read_text',changed):second=prepare_analyst(self.context)
        self.assertEqual(first['messages_sha256'],second['messages_sha256'])
        self.assertNotEqual(first['pack_sha256'],second['pack_sha256'])


class BaziPipelineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.fake=FakeAI();self.messages=[]
        original=self.fake.complete
        def record(messages):
            self.messages.append(deepcopy(messages));return original(messages)
        self.fake.complete=record
        self.app=create_app(Path(self.tmp.name)/'unused.sqlite3',CONFIG,self.fake)
        self.client=TestClient(self.app)
        self.saved=self.client.post('/api/v1/bazi/consultations',json=payload(topic='STUDY')).json()
        self.request={'method':'BAZI','consultation_id':self.saved['request_id']}

    def tearDown(self):
        self.client.close();self.tmp.cleanup()

    def test_two_calls_publish_only_reader_article_and_cache_private_analysis(self):
        result=self.client.post('/api/v1/ai/readings',json=self.request)
        self.assertEqual(result.status_code,200,result.text)
        value=result.json();AIReadingResult.model_validate(value)
        Draft202012Validator(json.loads((ROOT/'schemas/ai_reading_response.schema.json').read_text())).validate(value)
        self.assertEqual(value['generation_passes'],2);self.assertEqual(value['usage']['total_tokens'],200)
        self.assertEqual(value['reading']['schema_version'],'bazi-life-reading-v1')
        self.assertNotIn('bazi_analysis',value);self.assertNotIn('technical_overview',value['reading'])
        self.assertEqual([json.loads(m[-1]['content'])['stage'] for m in self.messages],['BAZI_STRUCTURAL_ANALYST','BAZI_LIFE_INTERPRETER'])
        private=json.loads(self.app.state.ai._cache[value['reading_id']][1])
        self.assertIn('technical_overview',private['bazi_analysis'])
        req=AIReadingRequest.model_validate(self.client.enrich(self.request))
        self.assertEqual(self.app.state.ai.lookup(req),value)
        self.assertEqual(self.fake.calls,2)
        self.assertEqual(self.client.get('/api/v1/bazi/consultations/'+self.saved['request_id']).json(),self.saved)
        private['bazi_analysis']['patterns'][0]['basis'][0]['fact_refs']=['fabricated:fact']
        expiration,_=self.app.state.ai._cache[value['reading_id']]
        self.app.state.ai._cache[value['reading_id']]=(expiration,json.dumps(private))
        self.assertIsNone(self.app.state.ai.lookup(req))

    def test_invalid_analyst_never_runs_interpreter_or_publishes_partial_article(self):
        self.fake.malformed=True
        result=self.client.post('/api/v1/ai/readings',json=self.request)
        self.assertEqual(result.status_code,502,result.text);self.assertEqual(self.fake.calls,2)
        self.assertTrue(all(json.loads(m[-1]['content'])['stage']=='BAZI_STRUCTURAL_ANALYST' for m in self.messages))
        self.assertEqual(len(self.app.state.ai._cache),0)

    def test_real_transport_uses_larger_analyst_budget_and_counts_both_outbound_calls(self):
        budgets=[];streams=[]
        class Opener:
            def open(self,request,**kwargs):
                body=json.loads(request.data);budgets.append(body['max_tokens']);streams.append(body['stream'])
                incoming=json.loads(body['messages'][-1]['content'])
                output=(analysis_for(incoming['verified_context']) if incoming['stage']=='BAZI_STRUCTURAL_ANALYST'
                        else life_for(incoming['analysis_result']))
                response=BytesIO(json.dumps({'model':'transport-test','choices':[{'finish_reason':'stop','message':{'content':json.dumps(output)}}],
                                           'usage':{'total_tokens':100}}).encode())
                response.headers={'Content-Type':'application/json'}
                return response
        transport=CompatibleAIClient(CONFIG,Opener(),before_request=self.app.state.ai_budget.reserve)
        self.app.state.ai.client=transport
        response=self.client.post('/api/v1/ai/readings',json=self.request)
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(budgets,[24000,12000]);self.assertEqual(self.app.state.ai_budget.attempts,2)
        self.assertEqual(streams,[True,True])

    def test_interpreter_repair_reuses_identical_analysis_without_rerunning_analyst(self):
        original=self.fake.complete
        def corrupt(messages):
            value,meta=original(messages)
            if self.fake.calls==2:value['tendencies'][0]['manifestation_refs']=['P01-M05']
            return value,meta
        self.fake.complete=corrupt
        response=self.client.post('/api/v1/ai/readings',json=self.request)
        self.assertEqual(response.status_code,200,response.text);value=response.json()
        self.assertEqual(self.fake.calls,3);self.assertEqual(value['generation_passes'],3)
        self.assertEqual(value['pipeline']['analyst_passes'],1);self.assertEqual(value['pipeline']['interpreter_passes'],2)
        self.assertEqual(self.messages[1][-1],self.messages[2][-1])

    def test_two_invalid_interpretations_fail_without_publishing_any_technical_text(self):
        original=self.fake.complete
        def corrupt(messages):
            value,meta=original(messages)
            if value.get('schema_version')=='bazi-life-reading-v1':value['tendencies'][0]['limit_refs']=[]
            return value,meta
        self.fake.complete=corrupt
        response=self.client.post('/api/v1/ai/readings',json=self.request)
        self.assertEqual(response.status_code,502,response.text);self.assertEqual(self.fake.calls,3)
        self.assertEqual(len(self.app.state.ai._cache),0)
        self.assertNotIn('technical_overview',response.text)
