# -*- coding: utf-8 -*-
"""csl_pyutil — generic (non-Sanskrit-specific) Python helpers shared across
the CDSL / Sanskrit-Lexicon repos.

Public API
----------
render_review_sheet(items, config, extras=True)   self-contained HTML review/
                                                    voting sheet (H925)
render_review_sheet_packset(items, config, ...)   the same sheet split into
                                                    packs of 10 sharing one
                                                    sheet_id, plus an index
                                                    page (V16, H2991)
anatomy.highlight(raw, target=None, ...)          colour-coded CDSL raw-markup
anatomy.legend_html(parts=None, ...)                anatomy for a panel (H1808)
evidence.EvidenceManifest / evidence.preflight    the V9 evidence-reuse gate a
                                                    sheet must pass before it is
                                                    written (H1889)
RU_UI_STRINGS                                     one-line Russian chrome
                                                    preset for config["ui_strings"]
                                                    (H2854)
integrity_tripwire.check / .extract               committed checksum + key-set
                                                    on human-reviewed overlay
                                                    data, red in CI when a
                                                    seeder wipes it (H2891)
"""
from csl_pyutil import anatomy, evidence
from csl_pyutil.evidence import EvidenceManifest, PreflightError, PreflightWarning, preflight
from csl_pyutil.review_sheet import (render_review_sheet, render_review_sheet_packset,
                                     esc, mark_cyrillic, RU_UI_STRINGS)

# integrity_tripwire is imported LAZILY (PEP 562), not eagerly like its
# neighbours. Its documented CI invocation is `python -m
# csl_pyutil.integrity_tripwire --check`, and runpy warns "found in sys.modules
# after import of package" whenever the package has already pulled the module
# in — which it would, on every single tripwire run in every consumer repo. A
# gate whose job is to be believed when it prints RED must not also print a
# spurious RuntimeWarning every time it prints GREEN.
_LAZY = {
    "integrity_tripwire": None,
    "TripwireError": "integrity_tripwire",
    "project": "integrity_tripwire",
    "overlay_digest": "integrity_tripwire",
    "keyset_digest": "integrity_tripwire",
    "is_reviewed": "integrity_tripwire",
    "extract": "integrity_tripwire",
    "check": "integrity_tripwire",
    "redact": "integrity_tripwire",
}


def __getattr__(name):
    if name in _LAZY:
        import importlib

        module = importlib.import_module("csl_pyutil.integrity_tripwire")
        return module if _LAZY[name] is None else getattr(module, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(list(globals()) + list(_LAZY))

__version__ = "0.17.1"
__all__ = ["render_review_sheet", "render_review_sheet_packset", "esc", "mark_cyrillic",
           "RU_UI_STRINGS", "anatomy", "evidence",
           "EvidenceManifest", "PreflightError", "PreflightWarning", "preflight",
           "integrity_tripwire", "TripwireError", "project", "overlay_digest",
           "keyset_digest", "is_reviewed", "extract", "check"]
