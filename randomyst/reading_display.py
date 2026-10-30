"""Reject machine notation inside AI prose without changing internal contexts."""
import re
import json


class UnreadableReading(ValueError):
    pass


class VerboseReading(ValueError):
    """A new reading exceeds the reading budget; never silently cut its claims."""

    def __init__(self, fields):
        self.fields = fields
        super().__init__("Reading exceeds the plain-language length budget")


class JargonReading(ValueError):
    def __init__(self, fields):
        self.fields = fields
        super().__init__("Reading requires unexplained specialist vocabulary")


BAZI_TERMS = ("nhật chủ", "thập thần", "tàng can", "khí thế", "phù ức", "điều hậu", "vượng nhược",
              "thân vượng", "thân nhược", "sinh xuất", "tiết hao", "dụng thần", "cách cục",
              "nguyệt lệnh", "can lộ", "thực thương", "quan sát", "chính ấn", "thiên ấn")

LIUYAO_TERMS = ("quan quỷ", "phụ mẫu", "thê tài", "huynh đệ", "tử tôn", "dụng thần", "nguyên thần",
                "kỵ thần", "cừu thần", "nhật–nguyệt", "nhật nguyệt", "tuần không", "nguyệt phá",
                "phi thần", "phục thần", "hồi đầu sinh", "hồi đầu khắc", "hóa tiến", "hóa thoái",
                "ám động", "thế–ứng", "thế ứng", "sinh phù", "tiết khí", "vượng suy", "khí thế",
                "khí mùa", "hào động", "hào tĩnh", "hào thế", "hào dụng", "vượng tướng",
                "hợp trói", "biến hào", "hào biến", "minh động", "động biến", "nạp giáp", "lục thân", "lục thú")


def validate_liuyao_language(reading):
    """Keep new reader answers plain; technical evidence remains available separately."""
    def terms(text):
        normalized = re.sub(r"\s*[-–—]\s*", "–", text.casefold())
        found = {term for term in LIUYAO_TERMS if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", normalized)}
        found.update(re.findall(r"\bhào\s+(?:số\s+)?[1-6]\b|\b[lh][1-6]\b", normalized))
        return found
    fields = [("summary", reading.summary.text),
              *[(f"analysis.{i}", row.text) for i, row in enumerate(reading.analysis)],
              *[(f"practical_options.{i}", row.text) for i, row in enumerate(reading.practical_options)],
              *[(f"limits.{i}", text) for i, text in enumerate(reading.limits)]]
    issues = [{"field": name, "terms": sorted(terms(text))} for name, text in fields if terms(text)]
    if issues:
        raise JargonReading(issues)
    return reading


def validate_bazi_language(reading):
    """Keep specialist labels out of the takeaway; allow two in explanations.

    This is a narrow vocabulary check, not a grader of meaning or factual truth.
    Legacy readings remain accessible because this runs only during generation.
    """
    def terms(text):
        return {term for term in BAZI_TERMS
                if (term != "quan sát" or "Quan Sát" in text)
                and re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text.casefold())}
    fields = [("summary", reading.summary.text),
              *[(f"practical_options.{i}", row.text) for i, row in enumerate(reading.practical_options)]]
    issues = [{"field": name, "terms": sorted(terms(text))} for name, text in fields if terms(text)]
    analysis_terms = set().union(*(terms(row.text) for row in reading.analysis))
    if len(analysis_terms) > 2:
        issues.append({"field": "analysis", "max_specialist_terms": 2, "terms": sorted(analysis_terms)})
    if issues:
        raise JargonReading(issues)
    return reading


def validate_reading_brevity(reading, *, section_limit_factor=1.0):
    """Bound new prose only, so saved historical readings remain accessible.

    Counts use whitespace-separated Vietnamese words, including punctuation.
    This checks length, not whether a person understands the interpretation.
    """
    # A short complete Liu Yao article may need uneven section lengths. Keep
    # its hard 300-word total, with modest section headroom rather than failing
    # a useful 261-word answer because its summary has 52 instead of 50 words.
    if not 1 <= section_limit_factor <= 1.5:
        raise ValueError("Invalid section budget")
    fields = [("summary", reading.summary.text, int(50*section_limit_factor))]
    fields += [(f"analysis.{i}", row.text, int(70*section_limit_factor)) for i, row in enumerate(reading.analysis)]
    fields += [(f"practical_options.{i}", row.text, int(35*section_limit_factor)) for i, row in enumerate(reading.practical_options)]
    fields += [(f"limits.{i}", value, int(30*section_limit_factor)) for i, value in enumerate(reading.limits)]
    issues = [{"field": name, "max_words": limit, "actual_words": len(text.split())}
              for name, text, limit in fields if len(text.split()) > limit]
    if len(reading.analysis) > 2:
        issues.append({"field": "analysis", "max_items": 2})
    if sum(len(text.split()) for _, text, _ in fields) > 300:
        issues.append({"field": "reading", "max_words": 300,
                       "actual_words": sum(len(text.split()) for _, text, _ in fields)})
    if issues:
        raise VerboseReading(issues)
    return reading


INTERNAL = re.compile(
    r"```|[{}]|\[object\s+\w+\]|\b[A-Za-z0-9]+_[A-Za-z0-9_]+\b"
    r"|\$(?:schema|defs|ref)\b"
    r"|\b(?:facts?|evidence|findings?|context|assessment|chart|line|engine|date|reading|pillar|stem|root):[A-Za-z0-9_:-]+"
    r"|\b(?:Traceback|ValidationError|TypeError|SyntaxError)\b"
    r"|(?:[\"']\s*:\s*[\"'\[{\d])|<\/?[A-Za-z][^>]*>"
)


def readable_prose(text):
    if not isinstance(text, str) or INTERNAL.search(text):
        return False
    if re.search(r"(?:^|\n)\s*(?:type|properties|required|additionalProperties|summary|analysis)\s*:\s*(?:object|array|string|boolean|number|\[|\n|$)", text):
        return False
    if text.strip().startswith("[") and text.strip().endswith("]"):
        return False
    for match in re.finditer(r"\[[^\[\]]*\]", text):
        try:
            if isinstance(json.loads(match[0]), list):
                return False
        except ValueError:
            pass
    return True


def validate_reading_prose(reading):
    texts = [reading.summary.text, *(r.text for r in reading.analysis),
             *(r.text for r in reading.practical_options), *reading.limits]
    if not all(readable_prose(text) for text in texts):
        raise UnreadableReading("Reading prose contains internal notation")
    return reading
