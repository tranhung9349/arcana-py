"""Pinned tinix-bazi engine, isolated from its Express/DB/OpenRouter application."""
from datetime import datetime
from hashlib import sha256
from html import unescape
import json
from pathlib import Path
import re
import shutil
import subprocess
from threading import BoundedSemaphore
from zoneinfo import ZoneInfo

from .bazi_models import BaziEngineResult, BaziEvidence, BaziFinding, NatalAssessment, NatalReading
from .bazi_rules import BaziRules, digest
from .engine import EngineError

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor/tinix-bazi"
COMMIT = "80ff4463d0397c1b11db76f38d880255f55558bc"
VERSION = "tinix-bazi-2026-10-28-v2"
SOURCE_URL = f"https://github.com/vhphuoc1102/tinix-bazi/tree/{COMMIT}/backendjs/src/bazi"
TOPICS = {"GENERAL": "Tổng quan", "CAREER": "Công việc", "WEALTH": "Tài chính", "STUDY": "Học tập", "RELATIONSHIPS": "Quan hệ"}


def prose(value):
    """Source prose is data: remove presentation markup; never execute it."""
    text = re.sub(r"<br\s*/?>|</p>", "\n", str(value), flags=re.I)
    text = unescape(re.sub(r"<[^>]*>", "", text))
    return re.sub(r"[*#=]{2,}", "", text).strip()


def excerpts(value, budget=2400):
    rows = []
    def visit(item):
        if isinstance(item, str):
            text = prose(item)
            if text:
                rows.append(text)
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
    visit(value)
    return "\n".join(rows)[:budget]


