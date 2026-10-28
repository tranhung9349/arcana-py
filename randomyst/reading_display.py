"""Reject machine notation inside AI prose without changing internal contexts."""
import re
import json


class UnreadableReading(ValueError):
    pass


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
