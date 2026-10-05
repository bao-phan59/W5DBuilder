"""JSON-compatible validation reports shared by pure domain validators."""
from typing import TypedDict


class Issue(TypedDict):
    code: str
    path: str
    message: str


class ValidationReport(TypedDict):
    errors: list[Issue]
    warnings: list[Issue]
    infos: list[Issue]


def empty_report() -> ValidationReport:
    return {"errors": [], "warnings": [], "infos": []}


def pointer(parts) -> str:
    """RFC 6901 pointer; the empty string addresses the document root."""
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)
