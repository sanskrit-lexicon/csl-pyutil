"""One version per distribution — pinned, because it drifted twice (H2131).

`review_sheet.__version__` was left at 0.5.0 while the package moved to 0.6.0, was
fixed in the 0.7.0 release, and then regressed immediately: at the v0.8.0 tag
`review_sheet.__version__` still read "0.7.0" against `pyproject.toml`'s "0.8.0".
Nothing pinned it, so nothing caught it. This does.
"""
import re
from pathlib import Path

import csl_pyutil
from csl_pyutil import review_sheet

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    """Read [project] version without a TOML dependency (stdlib tomllib is 3.11+)."""
    text = _PYPROJECT.read_text(encoding="utf-8")
    body = text.split("[project]", 1)[1]
    # Stop at the next top-level table so a later table's `version` cannot match.
    body = re.split(r"^\[", body, maxsplit=1, flags=re.M)[0]
    m = re.search(r'^version\s*=\s*"([^"]+)"', body, flags=re.M)
    assert m, "no [project] version in pyproject.toml"
    return m.group(1)


def test_package_and_module_versions_agree():
    assert csl_pyutil.__version__ == review_sheet.__version__


def test_versions_track_pyproject():
    expected = _pyproject_version()
    assert csl_pyutil.__version__ == expected
    assert review_sheet.__version__ == expected
