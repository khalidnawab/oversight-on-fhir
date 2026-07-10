"""Guards that the published IG and the Python reference implementation agree on canonical URLs.
Skips if the IG has not been built with SUSHI yet."""
import json
from pathlib import Path

import pytest

from oversight.oversight import taxonomy as t

_GEN = Path(__file__).parent.parent / "ig" / "fsh-generated" / "resources"
pytestmark = pytest.mark.skipif(not _GEN.exists(), reason="IG not built (run `npx fsh-sushi ig`)")


def _load(name: str) -> dict:
    return json.loads((_GEN / name).read_text(encoding="utf-8"))


def test_reason_codesystem_url_matches_taxonomy():
    cs = _load("CodeSystem-oversight-reason.json")
    assert cs["url"] == t.REASON_CS_URL
    codes = {c["code"] for c in cs["concept"]}
    assert {c["code"] for c in t.REASON_CODES} == codes


def test_disposition_codesystem_url_matches_taxonomy():
    cs = _load("CodeSystem-oversight-disposition.json")
    assert cs["url"] == t.DISPOSITION_CS_URL
    assert {c["code"] for c in cs["concept"]} == {c["code"] for c in t.DISPOSITION_CODES}


def test_reason_extension_url_matches_taxonomy():
    ext = _load("StructureDefinition-oversight-reason-ext.json")
    assert ext["url"] == t.REASON_EXT_URL


def test_oversight_event_profile_exists():
    sd = _load("StructureDefinition-oversight-event.json")
    assert sd["type"] == "AuditEvent"
    assert sd["kind"] == "resource"
