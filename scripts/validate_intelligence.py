#!/usr/bin/env python3
"""Validates every JSON file under argus-intelligence/{services,technologies,
vulnerabilities}/ against argus-intelligence/schema.json.

Usage:
    python scripts/validate_intelligence.py

Exits 0 and prints a summary if every file is valid. Exits 1 and prints one
line per problem — file path, the exact field, and what's wrong — if
anything fails, so a malformed contributed entry is caught here instead of
silently breaking the intelligence loader at runtime (loader.py currently
just logs a warning and skips a file it can't parse, which is easy to miss).

Also runnable as a pytest test (see backend/tests/test_intelligence_schema.py),
which calls validate() directly and asserts no errors.
"""
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("error: the 'jsonschema' package is required — pip install jsonschema", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
INTELLIGENCE_DIR = REPO_ROOT / "argus-intelligence"
SCHEMA_PATH = INTELLIGENCE_DIR / "schema.json"
CATEGORIES = ("services", "technologies", "vulnerabilities")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def validate() -> list[str]:
    """Returns a list of human-readable error strings — empty if everything's valid."""
    errors: list[str] = []

    if not SCHEMA_PATH.exists():
        return [f"schema not found at {_relative(SCHEMA_PATH)}"]

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())

    found_any_file = False
    for category in CATEGORIES:
        cat_dir = INTELLIGENCE_DIR / category
        if not cat_dir.is_dir():
            errors.append(f"{category}/: directory not found under {_relative(INTELLIGENCE_DIR)}")
            continue

        for json_file in sorted(cat_dir.glob("*.json")):
            found_any_file = True
            rel = _relative(json_file)

            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"{rel}: invalid JSON — {e.msg} (line {e.lineno}, column {e.colno})")
                continue

            for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
                field = ".".join(str(p) for p in error.absolute_path) or "(root)"
                errors.append(f"{rel}: field '{field}' — {error.message}")

    if not found_any_file:
        errors.append(f"no *.json files found under {_relative(INTELLIGENCE_DIR)}/{{{','.join(CATEGORIES)}}}/")

    return errors


def main() -> int:
    errors = validate()

    if errors:
        print(f"Intelligence library validation FAILED — {len(errors)} problem(s):\n", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        print(f"\nSee {_relative(INTELLIGENCE_DIR / 'SCHEMA.md')} for field documentation "
              f"and {_relative(INTELLIGENCE_DIR / 'CONTRIBUTING.md')} for how to fix this.", file=sys.stderr)
        return 1

    total = sum(len(list((INTELLIGENCE_DIR / c).glob("*.json"))) for c in CATEGORIES)
    print(f"Intelligence library validation passed — {total} entries across {', '.join(CATEGORIES)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
