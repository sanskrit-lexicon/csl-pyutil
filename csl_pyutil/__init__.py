# -*- coding: utf-8 -*-
"""csl_pyutil — generic (non-Sanskrit-specific) Python helpers shared across
the CDSL / Sanskrit-Lexicon repos.

Public API
----------
render_review_sheet(items, config, extras=True)   self-contained HTML review/
                                                    voting sheet (H925)
"""
from csl_pyutil.review_sheet import render_review_sheet, esc

__version__ = "0.2.0"
__all__ = ["render_review_sheet", "esc"]
