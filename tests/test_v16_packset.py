# -*- coding: utf-8 -*-
"""V16 (H2991) — packs of 10 sharing one record, and the public vote inbox.

W3 track B. A 320-card sheet is one file and one sitting nobody finishes, so a
long sheet now emits an index page plus `pack-NN.html` slices. The packs share
`sheet_id` — and therefore `STORE_KEY` — so pack 2 already knows what pack 1
decided, while each pack's own export still names only its slice.

The inbox half pushes ids+verdicts to a public repo and pulls them back on load.
These tests pin what a PUBLIC repo is allowed to receive: no card text, no
markup, no over-long note, and nothing at all from a sheet flagged
`personal_data`.

On the device flow, measured 18-08-2026 and pinned in `test_inbox_*_disabled*`:
GitHub sends no `Access-Control-Allow-Origin` on `login/device/code`, so a
static page cannot complete the exchange without a CORS-capable relay. The
button therefore stays disabled until BOTH `client_id` and `device_url` are
configured — shipping an enabled control that cannot succeed would be worse than
shipping none.
"""
import json
import re
import shutil
import subprocess

import pytest

from csl_pyutil import render_review_sheet_packset
from csl_pyutil.review_sheet import RU_UI_STRINGS, UI_STRINGS

from test_review_sheet import _config, _items, render_review_sheet


def _n_items(n):
    """n cards with stable ids, so a slice is checkable by id."""
    return [{"id": "R%03d" % i, "filt": "a", "title": "item %d" % i,
             "question": "Is card %d right?" % i, "panels": []}
            for i in range(1, n + 1)]


def _screening():
    return {"deterministic": 1, "lookup": 0, "agent": 0, "human": 1,
            "evidence_path": "tests/fixture_screening.md", "rules": ["r"]}


def _packset(items, **overrides):
    return render_review_sheet_packset(items, _config(**overrides),
                                       screening=_screening())


def _ids_in(html):
    return re.findall(r'<section class="card" data-id="([^"]+)"', html)


# --------------------------------------------------------------------- B1 split

def test_ten_items_is_one_file_no_parent():
    out = _packset(_n_items(10))
    assert out["parent"] is None
    assert len(out["packs"]) == 1


def test_ten_items_is_byte_identical_to_a_plain_render():
    """Splitting a sheet that fits would cost a click and buy nothing."""
    items = _n_items(10)
    packed = _packset(items)["packs"][0]
    plain = render_review_sheet(items, _config(), screening=_screening())
    assert packed == plain


def test_eleven_items_is_parent_plus_two_packs():
    out = _packset(_n_items(11))
    assert out["parent"] is not None
    assert len(out["packs"]) == 2
    assert [len(_ids_in(p)) for p in out["packs"]] == [10, 1]


def test_twentytwo_items_is_parent_plus_three_packs_last_short():
    out = _packset(_n_items(22))
    assert len(out["packs"]) == 3
    assert [len(_ids_in(p)) for p in out["packs"]] == [10, 10, 2]


def test_packs_partition_the_items_in_order():
    items = _n_items(22)
    out = _packset(items)
    seen = [i for p in out["packs"] for i in _ids_in(p)]
    assert seen == [it["id"] for it in items]


def test_every_pack_carries_the_same_sheet_id():
    """One sheet_id -> one STORE_KEY -> pack 2 sees what pack 1 decided."""
    out = _packset(_n_items(22))
    for pack in out["packs"]:
        assert 'var SHEET_ID = "test-sheet_scope";' in pack
    assert 'var SHEET_ID = "test-sheet_scope";' in out["parent"]


def test_pack_export_names_only_its_own_slice():
    out = _packset(_n_items(22))
    tail = json.loads(re.search(r"var ids = (\[.*?\]);", out["packs"][2]).group(1))
    assert tail == ["R021", "R022"]


