"""Basic Na Jia chart; source rules are inspectable in config/coins_rules.json.

This builds a chart, not an automatic verdict or event-timing engine.
"""
from .maihoa import TRIGRAMS

STEMS = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
BRANCHES = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
BRANCHES_ZH = list('子丑寅卯辰巳午未申酉戌亥')
BRANCH_ELEMENTS = ['Thủy', 'Thổ', 'Mộc', 'Mộc', 'Thổ', 'Hỏa', 'Hỏa', 'Thổ', 'Kim', 'Kim', 'Thổ', 'Thủy']
GENERATES = {'Mộc': 'Hỏa', 'Hỏa': 'Thổ', 'Thổ': 'Kim', 'Kim': 'Thủy', 'Thủy': 'Mộc'}
CONTROLS = {'Mộc': 'Thổ', 'Thổ': 'Thủy', 'Thủy': 'Hỏa', 'Hỏa': 'Kim', 'Kim': 'Mộc'}


def relative(palace, line):
    if palace == line:
        return 'Huynh đệ'
    if GENERATES[line] == palace:
        return 'Phụ mẫu'
    if GENERATES[palace] == line:
        return 'Tử tôn'
    return 'Thê tài' if CONTROLS[palace] == line else 'Quan quỷ'


class NaJia:
    def __init__(self, config):
        self.config = config
        self.trigram_ids = {value[2]: key for key, value in TRIGRAMS.items()}
        self.palaces = {}
        for trigram, (_, element, half) in TRIGRAMS.items():
            bits = list(half + half)
            for stage, flips, world in zip(config['palace_stages'], [[], [0], [1], [2], [3], [4], [3], [0, 1, 2]], [6, 1, 2, 3, 4, 5, 4, 3]):
                for index in flips:
                    bits[index] ^= 1
                key = tuple(bits)
                if key in self.palaces:
                    raise RuntimeError('Duplicate Na Jia palace assignment')
                self.palaces[key] = (trigram, element, stage, world)
        if len(self.palaces) != 64:
            raise RuntimeError('Expected 64 Na Jia palace assignments')

    def assignments(self, bits):
        rows = []
        for start, side in ((0, 'lower'), (3, 'upper')):
            trigram = self.trigram_ids[tuple(bits[start:start+3])]
            entry = self.config['najia'][str(trigram)]
            stem = entry[side + '_stem']
            branches = entry['branches'][start:start+3]
            rows.extend((STEMS[stem], BRANCHES[z], BRANCHES_ZH[z], BRANCH_ELEMENTS[z], z) for z in branches)
        return rows

    def chart(self, bits, changed, moving, clock):
        trigram, element, stage, world = self.palaces[tuple(bits)]
        response = (world + 2) % 6 + 1
        day = clock['gans'][2]
        day_branch = clock['zhis'][2]
        start_branch = (day_branch - day) % 12
        void = [(start_branch + 10) % 12, (start_branch + 11) % 12]
        spirits = self.config['spirits']
        first_spirit = self.config['day_stem_spirit_start'][day]
        changed_rows = self.assignments(changed)
        rows = []
        for i, (stem, branch, zh, line_element, z) in enumerate(self.assignments(bits), 1):
            target = changed_rows[i-1] if i in moving else None
            rows.append({'position': i, 'stem': stem, 'branch': branch, 'branch_zh': zh, 'element': line_element,
                         'relative': relative(element, line_element), 'spirit': spirits[(first_spirit + i - 1) % 6],
                         'is_world': i == world, 'is_response': i == response, 'moving': i in moving,
                         'void': z in void, 'month_clash': z == (clock['zhis'][1] + 6) % 12,
                         'changed_stem': target[0] if target else None, 'changed_branch': target[1] if target else None,
                         'changed_element': target[3] if target else None,
                         'changed_relative': relative(element, target[3]) if target else None})
        return {'palace': TRIGRAMS[trigram][0], 'palace_element': element, 'stage': stage,
                'world_line': world, 'response_line': response, 'void_branches': [BRANCHES[z] for z in void],
                'lines_bottom_to_top': rows, 'scope': 'BASIC_NAJIA_CHART'}
