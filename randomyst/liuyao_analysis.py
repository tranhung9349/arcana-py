"""Conditional Na Jia interpretation, with source-linked facts rather than a luck score.

The classical rules are not a predictive model. Selection priorities and synthesis
are explicit product policies; unresolved interactions stay visible in the result.
"""
from hashlib import sha256
import json
from pathlib import Path

from .engine import EngineError, ROOT
from .liuyao import BRANCHES, BRANCH_ELEMENTS, CONTROLS, GENERATES, relative
from .liuyao_models import AnalysisContext, LiuYaoAnalysis
from .liuyao_intent import QuestionIntentRecognizer
from .maihoa import TRIGRAMS

RELATION_LABELS = {
    'SAME': 'đồng hành', 'GENERATES': 'sinh hào', 'CONTROLS': 'khắc hào',
    'DRAINS': 'hào sinh ra ngoài · tiết khí', 'CONSUMES': 'hào khắc ra ngoài · hao khí',
}
SEASONS = {'SAME': 'Vượng', 'GENERATES': 'Tướng', 'CONTROLS': 'Tử', 'DRAINS': 'Hưu', 'CONSUMES': 'Tù'}
TRANSFORM_LABELS = {
    'RETURN_GENERATES': 'Hồi đầu sinh', 'RETURN_CONTROLS': 'Hồi đầu khắc',
    'RETURN_SAME': 'Hóa đồng hành', 'RETURN_DRAINS': 'Hóa tiết khí', 'RETURN_CONSUMES': 'Hóa hao khí',
    'ADVANCE': 'Hóa tiến', 'RETREAT': 'Hóa thoái', 'REPEAT': 'Phục ngâm tại hào',
    'RETURN_CLASH': 'Phản ngâm tại hào', 'RETURN_COMBINE': 'Hóa hợp',
    'CHANGED_VOID': 'Hóa Không', 'CHANGED_MONTH_CLASH': 'Hóa Nguyệt Phá',
}
SUPPORT_RELATIONS = {'SAME', 'GENERATES'}


def element_relation(source, target):
    """Direction is always source -> target, including a changed line -> its origin."""
    if source == target:
        return 'SAME'
    if GENERATES[source] == target:
        return 'GENERATES'
    if CONTROLS[source] == target:
        return 'CONTROLS'
    return 'DRAINS' if GENERATES[target] == source else 'CONSUMES'


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def line_label(key):
    return ('Phục thần dưới hào ' if key.startswith('H') else 'hào ') + key[1:]


def calendar_phrase(label, branch, source_element, target_element, relation):
    source = f'{label} {branch} {source_element}'
    if relation == 'SAME':
        return source + f' đồng hành với hào {target_element}'
    if relation in ('GENERATES', 'CONTROLS'):
        return source + (' sinh' if relation == 'GENERATES' else ' khắc') + f' hào {target_element}'
    return (source + f': hào {target_element} ' + ('sinh ra ngoài nên tiết khí' if relation == 'DRAINS' else 'khắc ra ngoài nên hao khí'))