def test_custom_pack_size():
    out = _packset(_n_items(9), pack_size=4)
    assert [len(_ids_in(p)) for p in out["packs"]] == [4, 4, 1]


@pytest.mark.parametrize("bad", [0, -1])
def test_pack_size_must_be_positive(bad):
    with pytest.raises(ValueError, match="pack_size"):
        _packset(_n_items(5), pack_size=bad)


def test_pack_size_must_be_an_int():
    with pytest.raises(TypeError, match="pack_size"):
        _packset(_n_items(5), pack_size=2.5)


# --------------------------------------------------------------------- parent page

def test_parent_links_every_pack_under_the_hub_name():
    out = render_review_sheet_packset(_n_items(22), _config(), screening=_screening(),
                                      hub_name="h2991_demo")
    for name in ("pack-01", "pack-02", "pack-03"):
        assert 'href="h2991_demo/%s.html"' % name in out["parent"]


def test_parent_hub_name_defaults_to_sheet_id():
    out = _packset(_n_items(11))
    assert 'href="test-sheet_scope/pack-01.html"' in out["parent"]


def test_parent_knows_each_packs_ids_for_progress():
    out = _packset(_n_items(22))
    packs = json.loads(re.search(r"var PACKS = (\[.*?\]);", out["parent"]).group(1))
    assert [len(p["ids"]) for p in packs] == [10, 10, 2]
    assert [p["name"] for p in packs] == ["01", "02", "03"]


def test_parent_carries_no_card_content():
    """The index is an index: no questions, no panels, nothing to vote on."""
    out = _packset(_n_items(22))
    assert "Is card 1 right?" not in out["parent"]
    assert 'class="card"' not in out["parent"]


def test_parent_is_stamped_with_the_generator_version():
    from csl_pyutil import __version__
    out = _packset(_n_items(11))
    assert 'content="csl-pyutil/%s"' % __version__ in out["parent"]


# --------------------------------------------------------------------- B2 inbox

_INBOX = {"repo": "gasyoun/vote-inbox", "client_id": "Iv1.demo",
          "device_url": "https://relay.example/device"}


def test_inbox_absent_by_default():
    """No github_inbox key -> not one V16 inbox identifier in the document."""
    out = _packset(_n_items(11))
    for ident in ("inboxBtn", "__inboxPut", "__inboxHydrate", "var INBOX ="):
        assert ident not in out["packs"][0]
        assert ident not in out["parent"]


def test_inbox_button_present_when_configured():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    assert 'id="inboxBtn"' in out["packs"][0]
    assert "__inboxHydrate();" in out["packs"][0]


def test_inbox_enabled_needs_both_client_id_and_relay():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    inbox = json.loads(re.search(r"var INBOX = (\{.*?\});", out["packs"][0]).group(1))
    assert inbox["enabled"] is True


@pytest.mark.parametrize("missing", ["client_id", "device_url"])
def test_inbox_disabled_when_half_configured(missing):
    """Measured 18-08-2026: github.com/login/device/* sends no CORS header, so
    without a relay the exchange cannot complete. Half a config is disabled."""
    cfg = dict(_INBOX)
    cfg[missing] = ""
    out = _packset(_n_items(11), github_inbox=cfg)
    inbox = json.loads(re.search(r"var INBOX = (\{.*?\});", out["packs"][0]).group(1))
    assert inbox["enabled"] is False
    assert "__inboxBtn.disabled = true;" in out["packs"][0]


def test_inbox_disabled_still_ships_the_pack_layer():
    """«Код пакетов всё равно кораблится» — a missing OAuth app is not a stop."""
    out = _packset(_n_items(22), github_inbox={"client_id": "", "device_url": ""})
    assert len(out["packs"]) == 3
    assert 'id="inboxBtn"' in out["packs"][0]


