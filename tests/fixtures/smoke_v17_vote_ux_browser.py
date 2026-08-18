# -*- coding: utf-8 -*-
"""V17 in a real browser — the four things MG asked for, checked as a reviewer sees them."""
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(sys.argv[1])
PORT = 8761
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % PORT

fails = []


def check(label, cond, detail=""):
    print("  %s %-52s%s" % ("PASS" if cond else "FAIL", label, detail))
    if not cond:
        fails.append(label)


from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_context(viewport={"width": 1200, "height": 800}).new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto("%s/h2991_demo/pack-01.html" % base)
    page.wait_for_selector(".card")
    page.wait_for_timeout(400)

    # 2. progress bar at the top, and it is actually at the top of the viewport
    pb = page.locator("#voteProg")
    check("progress bar present", pb.count() == 1)
    box = pb.bounding_box()
    check("progress bar is at the top", box and box["y"] < 130, " y=%s" % (box and round(box["y"])))

    # 3. whole-set counter
    txt = page.locator("#voteProgText").inner_text()
    check("counter names the WHOLE set", "22" in txt, " %r" % txt)

    # 1. submit controls at the foot, below the cards
    dl = page.locator("#downloadBtn")
    check("download button moved into the foot bar",
          page.locator("#voteBar #downloadBtn").count() == 1)
    dlbox = dl.bounding_box()
    vh = page.viewport_size["height"]
    check("submit is pinned to the bottom of the viewport",
          dlbox and dlbox["y"] > vh * 0.7, " y=%s vh=%s" % (dlbox and round(dlbox["y"]), vh))
    check("submit is below the header in the DOM",
          page.evaluate("() => { var h=document.querySelector('header.top'), b=document.getElementById('voteBar');"
                        " return !!(h && b) && (h.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0; }"))
    check("filters stayed at the top",
          page.locator("#voteBar #filterbar").count() == 0)

    # 3. ETA appears once there is a pace to measure
    for card in page.locator(".card").all()[:6]:
        card.locator('button.vote[data-vote="approve"]').click()
        page.wait_for_timeout(1100)          # let the 1s clock tick attribute time
    page.wait_for_timeout(1200)
    eta = page.locator("#voteProgEta").inner_text()
    check("whole-set ETA is shown", bool(eta.strip()), " %r" % eta)
    check("ETA is about the whole set", "22" in eta, " %r" % eta)
    prog = page.locator("#voteProgText").inner_text()
    check("counter advanced", "6" in prog, " %r" % prog)

    # 4. auto-advance lands the card near the top, not the middle
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(900)
    active = page.locator(".card.kbd-active")
    if active.count():
        ab = active.bounding_box()
        check("advanced card sits near the top", ab and ab["y"] < 260, " y=%s" % (ab and round(ab["y"])))
    else:
        check("advanced card sits near the top", False, " (no kbd-active card)")

    check("no uncaught JS errors", errs == [], " %s" % errs[:1])
    browser.close()

httpd.shutdown()
print()
if fails:
    print("V17 SMOKE FAILED: %s" % ", ".join(fails))
    sys.exit(1)
print("V17 SMOKE PASS")