class LiuYaoInterpreter:
    def __init__(self, najia):
        self.najia = najia
        raw = (ROOT / 'config/liuyao_analysis_rules.json').read_bytes()
        self.config = json.loads(raw)
        # Cache identity includes executable rules and the chart/calendar dependencies.
        dependencies = [Path(__file__), ROOT / 'randomyst/liuyao_models.py', ROOT / 'randomyst/liuyao.py',
                        ROOT / 'randomyst/time_engine.py', ROOT / 'config/coins_rules.json',
                        ROOT / 'randomyst/liuyao_intent.py', ROOT / 'config/liuyao_intent_rules.json']
        self.rules_sha256 = sha256(raw + b''.join(path.read_bytes() for path in dependencies)).hexdigest()
        self.combines = {frozenset(pair) for pair in self.config['combines']}
        self.advances = {tuple(pair) for pair in self.config['advances']}
        self.intent = QuestionIntentRecognizer(self.config['topics'])

    def rules(self):
        return {'version': self.config['version'], 'rules_sha256': self.rules_sha256,
                'topics': self.config['topics'], 'sources': self.config['sources'], 'limitations': self.config['limits'],
                'intent_rules_version': self.intent.config['version'], 'intent_notes': self.intent.config['notes']}

    def combines_with(self, a, b):
        return frozenset((a, b)) in self.combines

    def line_state(self, row, clock, void_branches, hidden=False):
        z = BRANCHES.index(row['branch'])
        month, day = clock['zhis'][1:3]
        mr = element_relation(BRANCH_ELEMENTS[month], row['element'])
        dr = element_relation(BRANCH_ELEMENTS[day], row['element'])
        month_clash, day_clash = z == (month + 6) % 12, z == (day + 6) % 12
        month_good = mr in SUPPORT_RELATIONS and not month_clash
        day_good = dr in SUPPORT_RELATIONS
        flags, caveats, transformation = [], [], []
        for flag, condition in [('VOID', row['branch'] in void_branches), ('MONTH_CLASH', month_clash),
                                ('DAY_CLASH', day_clash), ('MONTH_COMBINE', self.combines_with(z, month)),
                                ('DAY_COMBINE', self.combines_with(z, day)), ('MONTH_VALUE', z == month), ('DAY_VALUE', z == day)]:
            if condition:
                flags.append(flag)
        if row['moving']:
            activity = 'MOVING'
        elif day_clash and month_good and not hidden:
            activity = 'DARK_ACTIVE'
        elif day_clash and not hidden:
            activity = 'DAY_CLASH_WEAK'
        else:
            activity = 'STATIC'
        calendar_state = 'SUPPORTED' if month_good and day_good else 'MIXED' if month_good or day_good else 'WEAK'
        if month_clash:
            calendar_state = 'MIXED' if day_good else 'WEAK'
        if dr == 'CONTROLS' and month_good:
            calendar_state = 'MIXED'
        if row['moving'] and row.get('changed_branch'):
            changed_z = BRANCHES.index(row['changed_branch'])
            transformation.append('RETURN_' + element_relation(row['changed_element'], row['element']))
            if (z, changed_z) in self.advances:
                transformation.append('ADVANCE')
            if (changed_z, z) in self.advances:
                transformation.append('RETREAT')
            if z == changed_z:
                transformation.append('REPEAT')
            if changed_z == (z + 6) % 12:
                transformation.append('RETURN_CLASH')
            if self.combines_with(z, changed_z):
                transformation.append('RETURN_COMBINE')
            if row['changed_branch'] in void_branches:
                transformation.append('CHANGED_VOID')
            if changed_z == (month + 6) % 12:
                transformation.append('CHANGED_MONTH_CLASH')
        if 'VOID' in flags:
            caveats.append('Đang trong Tuần Không: cần xét xuất Không hoặc điền thực; không tự loại bỏ hào.')
        if 'MONTH_CLASH' in flags:
            caveats.append('Nguyệt Phá: tác dụng cần đối chiếu ngày sinh trợ, trực chi, hợp và khi đổi tháng.')
        if activity == 'DAY_CLASH_WEAK':
            caveats.append('Tĩnh gặp Nhật xung khi chưa được tháng sinh phù: nghiêng về Nhật phá, chưa đủ căn cứ gọi ám động.')
        if activity == 'DARK_ACTIVE':
            caveats.append('Tĩnh được tháng sinh phù gặp Nhật xung: xét ám động sơ bộ, không lật hào hay tạo quẻ biến mới.')
        if row['moving'] and 'DAY_COMBINE' in flags:
            caveats.append('Động gặp Nhật hợp: có điều kiện hợp trói cần xét; không đồng nghĩa hợp là tốt ngay.')
        if hidden:
            caveats.append('Phục thần chưa hiện: còn phụ thuộc Phi thần và điều kiện xuất lộ.')
        if any(t in transformation for t in ('CHANGED_VOID', 'CHANGED_MONTH_CLASH')):
            caveats.append('Hào biến gặp Không/Phá: tác dụng của biến hào có điều kiện thời gian, không xóa hồi đầu sinh/khắc.')
        calendar_summary = (calendar_phrase('Tháng', BRANCHES[month], BRANCH_ELEMENTS[month], row['element'], mr) + '; ' +
                            calendar_phrase('ngày', BRANCHES[day], BRANCH_ELEMENTS[day], row['element'], dr) + '.')
        return {'key': ('H' if hidden else 'L') + str(row['position']), 'position': row['position'],
                'visibility': 'HIDDEN' if hidden else 'VISIBLE', 'branch': row['branch'], 'element': row['element'],
                'relative': row['relative'], 'month_relation': mr, 'day_relation': dr,
                'seasonal_state': SEASONS[mr], 'calendar_state': calendar_state, 'calendar_summary': calendar_summary,
                'activity': activity, 'flags': flags, 'transformation': transformation, 'caveats': caveats}

    def hidden_rows(self, chart, target):
        trigram = next(value for value in TRIGRAMS.values() if value[0] == chart['palace'])
        return [{'position': i, 'stem': row[0], 'branch': row[1], 'element': row[3],
                 'relative': relative(chart['palace_element'], row[3]), 'moving': False}
                for i, row in enumerate(self.najia.assignments(trigram[2] * 2), 1)
                if relative(chart['palace_element'], row[3]) == target]

    def selection(self, chart, states, hidden, context):
        topic = self.config['topics'][context.topic]
        target = context.use_relative or topic['target']
        if target in ('WORLD', 'RESPONSE'):
            position = chart['world_line'] if target == 'WORLD' else chart['response_line']
            candidates = [row for row in states if row['position'] == position]
            label = 'Thế' if target == 'WORLD' else 'Ứng'
            reason = f"Chủ đề {topic['label']} lấy hào {label} làm trọng tâm."
        else:
            candidates = [row for row in states if row['relative'] == target] or hidden
            reason = f"{'Lựa chọn Lục thân của bạn' if context.use_relative else 'Chủ đề ' + topic['label']} lấy {target} làm Dụng thần."
        if not candidates:
            raise RuntimeError('Every palace must supply all five relatives')
        chosen, status = None, 'SELECTED'
        if context.focus_line is not None:
            chosen = next((r for r in candidates if r['position'] == context.focus_line), None)
            if chosen is None:
                raise EngineError('INVALID_USE_LINE', 'Hào chọn không thuộc nhóm Dụng thần của chủ đề này. Chọn một hào trong danh sách ứng viên.', 422)
            reason += f" Bạn chỉ định hào {context.focus_line}; các ứng viên còn lại vẫn được giữ để đối chiếu."
        elif len(candidates) == 1:
            chosen = candidates[0]
            reason += ' Chỉ có một hào phù hợp.'
        else:
            # Inspectable product priority, never a claim of a universal classical rule.
            for preferred, description in [([r for r in candidates if r['visibility'] == 'VISIBLE' and r['position'] == chart['world_line']], 'trì Thế'),
                                            ([r for r in candidates if r['activity'] == 'MOVING'], 'minh động'),
                                            ([r for r in candidates if 'DAY_VALUE' in r['flags'] or 'MONTH_VALUE' in r['flags']], 'trực Nhật/Nguyệt')]:
                if len(preferred) == 1:
                    chosen, status = preferred[0], 'PROVISIONAL'
                    reason += f" Tạm ưu tiên hào {chosen['position']} vì {description}; đây là ưu tiên của module, có thể chọn lại theo việc hỏi."
                    break
            if chosen is None:
                status = 'AMBIGUOUS'
                reason += ' Có nhiều hào phù hợp và chưa có ưu tiên rõ; cần chọn hào theo đối tượng thực tế trước khi chốt xu hướng.'
        if candidates[0]['visibility'] == 'HIDDEN':
            reason += ' Quẻ chủ thiếu Lục thân này; tra Phục thần từ quẻ thuần của bản cung, không thay hào hiện bằng hào biến.'
        return target, candidates, chosen, status, reason

    def analyze(self, session, context: AnalysisContext):
        intent = self.intent.recognize(session['question'], context.topic) if context.intent_mode == 'COMBINED' else None
        if intent and intent['needs_review'] and not context.intent_acknowledged:
            raise EngineError('INTENT_REVIEW_REQUIRED', intent['message'], 422)
        chart, clock = session['najia'], session['calendar']
        rows = chart['lines_bottom_to_top']
        states = [self.line_state(row, clock, chart['void_branches']) for row in rows]
        topic = self.config['topics'][context.topic]
        target = context.use_relative or topic['target']
        hidden_rows = self.hidden_rows(chart, target) if target not in ('WORLD', 'RESPONSE') and not any(r['relative'] == target for r in rows) else []
        hidden = [self.line_state(row, clock, chart['void_branches'], True) for row in hidden_rows]
        target, candidates, chosen, selection_status, reason = self.selection(chart, states, hidden, context)
        all_states = states + hidden
        raw_by_key = {**{'L' + str(row['position']): row for row in rows},
                      **{'H' + str(row['position']): row for row in hidden_rows}}
        findings, timing = [], []

        def finding(rule, effect, title, explanation, evidence, source_ids):
            findings.append({'id': f'F{len(findings)+1:03}', 'rule': rule, 'effect': effect,
                             'title': title, 'explanation': explanation, 'evidence': evidence, 'source_ids': source_ids})

        finding('USE_SELECTION', 'CONDITION' if selection_status != 'SELECTED' else 'CONTEXT', 'Chọn Dụng thần', reason,
                [f"{r['key']}: {r['relative']} {r['branch']} {r['element']}" for r in candidates], ['USE', 'MULTIPLE'])
        representatives = []
        if hidden:
            for label, z in [('Nguyệt', clock['zhis'][1]), ('Nhật', clock['zhis'][2])]:
                if relative(chart['palace_element'], BRANCH_ELEMENTS[z]) == target:
                    representatives.append(f'{label} {BRANCHES[z]} · {target}')
            for state in hidden:
                fly = rows[state['position']-1]
                rel = element_relation(fly['element'], state['element'])
                finding('FLY_HIDDEN', 'CONDITION', f"Phục thần hào {state['position']}",
                        f"{state['relative']} {state['branch']} phục dưới {fly['relative']} {fly['branch']}; Phi thần {RELATION_LABELS[rel]}. "
                        'Chưa hiện không đồng nghĩa không có tác dụng; cần kiểm tra sinh phù và lúc xuất lộ.',
                        [f"{state['key']} dưới L{state['position']}", f"Phi→Phục: {rel}"], ['HIDDEN'])
            if representatives:
                finding('CALENDAR_USE', 'CONTEXT', 'Nhật/Nguyệt cũng mang Lục thân cần tìm',
                        'Có thể tham chiếu Nhật/Nguyệt làm đại diện Dụng thần theo Tăng San; module vẫn trình bày Phục thần để giữ rõ vị trí trong quẻ.',
                        representatives, ['HIDDEN'])

        evaluated = [chosen] if chosen else candidates
        focus_findings = [f for f in findings if f['rule'] in ('FLY_HIDDEN', 'CALENDAR_USE')]
        roles = []
        for focus in evaluated:
            key = focus['key']; start = len(findings)
            label = f"{'Phục ' if focus['visibility'] == 'HIDDEN' else ''}hào {focus['position']} · {focus['relative']} {focus['branch']}"
            finding('CALENDAR_STRENGTH', 'SUPPORT' if focus['calendar_state'] == 'SUPPORTED' else 'OBSTACLE' if focus['calendar_state'] == 'WEAK' else 'CONDITION',
                    label + ' · Nhật–Nguyệt', focus['calendar_summary'] +
                    f" Khí mùa: {focus['seasonal_state']}; đây là nền sơ bộ, còn phải đối chiếu động biến và các quan hệ khác.",
                    [key, 'calendar.month_branch', 'calendar.day_branch'], ['SEASON', 'MONTH', 'DAY'])
            for flag, rule, title, explanation in [
                ('VOID', 'VOID', 'Dụng thần gặp Tuần Không', 'Không là điều kiện chưa thực trong tuần đang xét. Được sinh phù hoặc đang động vẫn phải giữ để luận; chưa đủ căn cứ kết luận việc thất bại.'),
                ('MONTH_CLASH', 'MONTH_CLASH', 'Dụng thần gặp Nguyệt Phá', 'Tháng xung chi hào; trước mắt có trở ngại về thời. Xem thêm Nhật sinh/trực chi, hợp và khi đổi tháng, không coi hào bị xóa.'),
                ('DAY_COMBINE', 'DAY_COMBINE', 'Dụng thần gặp Nhật hợp', 'Hào động gặp Nhật hợp có thể bị trói; hào tĩnh gặp hợp có mặt sinh khởi. Cần đối chiếu sinh khắc, không dùng chữ hợp để chốt tốt.'),
            ]:
                if flag in focus['flags']:
                    finding(rule, 'CONDITION', title, explanation, [key, flag], ['VOID'] if rule == 'VOID' else ['MONTH'] if rule == 'MONTH_CLASH' else ['COMBINE'])
            if focus['activity'] in ('DARK_ACTIVE', 'DAY_CLASH_WEAK'):
                explanation = ('Tĩnh được tháng sinh phù gặp Nhật xung: xét ám động sơ bộ; không lật hào hoặc tạo quẻ biến mới.'
                               if focus['activity'] == 'DARK_ACTIVE' else
                               'Tĩnh gặp Nhật xung khi chưa được tháng sinh phù: nghiêng về Nhật phá; cần kiểm tra thêm cứu giải.')
                finding('DAY_ACTIVATION', 'CONDITION', 'Nhật xung hào tĩnh', explanation,
                        [key, focus['activity']], ['DAY'])
            original_row = raw_by_key[key]
            if focus['transformation']:
                labels = [TRANSFORM_LABELS[t] for t in focus['transformation']]
                if 'RETURN_CONTROLS' in focus['transformation'] or 'RETREAT' in focus['transformation']:
                    effect = 'OBSTACLE'
                elif 'RETURN_GENERATES' in focus['transformation'] or 'ADVANCE' in focus['transformation']:
                    effect = 'SUPPORT'
                else:
                    effect = 'CONDITION'
                finding('FOCUS_TRANSFORM', effect, label + ' · động biến',
                        f"{original_row['branch']} {original_row['element']} → {original_row['changed_branch']} {original_row['changed_element']}: {', '.join(labels)}. "
                        'Hồi đầu xét biến hào tác động về chính hào gốc; không cho biến hào sinh khắc chéo mọi hào trong quẻ.',
                        [key, f"changed.L{focus['position']}", *focus['transformation']], ['TRANSFORM', 'ADVANCE'])
                if any(t in focus['transformation'] for t in ('CHANGED_VOID', 'CHANGED_MONTH_CLASH')):
                    finding('TRANSFORM_TIME_CONDITION', 'CONDITION', 'Động biến còn điều kiện Không/Phá',
                            'Hào biến rơi Không/Phá nên chưa chốt tác dụng hồi đầu ngay; hóa tiến/thoái vẫn được ghi nhận, cần chờ điều kiện phù hợp.',
                            [key, *focus['transformation']], ['ADVANCE', 'VOID'])
            role_elements = {'Dụng thần': focus['element'],
                             'Nguyên thần': next(e for e in GENERATES if GENERATES[e] == focus['element']),
                             'Kỵ thần': next(e for e in CONTROLS if CONTROLS[e] == focus['element'])}
            role_elements['Cừu thần'] = next(e for e in CONTROLS if CONTROLS[e] == role_elements['Nguyên thần'])
            if chosen:
                roles = [{'role': role, 'element': element, 'line_keys': [r['key'] for r in states if r['element'] == element],
                          'active_line_keys': [r['key'] for r in states if r['element'] == element and r['activity'] in ('MOVING', 'DARK_ACTIVE')]}
                         for role, element in role_elements.items()]
            for source in states:
                if source['key'] == key:
                    continue
                rel = element_relation(source['element'], focus['element'])
                active = source['activity'] in ('MOVING', 'DARK_ACTIVE')
                # Static interactions matter in an entirely still chart, subject to strength.
                strong_static = not any(r['activity'] in ('MOVING', 'DARK_ACTIVE') for r in states) and source['calendar_state'] == 'SUPPORTED'
                role = next((name for name, element in role_elements.items() if source['element'] == element), 'Tiết thần')
                role_label = 'Đồng hành với Dụng' if role == 'Dụng thần' else role
                if not active and not strong_static:
                    continue
                if rel not in ('SAME', 'GENERATES', 'CONTROLS') and role != 'Cừu thần':
                    continue
                action = 'minh động' if source['activity'] == 'MOVING' else 'ám động sơ bộ' if active else 'tĩnh được Nhật–Nguyệt sinh phù trong quẻ tĩnh'
                effect = 'SUPPORT' if rel in SUPPORT_RELATIONS else 'OBSTACLE' if rel == 'CONTROLS' else 'CONDITION'
                conditions = list(source['caveats'])
                sz, fz = BRANCHES.index(source['branch']), BRANCHES.index(focus['branch'])
                if self.combines_with(sz, fz):
                    conditions.append('Hai chi thuộc cặp lục hợp; tác dụng còn phải đối chiếu động/tĩnh và hợp trói, không tự hóa hành.')
                if sz == (fz+6) % 12:
                    conditions.append('Hai chi còn lục xung; phải xét cả xung và sinh khắc, không dùng một quan hệ để xóa quan hệ còn lại.')
                if source['calendar_state'] == 'WEAK':
                    conditions.append('Nguồn hào đang yếu theo Nhật–Nguyệt; chưa coi quan hệ này đã phát huy trọn vẹn.')
                for t in ('RETURN_CONTROLS', 'RETREAT'):
                    if t in source['transformation']:
                        conditions.append('Nguồn hào có ' + TRANSFORM_LABELS[t].lower() + ', tác dụng cần xét lại.')
                if conditions:
                    effect = 'CONDITION'
                wording = f"Hào {source['position']} {source['relative']} {source['branch']} ({role_label}) {action}, {RELATION_LABELS[rel]} đối với {line_label(key)}."
                if role == 'Cừu thần':
                    wording = f"Hào {source['position']} {source['branch']} là Cừu thần: có quan hệ khắc Nguyên thần, sinh Kỵ thần; cần xét chuỗi tác động thay vì coi là khắc Dụng trực tiếp."
                finding('LINE_INTERACTION', effect, f"Hào {source['position']} → {line_label(key)} · {role_label}", wording + (' ' + ' '.join(conditions) if conditions else ''),
                        [source['key'], key, f"{source['element']}→{focus['element']}: {rel}", *source['transformation']], ['ROLES', 'MOTION'])
            # A simultaneously active original/Ky chain changes the meaning of direct control.
            active_elements = {r['element'] for r in states if r['activity'] in ('MOVING', 'DARK_ACTIVE')}
            if role_elements['Nguyên thần'] in active_elements and role_elements['Kỵ thần'] in active_elements:
                finding('GENERATION_CHAIN', 'CONDITION', 'Nguyên thần và Kỵ thần cùng hoạt động',
                        'Kỵ thần có thể sinh Nguyên thần rồi Nguyên thần sinh Dụng (tham sinh quên khắc). Module giữ cả hai chiều sinh/khắc, chưa tự triệt tiêu Kỵ khi chưa giải toàn cục.',
                        [key, f"{role_elements['Kỵ thần']}→{role_elements['Nguyên thần']}→{focus['element']}"], ['ROLES'])
            z = BRANCHES.index(focus['branch'])
            if 'VOID' in focus['flags']:
                timing.append({'line_key': key, 'kind': 'FILL_VOID', 'branches': [focus['branch']],
                               'explanation': 'Đối chiếu lúc xuất tuần hoặc ngày trực chi để xét điền thực; đây là điều kiện cần xét, chưa bảo đảm việc thành.'})
            if 'MONTH_CLASH' in focus['flags']:
                timing.append({'line_key': key, 'kind': 'REPAIR_MONTH_CLASH', 'branches': [focus['branch'], BRANCHES[next(iter(next(p for p in self.combines if z in p) - {z}))]],
                               'explanation': 'Đối chiếu trực chi, hợp chi hoặc khi qua tháng đang xung; chưa ấn định một ngày ứng nghiệm.'})
            if 'DAY_COMBINE' in focus['flags'] and focus['activity'] == 'MOVING':
                timing.append({'line_key': key, 'kind': 'RELEASE_COMBINE', 'branches': [BRANCHES[(z+6) % 12]],
                               'explanation': 'Chi xung hào là một điều kiện xem xét giải hợp trói; phải kiểm tra thêm sinh khắc.'})
            if hidden:
                timing.append({'line_key': key, 'kind': 'REVEAL_HIDDEN', 'branches': [focus['branch']],
                               'explanation': 'Theo dõi điều kiện xuất lộ và Phi thần; trực chi đơn lẻ chưa đủ bảo đảm Phục thần hữu dụng.'})
            focus_findings.extend(findings[start:])

        world, response = states[chart['world_line']-1], states[chart['response_line']-1]
        wr = element_relation(response['element'], world['element'])
        wz, rz = BRANCHES.index(world['branch']), BRANCHES.index(response['branch'])
        branch_note = ' Chi Thế–Ứng xung nhau.' if wz == (rz+6) % 12 else (' Chi Thế–Ứng thuộc cặp lục hợp; còn xét động/tĩnh.' if self.combines_with(wz, rz) else '')
        finding('WORLD_RESPONSE', 'CONTEXT', 'Mình và bên đối diện · Thế–Ứng',
                f"Thế hào {world['position']} {world['branch']} {world['element']}; Ứng hào {response['position']} {response['branch']} {response['element']}. "
                f"Xét chiều Ứng → Thế: {RELATION_LABELS[wr]}." + branch_note + ' Đây là quan hệ cấu trúc, không khẳng định ý định hay hành vi của người kia.',
                [world['key'], response['key'], wr], ['COMBINE', 'ROLES'])
        if chosen and chosen['key'] != world['key']:
            relation_to_world = element_relation(chosen['element'], world['element'])
            relation_from_world = element_relation(world['element'], chosen['element'])
            extra = ('Trong câu hỏi tài, Tài khắc Thế còn có cách luận tài đến tìm mình; phải xem Thế có sức nhận hay không, không tự coi chữ khắc là bất lợi.'
                     if target == 'Thê tài' and relation_to_world == 'CONTROLS' else
                     'Đây là chiều quan hệ giữa đối tượng và người hỏi; tác dụng còn phụ thuộc sức hào và điều kiện động biến.')
            finding('USE_WORLD', 'CONTEXT', 'Đối tượng đang hỏi liên hệ với mình thế nào',
                    f"Dụng ở {line_label(chosen['key'])} {chosen['element']} → Thế hào {world['position']} {world['element']}: {RELATION_LABELS[relation_to_world]}. "
                    f"Chiều Thế → Dụng: {RELATION_LABELS[relation_from_world]}. " + extra,
                    [chosen['key'], world['key'], relation_to_world, world['calendar_summary']], ['USE', 'MONTH'])
            world_constraints = [*world['caveats']]
            if world['calendar_state'] == 'WEAK':
                world_constraints.append('Thế chưa được Nhật–Nguyệt sinh phù theo nền sơ bộ.')
            world_transform = [TRANSFORM_LABELS[t] for t in world['transformation'] if t in ('RETURN_CONTROLS', 'RETREAT', 'CHANGED_VOID', 'CHANGED_MONTH_CLASH')]
            if world_transform:
                world_constraints.append('Động biến của Thế: ' + ', '.join(world_transform) + '.')
            if world_constraints:
                finding('WORLD_CAPACITY', 'CONDITION', 'Sức tiếp nhận của người hỏi · hào Thế',
                        f"Thế hào {world['position']} {world['branch']} {world['element']}: " + world['calendar_summary'] + ' ' +
                        ' '.join(world_constraints) + ' Dụng có nền hỗ trợ vẫn cần kiểm tra điều kiện của Thế trước khi kết luận thuận lợi cho mình.',
                        [world['key'], *world['flags'], *world['transformation']], ['MONTH', 'DAY'])
                focus_findings.append(findings[-1])
        emerging = [r['position'] for r in rows if r['moving'] and r.get('changed_relative') == target] if target not in ('WORLD', 'RESPONSE') else []
        if emerging:
            finding('EMERGING_USE', 'CONDITION', 'Lục thân cần tìm xuất hiện ở hào biến',
                    'Giữ đây là dấu biến chuyển để đối chiếu; hào biến chỉ hồi đầu về hào gốc, không thay thế mọi ứng viên của quẻ chủ.',
                    [f'changed.L{i}' for i in emerging], ['TRANSFORM', 'HIDDEN'])
        support = [f for f in focus_findings if f['effect'] == 'SUPPORT']
        obstacles = [f for f in focus_findings if f['effect'] == 'OBSTACLE']
        conditions = [f for f in focus_findings if f['effect'] == 'CONDITION']
        if not chosen:
            tendency, headline = 'UNRESOLVED', 'Cần xác định hào Dụng thần trước khi chốt xu hướng'
        elif obstacles and not support:
            tendency, headline = 'OBSTACLES', 'Dụng thần đang gặp trở lực cần tháo gỡ'
        elif support and not obstacles and not hidden and not any(f['rule'] in ('GENERATION_CHAIN', 'TRANSFORM_TIME_CONDITION', 'WORLD_CAPACITY') for f in conditions):
            tendency, headline = 'SUPPORT_WITH_CONDITIONS', 'Có nền hỗ trợ, cần kiểm tra điều kiện phát huy'
        else:
            tendency, headline = 'MIXED', 'Có cả điều kiện hỗ trợ và điểm cần chờ hoặc làm rõ'
        meaning = 'Lục thân do bạn chỉ định' if context.use_relative else topic['meaning']
        narrative = [f"Với câu hỏi “{session['question']}”, khung {topic['label'].lower()} tập trung vào {meaning}. " + reason]
        if intent:
            recognized = next((c for c in intent['candidates'] if c['topic'] == context.topic), None)
            if recognized:
                narrative.append('Ý được nhận diện trong phạm vi bạn chọn: ' + '; '.join(recognized['intent_labels']) +
                                 '. Tín hiệu: ' + ', '.join('“' + term + '”' for term in recognized['terms']) + '.')
            elif intent['needs_review']:
                narrative.append('Câu hỏi và chủ đề có điểm cần làm rõ; bạn đã xác nhận giữ phạm vi ' + topic['label'] + '. Module giữ chủ đề này, không tự đổi Dụng thần.')
            else:
                narrative.append(intent['message'])
        if chosen:
            narrative.append(f"Trọng tâm là {'Phục thần ' if hidden else ''}hào {chosen['position']}, {chosen['relative']} {chosen['branch']} {chosen['element']}. " + chosen['calendar_summary'])
        else:
            narrative.append('Các ứng viên được luận song song ở dưới. Khi chọn một hào, app chỉ phân tích lại đúng quẻ đã lưu, không gieo lại đồng tiền.')
        for items, lead in [(support, 'Điểm nâng đỡ: '), (obstacles, 'Điểm cản trở: '), (conditions, 'Điều kiện cần giữ trong kết luận: ')]:
            if items:
                narrative.append(lead + ' '.join(f['explanation'] for f in items[:2]))
        narrative.append('Kết luận này mô tả thế sinh khắc theo phạm vi quy tắc hiện có; cần kiểm tra các điều kiện trên trước khi suy ra hành động, chưa khẳng định thành bại của sự việc.')
        practical_questions = [topic['advice']]
        if intent:
            applicable = {m['rule_id'] for m in intent['matches'] if m['topic'] == context.topic and m['disposition'] == 'INTENT'}
            practical_questions.extend(rule['advice'] for rule in self.intent.config['rules'] if rule['id'] in applicable and rule.get('advice'))
        practical_questions.append('Yếu tố nào trong phần điều kiện đã có bằng chứng thực tế, yếu tố nào vẫn chưa rõ?')
        return LiuYaoAnalysis.model_validate({
            'schema_version': 'liuyao-analysis-v1', 'session_id': session['request_id'],
            'rules_version': self.config['version'], 'rules_sha256': self.rules_sha256, 'snapshot_sha256': digest(session),
            'context': context.model_dump(), 'intent': intent, 'topic_label': topic['label'], 'method': 'DETERMINISTIC_RULES',
            'selection': {'target': target, 'reason': reason, 'status': selection_status, 'selected_key': chosen['key'] if chosen else None,
                          'candidate_keys': [r['key'] for r in candidates], 'hidden': bool(hidden),
                          'calendar_representatives': representatives, 'emerging_lines': emerging},
            'tendency': tendency, 'headline': headline, 'narrative': narrative,
            'practical_questions': practical_questions,
            'lines': all_states, 'roles': roles, 'findings': findings, 'timing_conditions': timing,
            'limitations': self.config['limits'], 'sources': self.config['sources'],
        }).model_dump(mode='json')
