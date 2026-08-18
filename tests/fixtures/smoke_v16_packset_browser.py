# -*- coding: utf-8 -*-
"""H2991 B4 live smoke — the 22-card fixture in a real browser.

Serves the built packset over http://127.0.0.1 so all three pages share ONE
origin (exactly as gasyoun.github.io does; file:// would give each page an
opaque origin and the shared-record claim would be untestable).

Asserts the acceptance sentence: "voting pack 1 leaves pack 2 unvoted; the
parent shows 1/3".
"""
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(sys.argv[1])
PORT = 8731

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % PORT

fails = []


def check(label, got, want):
    ok = got == want
    print("%s %-52s got=%r want=%r" % ("PASS" if ok else "FAIL", label, got, want))
    if not ok:
        fails.append(label)


from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context()
    page = ctx.new_page()

    # ---- pack 1: vote all 10 cards approve
    page.goto("%s/h2991_demo/pack-01.html" % base)
    page.wait_for_selector(".card")
    check("pack-01 renders 10 cards", page.locator(".card").count(), 10)
    for card in page.locator(".card").all():
        card.locator('button.vote[data-vote="approve"]').click()
    page.wait_for_timeout(300)
    check("pack-01 tally approve", page.locator("#c-approve").inner_text(), "10")
    check("pack-01 tally unvoted", page.locator("#c-unvoted").inner_text(), "0")

    store = page.evaluate("() => localStorage.getItem('review-sheet:h2991_demo')")
    import json
    rec = json.loads(store)
    check("shared record holds 10 decisions",
          sum(1 for v in rec.values() if v.get("decision")), 10)
    check("record holds ONLY pack-1 ids",
          sorted(k for k in rec if rec[k].get("decision")),
          ["D%02d" % i for i in range(1, 11)])

    # ---- pack 2: same origin, same sheet_id -> must be untouched
    page.goto("%s/h2991_demo/pack-02.html" % base)
    page.wait_for_selector(".card")
    page.wait_for_timeout(200)
    check("pack-02 renders 10 cards", page.locator(".card").count(), 10)
    check("pack-02 approve still 0", page.locator("#c-approve").inner_text(), "0")
    check("pack-02 unvoted still 10", page.locator("#c-unvoted").inner_text(), "10")

    # ---- pack 3: the short tail
    page.goto("%s/h2991_demo/pack-03.html" % base)
    page.wait_for_selector(".card")
    check("pack-03 is the short pack (2)", page.locator(".card").count(), 2)

    # ---- parent: 10 of 22, pack 1 done
    page.goto("%s/h2991_demo.html" % base)
    page.wait_for_timeout(300)
    check("parent overall text", page.locator("#ovText").inner_text(), "10 of 22 decided")
    check("parent pack-01 progress", page.locator("#pack-01 .prog").inner_text(), "10 / 10")
    check("parent pack-02 progress", page.locator("#pack-02 .prog").inner_text(), "0 / 10")
    check("parent pack-03 progress", page.locator("#pack-03 .prog").inner_text(), "0 / 2")
    check("parent marks pack-01 done",
          "done" in (page.locator("#pack-01").get_attribute("class") or ""), True)
    check("parent marks pack-02 not done",
          "done" in (page.locator("#pack-02").get_attribute("class") or ""), False)
    check("parent says 1 of 3 packs finished",
          page.locator("a.pack.done").count(), 1)

    # ---- inbox button: configured but no client_id/relay -> disabled
    page.goto("%s/h2991_demo/pack-01.html" % base)
    page.wait_for_timeout(200)
    check("inbox button present", page.locator("#inboxBtn").count(), 1)
    check("inbox button disabled", page.locator("#inboxBtn").is_disabled(), True)
    check("inbox note explains why",
          "релея" in page.locator("#inboxNote").inner_text(), True)

    errors = []
    page2 = ctx.new_page()
    page2.on("pageerror", lambda e: errors.append(str(e)))
    page2.goto("%s/h2991_demo/pack-02.html" % base)
    page2.wait_for_timeout(700)
    check("no uncaught JS errors on a pack", errors, [])

    browser.close()

httpd.shutdown()
print()
if fails:
    print("SMOKE FAILED: %d check(s): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("SMOKE PASS — all checks green")
