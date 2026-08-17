# -*- coding: utf-8 -*-
"""csl_pyutil — generic (non-Sanskrit-specific) Python helpers shared across
the CDSL / Sanskrit-Lexicon repos.

Public API
----------
render_review_sheet(items, config, extras=True)   self-contained HTML review/
                                                    voting sheet (H925)
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
from csl_pyutil import anatomy, evidence, integrity_tripwire
from csl_pyutil.evidence import EvidenceManifest, PreflightError, PreflightWarning, preflight
from csl_pyutil.integrity_tripwire import (
    TripwireError,
    check,
    extract,
    is_reviewed,
    keyset_digest,
    overlay_digest,
    project,
)
from csl_pyutil.review_sheet import render_review_sheet, esc, mark_cyrillic, RU_UI_STRINGS

__version__ = "0.15.0"
__all__ = ["render_review_sheet", "esc", "mark_cyrillic", "RU_UI_STRINGS", "anatomy", "evidence",
           "EvidenceManifest", "PreflightError", "PreflightWarning", "preflight",
           "integrity_tripwire", "TripwireError", "project", "overlay_digest",
           "keyset_digest", "is_reviewed", "extract", "check"]
