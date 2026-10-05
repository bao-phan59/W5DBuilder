"""Structural validation with an explicitly supplied, offline schema registry."""
from collections.abc import Mapping

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .report import ValidationReport, empty_report, pointer


def validate_schema(document, schema_id: str, schemas: Mapping[str, dict]) -> ValidationReport:
    # Missing/invalid schemas are configuration errors, not user data errors.
    schema = schemas[schema_id]
    registry = Registry().with_resources(
        (key, Resource.from_contents(value)) for key, value in schemas.items()
    )
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    report = empty_report()
    for error in sorted(validator.iter_errors(document), key=lambda item: pointer(item.absolute_path)):
        report["errors"].append({
            "code": f"schema.{error.validator}",
            "path": pointer(error.absolute_path),
            "message": error.message,
        })
    return report
