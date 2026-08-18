# -*- coding: utf-8 -*-
"""Build the H2991 22-card packset fixture — the B4 acceptance artifact.

`python tests/fixtures/build_v16_packset_demo.py <outdir>` writes

    <outdir>/h2991_demo.html            parent index (3 packs)
    <outdir>/h2991_demo/pack-01.html    cards 1-10
    <outdir>/h2991_demo/pack-02.html    cards 11-20
    <outdir>/h2991_demo/pack-03.html    cards 21-22

which is the hub's own layout (`vote/sheets/<name>.html` beside
`vote/sheets/<name>/pack-NN.html`). Voting pack 1 must leave pack 2 untouched
while the parent reads 10/22 — all three pages share one `sheet_id`, so one
localStorage record backs the whole sheet.

`--client-id` fills `github_inbox["client_id"]`; `--device-url` names a
CORS-capable relay for the device-code exchange. Without BOTH, the «Save to
GitHub» button ships disabled — GitHub sends no `Access-Control-Allow-Origin`
on `login/device/*` (measured 18-08-2026), so a static page cannot complete the
exchange on its own.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8")

from csl_pyutil import RU_UI_STRINGS, render_review_sheet_packset  # noqa: E402

SHEET_ID = "h2991_demo"
N = 22


def items():
    return [
        {"id": "D%02d" % i, "filt": "even" if i % 2 == 0 else "odd",
         "title": "demo card %d" % i,
         "question": "Карточка %d из %d: принять предложенное значение?" % (i, N),
         "panels": [("context", "<pre>card %d — before / after</pre>" % i)]}
        for i in range(1, N + 1)
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--client-id", default="")
    ap.add_argument("--device-url", default="")
    args = ap.parse_args()

    config = {
        "sheet_id": SHEET_ID,
        "title": "H2991 — packset demo",
        "subtitle": "22 карточки, 3 пакета — фикстура приёмки V16",
        "footer": "Approve/Reject/Defer per item.",
        "approve_label": "Approve", "reject_label": "Reject",
        "filters": [("odd", "odd"), ("even", "even")],
        "generated": "2026-08-18",
        "pack_size": 10,
        "ui_strings": RU_UI_STRINGS,
        "github_inbox": {"repo": "gasyoun/vote-inbox",
                         "client_id": args.client_id,
                         "device_url": args.device_url},
    }
    screening = {"deterministic": 0, "lookup": 0, "agent": 0, "human": N,
                 "evidence_path": "tests/fixtures/build_v16_packset_demo.py",
                 "rules": ["synthetic fixture — no screening applied"]}

    out = render_review_sheet_packset(items(), config, screening=screening,
                                      hub_name=SHEET_ID)
    assert out["parent"] is not None and len(out["packs"]) == 3, "expected parent + 3 packs"

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / (SHEET_ID + ".html")).write_text(out["parent"], encoding="utf-8")
    packdir = args.outdir / SHEET_ID
    packdir.mkdir(exist_ok=True)
    for n, html in enumerate(out["packs"], 1):
        (packdir / ("pack-%02d.html" % n)).write_text(html, encoding="utf-8")

    print("parent : %s" % (args.outdir / (SHEET_ID + ".html")))
    for n in range(1, len(out["packs"]) + 1):
        print("pack %02d: %s" % (n, packdir / ("pack-%02d.html" % n)))
    enabled = bool(args.client_id and args.device_url)
    print("github inbox button: %s" % ("ENABLED" if enabled else "disabled (needs client_id + device_url)"))


if __name__ == "__main__":
    main()
