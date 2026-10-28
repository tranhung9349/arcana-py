"""Local Vietnamese phrase recognition. Suggestions never silently replace a topic.

This is deliberately bounded: token boundaries, common explicit negations and
clause-level actor context are handled; arbitrary Vietnamese semantics are not.
"""
from hashlib import sha256
import json
import re
import unicodedata

from .engine import ROOT
from .liuyao_models import QuestionIntent


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower().replace('đ', 'd'))
                   if unicodedata.category(c) != 'Mn')


class QuestionIntentRecognizer:
    def __init__(self, topics):
        self.topics = topics
        self.config = json.loads((ROOT / 'config/liuyao_intent_rules.json').read_text())
        self.patterns = [(rule, term, re.compile(r'(?<!\w)' + r'\s+'.join(re.escape(word) for word in normalize(term).split()) + r'(?!\w)'))
                         for rule in self.config['rules'] for term in rule['terms']]
        self.negation = re.compile(r'(?:khong\s+(?:hoi|ban|xet|quan tam|lien quan)|khong phai|dung\s+(?:xet|luan)|bo qua|ngoai tru)(?:\s+\w+){0,4}\s*$')

    def recognize(self, question, topic):
        # Keep negation within the current clause; a question-final "không" is not negation.
        original = unicodedata.normalize('NFC', question.lower())
        clauses = re.split(r'[,.;!?\n]+|\b(?:nhưng|mà|còn|hay|hoặc|và|nhung|hoac|va)\b|\bma\b(?!\s+toi\b)', original)
        matches = []
        for original_clause in clauses:
            clause, offsets = '', []
            for index, char in enumerate(original_clause):
                folded = normalize(char); clause += folded; offsets.extend([index] * len(folded))
            local = []
            for rule, term, pattern in self.patterns:
                for hit in pattern.finditer(clause):
                    surface = original_clause[offsets[hit.start()]:offsets[hit.end()-1]+1]
                    words = re.findall(r'\w+', surface)
                    # Retain supplied accents: "ưu tiên" is not "tiền", "bỏ" is not "bố".
                    if any(normalize(word) != word and word != expected for word, expected in zip(words, term.lower().split())):
                        continue
                    disposition = 'NEGATED' if self.negation.search(clause[:hit.start()]) else 'INTENT'
                    local.append({'rule_id':rule['id'], 'topic':rule['topic'], 'label':rule['label'],
                                  'term':term, 'disposition':disposition})
            positive = {row['topic'] for row in local if row['disposition'] == 'INTENT'}
            # "Tôi đòi tiền từ mẹ" mentions a person, but asks about a financial action.
            objective = positive & {'WEALTH', 'CAREER', 'DOCUMENT'}
            for row in local:
                if row['disposition'] == 'INTENT' and ((objective and row['topic'] in {'PARENTS','CHILDREN','SIBLINGS','PARTNERSHIP'}) or (len(positive) > 1 and row['topic'] == 'GENERAL')):
                    row['disposition'] = 'CONTEXT'
                if row not in matches:
                    matches.append(row)
        candidates = []
        specific_rules = {rule['id'] for rule in self.config['rules'] if rule['specific']}
        for key, definition in self.topics.items():
            relevant = [m for m in matches if m['topic'] == key and m['disposition'] == 'INTENT']
            if relevant:
                candidates.append({'topic':key,'label':definition['label'],'target':definition['target'],
                                   'intent_labels':list(dict.fromkeys(m['label'] for m in relevant)),
                                   'terms':list(dict.fromkeys(m['term'] for m in relevant)),
                                   'evidence_level':'SPECIFIC_PHRASE' if any(m['rule_id'] in specific_rules for m in relevant) else 'KEYWORD'})
        suggested = candidates[0]['topic'] if len(candidates) == 1 else None
        status = 'UNRECOGNIZED' if not candidates else 'MULTIPLE' if len(candidates) > 1 else 'MATCH' if suggested == topic else 'CONFLICT'
        label = self.topics[topic]['label']
        if status == 'MATCH':
            message = f'Câu hỏi có tín hiệu phù hợp với chủ đề {label}. Giữ chủ đề này để chọn Dụng thần.'
        elif status == 'CONFLICT':
            message = f"Câu hỏi gợi ý {candidates[0]['label']}, khác chủ đề {label} đang chọn. Chọn gợi ý hoặc xác nhận giữ chủ đề hiện tại."
        elif status == 'MULTIPLE':
            message = 'Câu hỏi có nhiều nhóm ý: ' + ', '.join(c['label'] for c in candidates) + '. Chọn một phạm vi chính để luận; có thể tách thành câu hỏi riêng.'
        else:
            message = f'Chưa nhận diện được nhóm ý rõ từ câu hỏi. Tiếp tục lấy chủ đề {label} bạn chọn làm gốc.'
        notes = list(self.config['notes'])
        if any(m['disposition'] == 'CONTEXT' and m['topic'] in ('PARENTS','CHILDREN','SIBLINGS') for m in matches):
            notes.append('Có nhắc người thân trong việc đang hỏi. Kiểm tra bạn muốn luận sự việc hay lấy chính người đó làm đối tượng; có thể chỉ định Lục thân khi cần.')
        return QuestionIntent.model_validate({'rules_version':self.config['version'],
            'question_sha256':sha256(question.strip().encode()).hexdigest(), 'selected_topic':topic,
            'status':status, 'suggested_topic':suggested, 'candidates':candidates,
            'matches':matches, 'needs_review':status in ('CONFLICT','MULTIPLE'), 'message':message, 'notes':notes}).model_dump(mode='json')
