"""Validate canonical ScriptDocument fixtures, offline, from any working directory."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.domain.validation.report import empty_report
from app.domain.validation.schema_validator import validate_schema
from app.domain.validation.script_validator import validate_script

SCHEMA = ROOT / "contracts/schemas/script-document.schema.json"


def validate_document(document, schema):
    report = validate_schema(document, schema["$id"], {schema["$id"]: schema})
    if not report["errors"]:
        semantic = validate_script(document)
        for severity in report:
            report[severity].extend(semantic[severity])
    return report


def validate_file(path, schema):
    try:
        document = Path(path).read_text(encoding="utf-8-sig")
        document = json.loads(document)
    except (json.JSONDecodeError, UnicodeError) as error:
        report = empty_report()
        report["errors"].append({"code": "document.invalid_json", "path": "", "message": str(error)})
        return report
    return validate_document(document, schema)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="*", type=Path)
    args = parser.parse_args()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8-sig"))
    paths = args.documents or sorted((ROOT / "contracts/examples").glob("script-document.*.json"))
    if not paths:
        parser.error("No ScriptDocument fixtures found")
    results = {str(path): validate_file(path, schema) for path in paths}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return int(any(report["errors"] for report in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
