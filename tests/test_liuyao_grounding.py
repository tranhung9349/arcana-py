"""The actual model request must carry the saved casting and matching source text."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from randomyst.ai_client import AIConfig, CompatibleAIClient
from randomyst.ai_context import liuyao_context
from randomyst.coins_models import CoinRequest
from randomyst.coins_service import CoinService
from randomyst.interpretation import ExplanationRepository
from randomyst.liuyao_analysis import LiuYaoInterpreter, digest
from randomyst.liuyao_models import AnalysisContext
from randomyst.liuyao_sources import casting_sources
from research_tools.interpretation_prompt import ROOT, build_messages, load_pack
from tests.test_coin_consultations import payload


class LiuYaoGroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coins = CoinService(ExplanationRepository())
        cls.interpreter = LiuYaoInterpreter(cls.coins.najia)

    def casting(self, totals=(7,8,9,8,7,6)):
        request = payload(totals)
        request['question'] = 'Tôi sẽ tiếp tục được công việc hiện tại trong tháng 12/2026 hay không và công việc của tôi sẽ kéo dài bao lâu nữa?'
        coin = self.coins.consult(CoinRequest.model_validate(request))
        analysis = self.interpreter.analyze(coin, AnalysisContext(topic='CAREER'))
        return coin, analysis

    def test_full_saved_casting_calendar_and_assessment_are_supplied_without_recasting(self):
        coin, analysis = self.casting()
        before = deepcopy((coin, analysis))
        with patch.object(self.coins, 'consult', side_effect=AssertionError('No recast')), \
             patch.object(self.interpreter, 'analyze', side_effect=AssertionError('No reanalysis')), \
             patch('randomyst.time_engine.pillars', side_effect=AssertionError('No calendar calculation')):
            ctx = liuyao_context(coin, analysis)
        facts = {f.id: json.loads(f.text) for f in ctx.facts if f.id in (
            'casting:throws','chart:original','chart:changed','chart:moving_lines','chart:najia',
            'calendar:casting','reading:provenance','sources:documents','sources:rule_bindings')}
        for key, value in [('casting:throws',coin['casting']), ('chart:original',coin['original']['chart']),
                           ('chart:changed',coin['changed']['chart']), ('chart:moving_lines',[3,6]),
                           ('chart:najia',coin['najia']), ('calendar:casting',coin['calendar'])]:
            self.assertEqual(facts[key], value)
        self.assertEqual(facts['reading:provenance']['casting_snapshot_sha256'], digest(coin))
        for line in analysis['lines']:
            self.assertEqual(json.loads(next(f.text for f in ctx.facts if f.id=='line:'+line['key'])), line)
        self.assertEqual((coin,analysis), before)
        for finding in ctx.findings:
            if finding.id == 'scope:time': continue
            self.assertIn('assessment:'+finding.id, finding.fact_refs)
        # Bibliography alone must not masquerade as a captured chapter.
        bindings = [r for row in facts['sources:rule_bindings'] for r in row['rules']]
        self.assertTrue(any(r['capture_state']=='BIBLIOGRAPHY_ONLY' and not r['primary_evidence_refs'] for r in bindings))
        self.assertTrue(any(r['rule_source_id']=='USE' and r['primary_evidence_refs']==['ly:use_target'] for r in bindings))

    def test_only_the_actual_hexagrams_and_exact_pinned_text_are_retrieved(self):
        coin, analysis = self.casting()
        ctx = liuyao_context(coin, analysis)
        evidence = {e.id:e for e in ctx.evidence}
        docs = json.loads(next(f.text for f in ctx.facts if f.id=='sources:documents'))
        self.assertEqual({d['hexagram_id'] for d in docs['hexagrams']}, {63,42})
        for role in ('original','changed'):
            reading = coin[role]
            for card in [*reading['text']['cards'], *reading['reference_lines']]:
                actual = evidence[card['evidence_id']]
                self.assertEqual((actual.text,actual.url,actual.kind), (card['text'],card['source']['url'],'PRIMARY_TEXT'))
                self.assertEqual(actual.sha256,sha256(card['text'].encode()).hexdigest())
        career = evidence['ly:use_target']
        self.assertIn('官鬼', career.text)
        self.assertIn('oldid=2100700', career.url)
        self.assertNotIn('ly:wealth', evidence)
        self.assertNotIn('ly:two_uses', evidence)  # Web-only excerpt is not pinned locally.
        for doc in docs['method']:
            self.assertRegex(doc['document_sha256'],r'^[0-9a-f]{64}$')
            self.assertGreater(doc['revision_id'],0)

    def test_static_and_all_moving_castings_keep_their_actual_shape(self):
        for totals, original, changed in [((7,)*6,1,None), ((8,)*6,2,None), ((9,)*6,1,2), ((6,)*6,2,1)]:
            with self.subTest(totals=totals):
                coin, analysis = self.casting(totals)
                ctx = liuyao_context(coin,analysis)
                facts = {f.id:f.text for f in ctx.facts}
                self.assertEqual(json.loads(facts['chart:original'])['hexagram_id'],original)
                self.assertEqual(json.loads(facts['chart:changed']),coin['changed']['chart'] if changed else None)
                docs = json.loads(facts['sources:documents'])['hexagrams']
                self.assertEqual({d['hexagram_id'] for d in docs},{original,changed} if changed else {original})
                self.assertEqual(any(d['position']==7 for d in docs),changed is not None)
                if changed:
                    self.assertEqual(next(d['role'] for d in docs if d['position']==7),'original')

    def test_unreviewed_ai_drafts_are_excluded_and_source_mismatch_is_rejected(self):
        coin, analysis = self.casting()
        coin['original']['text']['overview']['text']='UNREVIEWED_DRAFT_SENTINEL'
        coin['original']['text']['cards'][0]['translation']['text']='UNREVIEWED_TRANSLATION_SENTINEL'
        analysis['snapshot_sha256']=digest(coin)
        serialized=liuyao_context(coin,analysis).model_dump_json()
        self.assertNotIn('SENTINEL', serialized)
        for mutation in ('text','commit','hexagram_id'):
            altered=deepcopy(coin)
            if mutation=='text': altered['original']['reference_lines'][0]['text']+='篡改'
            elif mutation=='commit':
                source=altered['original']['reference_lines'][0]['source']
                source['commit']='0'*40
                source['url']=f"https://github.com/{source['repository']}/blob/{source['commit']}/{source['path']}"
            else: altered['original']['chart']['hexagram_id']=64
            # Keep translation model valid so the corpus check itself is exercised.
            card=altered['original']['reference_lines'][0]
            card['translation']['source_text_sha256']=sha256(card['text'].encode()).hexdigest()
            bound=deepcopy(analysis);bound['snapshot_sha256']=digest(altered)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError,'pinned'):
                if mutation=='hexagram_id':
                    casting_sources(altered)
                else:
                    liuyao_context(altered,bound)

    def test_dedicated_prompt_and_complete_context_reach_configured_http_request(self):
        coin, analysis = self.casting()
        ctx=liuyao_context(coin,analysis)
        prepared=build_messages(ctx,limit=2)
        opener=Mock()
        opener.open.return_value=BytesIO(json.dumps({'choices':[{'message':{'content':'{}'},'finish_reason':'stop'}]}).encode())
        client=CompatibleAIClient(AIConfig('https://example.test/v1','configured-model','test-key',10),opener)
        client.complete(prepared['messages'])
        request=opener.open.call_args.args[0]
        sent=json.loads(request.data)
        self.assertEqual(request.full_url,'https://example.test/v1/chat/completions')
        self.assertEqual(sent['model'],'configured-model')
        self.assertEqual(json.loads(sent['messages'][-1]['content']),ctx.model_dump(mode='json'))
        prompt=sent['messages'][0]['content']
        for expected in ('casting:throws','sources:rule_bindings','BIBLIOGRAPHY_ONLY','Không gieo lại','ba năm','chỉ bổ trợ'):
            self.assertIn(expected,prompt)
        self.assertNotIn('test-key',sent['messages'][-1]['content'])

    def test_dedicated_prompt_and_new_retrieval_inputs_are_manifest_bound(self):
        manifest,_,cases=load_pack()
        target=ROOT/manifest['method_system_prompts']['LIUYAO_NAJIA']
        instruction=target.read_text()
        for case in cases:
            self.assertEqual(instruction in build_messages(case['context'])['messages'][0]['content'],case['context']['method']=='LIUYAO_NAJIA')
        pinned={f['path'] for f in manifest['files']}
        self.assertTrue({'randomyst/liuyao_sources.py','randomyst/ai_context.py','data/reference/open-iching/iching.json'} <= pinned)
        read=Path.read_bytes
        with patch.object(Path,'read_bytes',lambda p:read(p)+(b'changed' if p==target else b'')):
            with self.assertRaisesRegex(ValueError,'Few-shot file changed'):
                build_messages(cases[0]['context'])


if __name__=='__main__':
    unittest.main()
