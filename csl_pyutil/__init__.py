# -*- coding: utf-8 -*-
"""csl_pyutil — generic (non-Sanskrit-specific) Python helpers shared across
the CDSL / Sanskrit-Lexicon repos.

Public API
----------
render_review_sheet(items, config, extras=True)   self-contained HTML review/
                                                    voting sheet (H925)
"""
from csl_pyutil.review_sheet import render_review_sheet, esc, mark_cyrillic

__version__ = "0.5.0"
__all__ = ["render_review_sheet", "esc", "mark_cyrillic"]
