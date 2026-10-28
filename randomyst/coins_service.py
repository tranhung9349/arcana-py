"""Three-coin casting, basic Na Jia and durable consultation snapshots."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import secrets

from .coins_models import CoinReading, CoinRequest, CoinResponse
from .engine import EngineError, ROOT
from .liuyao import NaJia
from .maihoa import TRIGRAMS
from .time_engine import pillars

READING_GUIDE = [
    'Đọc quẻ chủ để nắm nghĩa chung; các hào động được giữ đầy đủ theo đúng sáu lượt gieo. Quẻ biến lật đồng thời tất cả hào động.',
    'Quẻ từ và hào từ là phần đọc kinh văn. Bàn Lục Hào bên dưới lập Nạp Giáp, cung, Thế–Ứng, Lục thân, Lục thú, Tuần Không và Nguyệt Phá để đối chiếu.',
    'Lục thân của hào biến được tính theo ngũ hành cung của quẻ chủ. Dấu Không/Phá chỉ ghi quan hệ lịch; không tự kết luận hào vô dụng hoặc cát hung.',
    'Bản ghi gieo giữ kinh văn và bàn Nạp Giáp. Module luận theo chủ đề được lưu riêng theo phiên và phiên bản quy tắc, có thể luận lại mà không gieo lại.',
]
LIMITATIONS = [
    'Nghĩa Việt và diễn giải là bản nháp AI chưa hiệu đính. Phiên này đọc corpus cục bộ, không gọi mô hình AI.',
    'Không áp quy tắc chọn một hào theo số hào động của trường phái đọc Chu Dịch vào phép Nạp Giáp; hiển thị đủ 0–6 hào động.',
    'Phần kinh văn không thay cho lời luận Lục Hào theo chủ đề. Xem phạm vi và các điều kiện chưa giải trong bản phân tích riêng.',
    'Trường hợp Càn/Khôn cả sáu hào động: nguồn có Dụng Cửu/Dụng Lục được hiển thị nguyên văn Hán riêng; corpus chưa có bản nghĩa Việt tương ứng.',
]


def cast_bits(totals):
    bits = tuple(v % 2 for v in totals)
    moving = [i for i, v in enumerate(totals, 1) if v in (6, 9)]
    changed = tuple(bit ^ (i in moving) for i, bit in enumerate(bits, 1))
    return bits, moving, changed


class CoinService:
    def __init__(self, explanations):
        self.explanations = explanations
        self.iching = explanations.iching
        path = ROOT / 'config/coins_rules.json'
        raw = path.read_bytes()
        self.config = json.loads(raw)
        self.rules_sha256 = sha256(raw).hexdigest()
        self.najia = NaJia(self.config)

    def chart(self, number):
        row = self.explanations.by_id[number]
        bits = row['array']
        names = {v[2]: v[0] for v in TRIGRAMS.values()}
        return {**self.iching.metadata(bits), 'name_vi': self.explanations.vi[number]['name_vi'],
                'lower_trigram': names[tuple(bits[:3])], 'upper_trigram': names[tuple(bits[3:])]}

    def catalog(self):
        return {'rules_version': self.config['rules_version'], 'method': self.config['method'],
                'convention': self.config['convention'], 'calendar_policy': self.config['calendar_policy'],
                'sources': deepcopy(self.config['sources']),
                'hexagrams': [self.chart(number) for number in range(1, 65)]}

    def reading(self, number):
        reference_lines = []
        for i in range(1, 7):
            card = next(c for c in self.explanations.hexagram(number, i)['cards'] if c['text_type'] == 'LINE_TEXT')
            line = next(l for l in self.explanations.by_id[number]['lines'] if l['id'] == i)
            card['title'] = f"Hào {i} · {line['name']}"
            reference_lines.append(card)
        return CoinReading.model_validate({
            'schema_version': 'coin-reading-v1', 'corpus_version': self.explanations.draft['version'],
            'chart': self.chart(number), 'text': self.explanations.hexagram(number), 'reference_lines': reference_lines,
            'interpretation_review_status': 'AI_DRAFT_UNREVIEWED',
        }).model_dump(mode='json')

    def consult(self, request: CoinRequest):
        throws = (deepcopy(request.throws_bottom_to_top) if request.source == 'MANUAL' else
                  [['BACK' if secrets.randbits(1) else 'INSCRIPTION' for _ in range(3)] for _ in range(6)])
        totals = [sum(3 if face == 'BACK' else 2 for face in row) for row in throws]
        bits, moving, changed = cast_bits(totals)
        instant = request.casting.clicked_at if request.casting.mode == 'CURRENT' else request.casting.custom_timestamp
        clock = pillars(instant)
        original_id, changed_id = (self.iching.by_bits[value]['id'] for value in (bits, changed))
        guide = list(READING_GUIDE)
        if not moving:
            guide.insert(0, 'Sáu hào đều tĩnh: không có hào động và không lập quẻ biến riêng.')
        if len(moving) == 6 and original_id in (1, 2):
            special = [l for l in self.explanations.by_id[original_id]['lines'] if l['id'] > 6]
            for row in special:
                guide.append(f"Nguyên văn tham khảo {row['name']}: {row['scripture']}")
        return CoinResponse.model_validate({
            'schema_version': 'coin-consultation-v1', 'request_id': request.request_id,
            'created_at': datetime.now(timezone.utc), 'rules_version': self.config['rules_version'],
            'question': request.question,
            'casting': {'method': self.config['method'], 'source': request.source, 'throws_bottom_to_top': throws,
                        'totals_bottom_to_top': totals, 'convention': self.config['convention'],
                        'randomness': 'SYSTEM_SECRETS' if request.source == 'RANDOM' else 'USER_SUPPLIED'},
            'calendar': {**clock, 'civil_datetime': instant.isoformat(), 'policy': self.config['calendar_policy'],
                         'rules_sha256': self.rules_sha256},
            'original': self.reading(original_id), 'changed': self.reading(changed_id) if moving else None,
            'moving_lines': moving, 'najia': self.najia.chart(bits, changed, moving, clock),
            'reading_guide': guide, 'limitations': LIMITATIONS, 'sources': self.config['sources'],
        }).model_dump(mode='json')


class CoinStore:
    def __init__(self, store):
        self.store = store
        with store.connect() as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS coin_sessions (request_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, response TEXT NOT NULL)')

    def execute(self, request, builder):
        payload = json.dumps(request.model_dump(mode='json'), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        digest = sha256(payload.encode()).hexdigest()
        with self.store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT payload_hash, response FROM coin_sessions WHERE request_id=?', (str(request.request_id),)).fetchone()
            if row:
                if row[0] != digest:
                    raise EngineError('COIN_REQUEST_CONFLICT', 'Mã phiên đã dùng với dữ liệu khác. Hãy tạo phiên mới.', 409)
                return json.loads(row[1])
            result = builder()
            connection.execute('INSERT INTO coin_sessions VALUES (?, ?, ?, ?)',
                               (str(request.request_id), digest, result['created_at'], json.dumps(result, ensure_ascii=False)))
            return result

    def get(self, request_id):
        with self.store.connect() as connection:
            row = connection.execute('SELECT response FROM coin_sessions WHERE request_id=?', (str(request_id),)).fetchone()
        if row is None:
            raise EngineError('COIN_NOT_FOUND', 'Không tìm thấy phiên gieo ba đồng.', 404)
        return json.loads(row[0])

    def history(self, limit=10):
        with self.store.connect() as connection:
            rows = connection.execute('SELECT response FROM coin_sessions ORDER BY rowid DESC LIMIT ?', (limit,)).fetchall()
        result = []
        for row in rows:
            data = json.loads(row[0])
            result.append({**{k: data[k] for k in ('request_id', 'question', 'created_at', 'rules_version')},
                           'source': data['casting']['source'], 'chart': data['original']['chart'],
                           'moving_lines': data['moving_lines']})
        return result
