"""Vietnam civil-time Ziwei consultations backed by the pinned local engine."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
from threading import BoundedSemaphore
from typing import Literal
from uuid import UUID

from pydantic import Field, ValidationError, field_validator, model_validator

from .engine import EngineError, ROOT
from .models import StrictModel, civil_validator
from .time_engine import BRANCHES

VENDOR = ROOT / "vendor" / "ziwei-doushu"
SOURCE = "https://github.com/Renhuai123/ziwei-doushu"


class ZiweiRequest(StrictModel):
    request_id: UUID
    civil_datetime: datetime
    gender: Literal["male", "female"]

    @field_validator("civil_datetime")
    @classmethod
    def valid_birth(cls, value):
        civil_validator(value)
        if not 1950 <= value.year <= 2026 or value.microsecond:
            raise ValueError("Ngày sinh phải trong 1950–2026, độ phân giải đến giây.")
        return value


class ZiweiStar(StrictModel):
    code: str
    name: str
    type: Literal["major", "minor", "lucky", "sha"]
    brightness: str | None
    transformation: Literal["Lộc", "Quyền", "Khoa", "Kỵ"] | None


class ZiweiPalace(StrictModel):
    code: str
    name: str
    branch: int = Field(ge=0, le=11)
    branch_name: str
    stem_name: str
    opposite_branch: int = Field(ge=0, le=11)
    borrowed_from_branch: int | None
    age_range: tuple[int, int] | None
    stars: list[ZiweiStar]


class ZiweiPattern(StrictModel):
    code: str
    level: Literal["excellent", "good", "neutral", "caution"]
    required: list[str]
    bonus: list[str]
    breaking: list[str]
    source: str | None


class ZiweiLunarDate(StrictModel):
    year: int
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=30)
    leap: bool


class ZiweiChart(StrictModel):
    lunar_date: ZiweiLunarDate
    chart_lunar_month: int = Field(ge=1, le=12)
    cycle_name: str
    ming_branch: int
    body_branch: int
    palaces: list[ZiweiPalace] = Field(min_length=12, max_length=12)
    patterns: list[ZiweiPattern]

    @model_validator(mode="after")
    def validate_chart(self):
        branches = {p.branch for p in self.palaces}
        majors = [star.code for p in self.palaces for star in p.stars if star.type == "major"]
        codes = {p.code for p in self.palaces}
        if (branches != set(range(12)) or len(codes) != 12 or
                not {code for code, _, _ in PALACE_TOPICS} <= codes or
                self.body_branch not in branches or
                not any(p.code == "命宫" and p.branch == self.ming_branch for p in self.palaces) or
                len(majors) != 14 or set(majors) != STAR_THEMES.keys()):
            raise ValueError("Invalid Ziwei palace or star distribution")
        for p in self.palaces:
            if p.opposite_branch != (p.branch + 6) % 12 or p.borrowed_from_branch not in (None, p.opposite_branch):
                raise ValueError("Invalid opposite palace")
        return self


STAR_THEMES = {
    "紫微": "điều phối và trách nhiệm",
    "天机": "lập kế hoạch và thích nghi",
    "太阳": "sự chủ động và vai trò công khai",
    "武曲": "tính thực tế và quản lý nguồn lực",
    "天同": "hợp tác và giữ hòa khí",
    "廉贞": "ranh giới, quy tắc và cách ứng xử",
    "天府": "tích lũy và gìn giữ nguồn lực",
    "太阴": "quan sát và chuẩn bị kỹ",
    "贪狼": "giao tiếp, sở thích và tìm cơ hội",
    "巨门": "lời nói, phân tích và tranh luận",
    "天相": "hỗ trợ và giữ cân bằng",
    "天梁": "dìu dắt và bảo vệ nguyên tắc",
    "七杀": "quyết đoán khi có áp lực",
    "破军": "thay đổi và tổ chức lại",
}

PALACE_TOPICS = (
    ("命宫", "Tổng quan", "cách tiếp cận việc mới"),
    ("官禄", "Công việc", "vai trò và cách làm việc"),
    ("财帛", "Tài chính", "cách tạo và quản lý nguồn lực"),
    ("夫妻", "Quan hệ", "cách hai người chia sẻ trách nhiệm"),
)

MODIFIER_COPY = {
    ("破军", "天钺"): "Phá Quân gặp Thiên Việt. Khi xét việc đổi cách làm, đây là dấu hiệu để đọc thêm vai trò của người hỗ trợ.",
    ("破军", "地劫"): "Phá Quân đồng cung Địa Kiếp. Phép luận thêm điều kiện giữ nguồn lực khi thay đổi, nhất là lúc chuyển từ thử nghiệm sang thực hiện.",
    ("贪狼", "火星"): "Tham Lang đồng cung Hỏa Tinh. Phép luận xem kỹ nhịp nhanh của cơ hội và khả năng giữ được nguồn lực sau đó.",
    ("天梁", "火星"): "Thiên Lương gặp Hỏa Tinh. Khi luận về bất đồng, tổ hợp này đặt trọng tâm vào cách phản ứng lúc sự việc diễn ra nhanh.",
    ("天梁", "擎羊"): "Thiên Lương gặp Kình Dương. Phép luận xét thêm cách giữ nguyên tắc và cách nói thẳng trong quan hệ.",
    ("武曲", "地空"): "Vũ Khúc gặp Địa Không. Phần đọc quan hệ cần xét thêm chênh lệch giữa cam kết và điều hai người có thể thực hiện.",
}

PATTERN_COPY = {
    "火贪格": ("Hỏa Tham", "Tham Lang đồng cung Hỏa Tinh và cung này hội chiếu Mệnh."),
    "铃贪格": ("Linh Tham", "Tham Lang đồng cung Linh Tinh và cung này hội chiếu Mệnh."),
    "杀破狼": ("Sát Phá Tham", "Thất Sát, Phá Quân và Tham Lang cùng xuất hiện trong tam phương tứ chính của Mệnh."),
    "机月同梁": ("Cơ Nguyệt Đồng Lương", "Các sao Thiên Cơ, Thái Âm, Thiên Đồng và Thiên Lương hội đủ theo điều kiện của bộ luật."),
    "机月同梁三星会": ("Cơ Nguyệt Đồng Lương hội ba sao", "Chỉ ba trong bốn sao hội chiếu, nên chưa đủ điều kiện của cách cục đầy đủ."),
    "紫府同宫": ("Tử Phủ đồng cung", "Tử Vi và Thiên Phủ cùng ở một cung. Vị trí cung này quyết định cách liên hệ với Mệnh."),
    "廉贞天相格": ("Liêm Trinh – Thiên Tướng", "Liêm Trinh và Thiên Tướng cùng ở một cung."),
    "魁钺同会": ("Khôi Việt đồng hội", "Thiên Khôi và Thiên Việt cùng hội chiếu Mệnh."),
    "昌曲同会": ("Xương Khúc đồng hội", "Văn Xương và Văn Khúc cùng hội chiếu Mệnh."),
    "辅弼同会": ("Phụ Bật đồng hội", "Tả Phụ và Hữu Bật cùng hội chiếu Mệnh."),
}


def reading_for(chart):
    by_code = {p.code: p for p in chart.palaces}
    by_branch = {p.branch: p for p in chart.palaces}
    sections = []
    for code, title, context in PALACE_TOPICS:
        palace = by_code[code]
        own = [s for s in palace.stars if s.type == "major"]
        borrowed = by_branch.get(palace.borrowed_from_branch)
        stars = own or ([s for s in borrowed.stars if s.type == "major"] if borrowed else [])
        position = f"Cung {palace.name} tại {palace.branch_name}"
        if own:
            basis = f"{position} có " + ", ".join(s.name for s in own) + "."
        elif stars:
            basis = f"{position} vô chính diệu. Phép đọc tham chiếu " + ", ".join(s.name for s in stars) + f" ở cung đối diện {borrowed.name}."
        else:
            basis = f"{position} vô chính diệu. Hai cung đối diện đều thiếu chính tinh để đọc theo nhóm sao này."
        if stars:
            themes = [f"{s.name} gợi hướng đọc về {STAR_THEMES[s.code]}" for s in stars]
            basis += f" Khi xét {context}, " + ". ".join(themes) + "."
        changes = [f"{s.name} Hóa {s.transformation}" for s in palace.stars if s.transformation]
        if changes:
            basis += " Tứ Hóa ghi nhận " + ", ".join(changes) + " tại cung này."
        own_codes = {s.code for s in own}
        present = {s.code for s in palace.stars}
        for (major, other), text in MODIFIER_COPY.items():
            if major in own_codes and other in present:
                basis += " " + text
        sections.append({"title": title, "text": basis, "palace_branch": palace.branch})

    patterns = [{"code": p.code, "title": PATTERN_COPY[p.code][0], "text": PATTERN_COPY[p.code][1]}
                for p in chart.patterns if p.code in PATTERN_COPY]
    return {"sections": sections, "patterns": patterns}


class ZiweiService:
    def __init__(self):
        raw = (VENDOR / "manifest.json").read_bytes()
        self.manifest = json.loads(raw)
        for name, digest in self.manifest["files"].items():
            if sha256((VENDOR / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"Ziwei engine checksum mismatch: {name}")
        self.rules_sha256 = sha256(raw).hexdigest()
        self.node = shutil.which("node")
        self.slots = BoundedSemaphore(2)

    def consult(self, request):
        civil = request.civil_datetime
        date = civil.date() + timedelta(days=int(civil.hour == 23))
        branch = ((civil.hour + 1) // 2) % 12
        birth = {"year": date.year, "month": date.month, "day": date.day,
                 "hour": branch, "gender": request.gender}
        if not self.node:
            raise EngineError("ZIWEI_ENGINE_FAILED", "Máy chủ chưa có engine lập lá số Tử Vi.", 503)
        if not self.slots.acquire(timeout=3):
            raise EngineError("SERVER_BUSY", "Đang có nhiều lượt lập lá số. Bạn có thể thử lại sau một lát.", 503)
        try:
            result = subprocess.run(
                [self.node, str(VENDOR / "runner.cjs")], input=json.dumps(birth),
                capture_output=True, text=True, cwd=ROOT, timeout=15, check=True,
                env={"TZ": "UTC", "PATH": str(Path(self.node).parent), "TMPDIR": os.getenv("TMPDIR", "/tmp")},
            )
            chart = ZiweiChart.model_validate_json(result.stdout)
        except (subprocess.SubprocessError, OSError, ValidationError):
            raise EngineError("ZIWEI_ENGINE_FAILED", "Chưa lập được lá số Tử Vi. Bạn có thể thử lại.", 503) from None
        finally:
            self.slots.release()

        commit = self.manifest["commit"]
        return {
            "schema_version": "ziwei-consultation-v1", "request_id": request.request_id,
            "created_at": datetime.now(timezone.utc), "civil_datetime": civil, "gender": request.gender,
            "effective_date": date, "hour_branch": BRANCHES[branch], "calendar_policy": "VN_CIVIL_NEXT_DAY_AT_23",
            "engine": {"repository": self.manifest["repository"], "commit": commit,
                       "rules_sha256": self.rules_sha256, "source": f"{SOURCE}/tree/{commit}"},
            "chart": chart, "reading": reading_for(chart), "model_called": False,
        }