class TinixBaziEngine:
    def __init__(self):
        # Reuse the existing verified calendar tables and primary bibliography.
        # Their former interpretation evaluator is never called for new charts.
        self.reference = BaziRules()
        self.config = self.reference.config
        manifest = json.loads((VENDOR / "manifest.json").read_text())
        for row in manifest["files"]:
            if sha256((VENDOR / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
                raise RuntimeError("Tinix engine checksum mismatch: " + row["path"])
        self.rules_sha256 = digest(manifest)
        self.version = VERSION
        self.corpus_version = "tinix-bazi-" + COMMIT[:12]
        self.node = shutil.which("node")
        self._slots = BoundedSemaphore(2)
        if not self.node:
            raise RuntimeError("Tinix Bazi requires Node.js >= 18 and npm ci")
        text = "Engine tinix-bazi được ghim theo commit; kết quả thuộc quy tắc mệnh lý truyền thống trong mã nguồn."
        self.evidence = [*self.reference.evidence, BaziEvidence(evidence_id="engine:tinix", kind="PROVIDER",
            title="Tinix BaZi engine · " + COMMIT[:12], text=text, url=SOURCE_URL, sha256=sha256(text.encode()).hexdigest())]
        self.coverage = [
            {"feature": "NATAL", "status": "SUPPORTED", "detail": "Tứ Trụ, Ngũ Hành, Dụng Hỷ Kỵ và luận tĩnh từ engine tinix-bazi."},
            {"feature": "LUCK_CYCLES", "status": "SUPPORTED", "detail": "Đại vận và Lưu niên theo giới tính và năm xem đã chọn."},
            {"feature": "CLASSICS", "status": "PARTIAL", "detail": "Điển tích là lời diễn giải đi kèm mã nguồn tinix-bazi, không mặc định là nguyên văn cổ thư đã kiểm chứng."},
            {"feature": "INTERPRETATION", "status": "PARTIAL", "detail": "Các nhánh luận của engine có thể dùng phép chấm khác nhau; ưu tiên phép cân bằng Ngũ Hành khi đọc vượng nhược và Dụng Hỷ Kỵ. Luận truyền thống không xác nhận sự kiện, bệnh lý hay kết quả tài chính."},
        ]

    def overview(self):
        return {**self.reference.overview(), "rules_version": self.version, "rules_sha256": self.rules_sha256,
                "corpus_version": self.corpus_version, "coverage": self.coverage,
                "engine": {"repository": "vhphuoc1102/tinix-bazi", "commit": COMMIT},
                "features": ["Homepage", "BaziChart", "LuckCycles", "Interpretation", "Consultant", "ConsultationHistory"]}

    def calculate(self, chart, gender, target_year=None):
        now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        year = target_year or now.year
        birth = chart.beijing_datetime
        request = {"birth": {"year": birth.year, "month": birth.month, "day": birth.day,
                    "hour": birth.hour, "minute": birth.minute, "second": birth.second,
                    "isFemale": gender == "female", "isSolar": True},
                   "pillars": [p.stem.zh + p.branch_zh for p in chart.pillars], "target_year": year,
                   "reference_time": f"{year}-07-01T12:00:00+07:00"}
        if not self._slots.acquire(timeout=3):
            raise EngineError("SERVER_BUSY", "Engine Bát Tự đang bận. Bạn có thể thử lại sau một lát.", 503)
        try:
            completed = subprocess.run([self.node, str(VENDOR / "runner.cjs")], input=json.dumps(request),
                capture_output=True, text=True, cwd=ROOT, timeout=15, check=True,
                env={"TZ": "UTC", "PATH": str(Path(self.node).parent)})
            result = json.loads(completed.stdout)
            if result["pillars"] != request["pillars"]:
                raise ValueError("Calendar mismatch")
        except (subprocess.SubprocessError, OSError, ValueError, KeyError):
            raise EngineError("BAZI_ENGINE_FAILED", "Engine Bát Tự chưa tính được lá số. Hãy kiểm tra ngày giờ sinh và thử lại.", 503) from None
        finally:
            self._slots.release()
        return BaziEngineResult(commit=COMMIT, adapter_version=VERSION, gender=gender, target_year=year,
            input_sha256=digest(request), result_sha256=digest(result), result=result)

    def evaluate(self, chart, facts, engine):
        result = engine.result
        balance = result["analysis"]["can_bang_ngu_hanh"]
        strength_name = balance["nhan_dinh"]["cuong_do"]
        preferred, supporting, restrain = [list(dict.fromkeys(balance[key]["ngu_hanh"])) for key in ("dung_than", "hy_than", "ky_than")]
        climate = balance["dieu_hau"]["can_thiet"]
        assessment = NatalAssessment(strength="STRONG" if "Vượng" in strength_name else "WEAK" if "Nhược" in strength_name else "MIXED",
            strength_name=strength_name, possible_following="Ngoại cách" in strength_name, structures=[],
            balance={"state": "CONDITIONAL", "preferred": preferred, "supporting": supporting, "restrain": restrain},
            climate_element=climate, climate_conflict=climate in restrain if climate else False)
        refs = [p.fact_id for p in chart.pillars]
        findings = []
        def add(key, title, text, fact_refs=refs):
            findings.append(BaziFinding(finding_id=key, rule_id="TINIX_" + key.upper(), title=title,
                text=prose(text), state="CONDITIONAL", fact_refs=fact_refs, evidence_refs=["engine:tinix"]))
        add("natal_context", "Lá số Tứ Trụ", " · ".join(p.stem.name + " " + p.branch for p in chart.pillars))
        add("roots", "Căn khí", excerpts(result["analysis"]["quan_he_can_chi"].get("can_khi", [])) or "Không có căn khí được engine ghi nhận.")
        scores = balance["nhan_dinh"]["diem_tuong_doi"]
        add("strength", "Vượng nhược theo phép cân bằng Ngũ Hành", f"{strength_name}. Điểm trợ lực {scores['ho_tro']}; điểm tiết hao và chế ước {scores['khac_che']}.")
        add("structure", "Cách cục", excerpts(result["analysis"]["ket_luan"], 1500))
        add("balance", "Dụng · Hỷ · Kỵ", "Ưu tiên: " + ", ".join(preferred) + "; hỗ trợ: " + ", ".join(supporting) + "; tiết chế: " + ", ".join(restrain))
        add("climate", "Điều hậu", excerpts(balance["dieu_hau"]) or "Không có yêu cầu điều hậu riêng theo engine.")
        add("relations", "Ma trận quan hệ Can Chi", excerpts(result["analysis"]["quan_he_can_chi"]))
        for key, title in (("luan_tinh", "Luận tĩnh"), ("luan_dong", "Luận động")):
            add(key, title, excerpts(result["analysis"][key]))
        add("luck_cycles", "Đại vận và Lưu niên", f"Engine đã tính {len(result['luck_cycles'])} đại vận; năm xem {engine.target_year}. " + excerpts(result["annual"], 1600))
        return assessment, findings

    def compose(self, assessment, findings, topic, question):
        selected = [f for f in findings if f.finding_id in {"natal_context", "strength", "structure", "balance", "relations", "luck_cycles"}]
        priority = {"GENERAL": ["natal_context", "strength"], "CAREER": ["structure", "balance"],
                    "WEALTH": ["balance", "luck_cycles"], "STUDY": ["strength", "structure"],
                    "RELATIONSHIPS": ["relations", "natal_context"]}[topic]
        selected.sort(key=lambda f: priority.index(f.finding_id) if f.finding_id in priority else len(priority))
        return NatalReading(topic=topic, topic_name=TOPICS[topic], question=question, title="Bát Tự · " + TOPICS[topic],
            summary="Lá số được phân tích bằng engine tinix-bazi: " + assessment.strength_name + ".",
            highlights=["strength", "structure", "balance", "luck_cycles"],
            sections=[{"title": f.title, "text": f.text, "finding_refs": [f.finding_id]} for f in selected], narrative_version=VERSION)