def test_each_pack_writes_its_own_inbox_file():
    out = _packset(_n_items(22), github_inbox=_INBOX)
    names = [json.loads(re.search(r"var INBOX = (\{.*?\});", p).group(1))["pack_name"]
             for p in out["packs"]]
    assert names == ["01", "02", "03"]
    assert "'decisions/' + encodeURIComponent(SHEET_ID) + '/pack-' + INBOX.pack_name" \
        in out["packs"][0]


def test_inbox_requests_public_repo_scope_only():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    assert "scope: 'public_repo'" in out["packs"][0]
    assert "'repo'" not in re.search(r"__inboxDeviceToken[\s\S]*?\n  \}",
                                     out["packs"][0]).group(0)


@pytest.mark.parametrize("key", ["client_secret", "token", "secret"])
def test_inbox_refuses_any_secret(key):
    with pytest.raises(ValueError, match=key):
        _packset(_n_items(11), github_inbox=dict(_INBOX, **{key: "s3cret"}))


def test_no_client_secret_anywhere_in_the_output():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    for doc in out["packs"] + [out["parent"]]:
        assert "client_secret" not in doc


def test_inbox_repo_must_be_owner_slash_name():
    with pytest.raises(ValueError, match="owner/name"):
        _packset(_n_items(11), github_inbox=dict(_INBOX, repo="justaname"))


# --------------------------------------------------------------------- personal data

def test_personal_data_removes_the_github_button():
    out = _packset(_n_items(11), github_inbox=_INBOX, personal_data=True)
    for ident in ("inboxBtn", "__inboxPut", "__inboxHydrate", "var INBOX ="):
        assert ident not in out["packs"][0]


def test_personal_data_still_packs():
    """Removing the inbox must not remove the reason the sheet was split."""
    out = _packset(_n_items(22), github_inbox=_INBOX, personal_data=True)
    assert len(out["packs"]) == 3
    assert out["parent"] is not None


def test_personal_data_must_be_a_bool():
    with pytest.raises(TypeError, match="personal_data"):
        _packset(_n_items(11), personal_data="yes")


# --------------------------------------------------------------------- note hygiene

def test_note_rules_are_pinned_in_the_emitted_guard():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    js = out["packs"][0]
    assert "if (note.length > 280) return false;" in js
    assert "if (note.indexOf('<') >= 0) return false;" in js
    assert "if (q && q.length > 12 && note.indexOf(q) >= 0) return false;" in js


def test_inbox_payload_carries_ids_and_verdicts_not_card_text():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    body = re.search(r"function __inboxPayload\(\) \{[\s\S]*?\n  \}", out["packs"][0]).group(0)
    assert "out = { id: it.id, decision: it.decision }" in body
    for leaked in ("title", "question", "panels", "filt"):
        assert leaked not in body


def test_inbox_reuses_export_payload_rather_than_the_item_literal():
    """The trap H2858/H2887 paid for: never re-emit `note: rec.note || ''`."""
    out = _packset(_n_items(11), github_inbox=_INBOX)
    js = re.search(r"var INBOX = [\s\S]*?__inboxHydrate\(\);", out["packs"][0]).group(0)
    assert "JSON.parse(exportPayload())" in js
    assert "rec.note ||" not in js


def test_inbox_layer_probes_no_neighbour_with_typeof():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    js = re.search(r"var INBOX = [\s\S]*?__inboxHydrate\(\);", out["packs"][0]).group(0)
    assert "typeof" not in js


def test_card_questions_map_is_scoped_to_the_pack():
    out = _packset(_n_items(22), github_inbox=_INBOX)
    q = json.loads(re.search(r"var CARD_Q = (\{.*?\});", out["packs"][2]).group(1))
    assert sorted(q) == ["R021", "R022"]


# --------------------------------------------------------------------- B3 hydrate

def test_hydrate_reads_the_public_contents_api_without_a_token():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    hydrate = re.search(r"function __inboxHydrate\(\)[\s\S]*?\n  \}", out["packs"][0]).group(0)
    assert "https://api.github.com/repos/" in out["packs"][0]
    assert "Authorization" not in hydrate


