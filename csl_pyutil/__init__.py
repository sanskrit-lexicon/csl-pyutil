# -*- coding: utf-8 -*-
"""csl_pyutil — generic (non-Sanskrit-specific) Python helpers shared across
the CDSL / Sanskrit-Lexicon repos.

Public API
----------
render_review_sheet(items, config, extras=True)   self-contained HTML review/
                                                    voting sheet (H925)
anatomy.highlight(raw, target=None, ...)          colour-coded CDSL raw-markup
anatomy.legend_html(parts=None, ...)                anatomy for a panel (H1808)
"""
from csl_pyutil import anatomy
from csl_pyutil.review_sheet import render_review_sheet, esc, mark_cyrillic

__version__ = "0.8.0"
__all__ = ["render_review_sheet", "esc", "mark_cyrillic", "anatomy"]
