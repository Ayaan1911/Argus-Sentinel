"""Runs the same validation as `python scripts/validate_intelligence.py`
against every argus-intelligence/*.json entry, as part of the normal test
suite — so a malformed contributed entry fails CI immediately instead of
silently breaking the intelligence loader at runtime (loader.py currently
just logs a warning and skips a file it can't parse)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_intelligence import validate  # noqa: E402


def test_intelligence_library_entries_are_valid():
    errors = validate()
    assert not errors, "argus-intelligence validation failed:\n" + "\n".join(f"  {e}" for e in errors)