def test_hydrate_lets_the_inbox_win_on_conflict():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    assert "state[it.id].decision = it.decision;" in out["packs"][0]


def test_hydrate_ignores_ids_outside_this_pack():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    assert "if (!it.decision || ids.indexOf(it.id) < 0) return;" in out["packs"][0]


# --------------------------------------------------------------------- localization

def test_ru_preset_translates_every_inbox_string():
    out = _packset(_n_items(11), github_inbox=_INBOX, ui_strings=RU_UI_STRINGS)
    js = out["packs"][0]
    assert "Сохранить в GitHub" in js
    assert "Save to GitHub" not in js
    assert "pulled {n} vote(s) from GitHub" not in js


def test_ru_preset_keeps_the_inbox_placeholders():
    out = _packset(_n_items(11), github_inbox=_INBOX, ui_strings=RU_UI_STRINGS)
    assert "{n}" in re.search(r"var INBOX_HYDRATED = '([^']*)';", out["packs"][0]).group(1)
    assert "{pack}" in re.search(r"var INBOX_SAVED = '([^']*)';", out["packs"][0]).group(1)
    code = re.search(r"var INBOX_CODE = '([^']*)';", out["packs"][0]).group(1)
    assert "{url}" in code and "{code}" in code


def test_every_new_ui_strings_key_has_a_russian_value():
    inbox_keys = {k for k in UI_STRINGS if k.startswith("inbox_")}
    assert inbox_keys, "V16 must register its chrome in UI_STRINGS"
    assert inbox_keys <= set(RU_UI_STRINGS)


# --------------------------------------------------------------------- script purity

@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("cfg", [
    {},
    {"github_inbox": _INBOX},
    {"github_inbox": dict(_INBOX, client_id="")},
    {"github_inbox": _INBOX, "personal_data": True},
    {"github_inbox": _INBOX, "ui_strings": RU_UI_STRINGS},
    {"github_inbox": _INBOX, "timing": False, "hand_in": False, "session_flow": False},
])
def test_emitted_pack_script_parses(tmp_path, cfg):
    out = _packset(_n_items(22), **cfg)
    for label, doc in (("pack", out["packs"][0]), ("parent", out["parent"])):
        script = "\n".join(re.findall(r"<script>([\s\S]*?)</script>", doc))
        f = tmp_path / ("%s.js" % label)
        f.write_text(script, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, "%s: %s" % (label, r.stderr)


def test_pack_and_parent_have_balanced_script_tags():
    out = _packset(_n_items(22), github_inbox=_INBOX)
    for doc in out["packs"] + [out["parent"]]:
        assert doc.count("<script>") == doc.count("</script>")
        assert doc.startswith("<!DOCTYPE html>")


# --------------------------------------------------------------------- branch default (0.17.1)

def test_inbox_names_no_branch_by_default():
    """0.17.0 defaulted to 'main' and gasyoun/vote-inbox is on `master`, so the
    first real save would have 404'd. Omitting `branch` lets the contents API
    resolve the repo's own default."""
    out = _packset(_n_items(11), github_inbox=_INBOX)
    inbox = json.loads(re.search(r"var INBOX = (\{.*?\});", out["packs"][0]).group(1))
    assert inbox["branch"] == ""
    assert "if (INBOX.branch) msg.branch = INBOX.branch;" in out["packs"][0]


def test_inbox_honours_an_explicit_branch():
    out = _packset(_n_items(11), github_inbox=dict(_INBOX, branch="master"))
    inbox = json.loads(re.search(r"var INBOX = (\{.*?\});", out["packs"][0]).group(1))
    assert inbox["branch"] == "master"


def test_inbox_read_omits_ref_when_no_branch_is_named():
    out = _packset(_n_items(11), github_inbox=_INBOX)
    assert "INBOX.branch ? '?ref=' + encodeURIComponent(INBOX.branch) : ''" in out["packs"][0]
