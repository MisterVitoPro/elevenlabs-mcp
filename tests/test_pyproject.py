import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

PYPROJECT = Path(__file__).parent.parent / "pyproject.toml"


def _get_deps():
    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["dependencies"]


def test_elevenlabs_dep_has_upper_bound():
    # P1-009: elevenlabs dep must pin an upper bound to avoid breaking major-version upgrades
    spec = next((d for d in _get_deps() if d.startswith("elevenlabs")), None)
    assert spec is not None
    assert "<3" in spec, f"elevenlabs must have upper bound <3.0.0, got: {spec}"


def test_elevenlabs_dep_has_minimum_2x():
    # P1-009: elevenlabs dep floor must be >=2.0.0 to guarantee the v2 API surface
    spec = next((d for d in _get_deps() if d.startswith("elevenlabs")), None)
    assert spec is not None
    assert ">=2" in spec, f"elevenlabs floor must be >=2.0.0, got: {spec}"


def test_fastmcp_dep_has_upper_bound():
    # P1-009: fastmcp dep must pin an upper bound to avoid breaking major-version upgrades
    spec = next((d for d in _get_deps() if d.startswith("fastmcp")), None)
    assert spec is not None
    assert "<4" in spec, f"fastmcp must have upper bound <4.0.0, got: {spec}"
