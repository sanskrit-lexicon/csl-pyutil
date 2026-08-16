# -*- coding: utf-8 -*-
"""H2854 step 1 — <meta name="generator"> lets the vote-hub CI staleness check
(gasyoun.github.io) compare a published sheet against the latest csl-pyutil
release tag with a plain string read, no repo-side bookkeeping."""
import csl_pyutil

from test_review_sheet import _config, _items, render_review_sheet
from csl_pyutil import render_review_sheet as _render_raw


def test_generator_meta_present_when_extras_true():
    out = render_review_sheet(_items(), _config())
    marker = '<meta name="generator" content="csl-pyutil/%s">' % csl_pyutil.__version__
    assert marker in out
    # placed right after the color-scheme meta, before <title>
    cs = out.index('<meta name="color-scheme" content="dark">')
    gen = out.index(marker)
    title = out.index("<title>")
    assert cs < gen < title


def test_generator_meta_absent_when_extras_false():
    out = _render_raw(_items(), _config(), extras=False)
    assert "generator" not in out
