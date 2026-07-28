#!/usr/bin/env python3
# Build the brother's public index.html.
# Parts (in order): robots meta -> PIN curtain -> dashboard (with a tiny hook injected) -> Supabase live layer.
# The hook `window.__gfhIngest = applySheet;` is injected ONLY here, into the dashboard's final IIFE close,
# so the shared source file (Medi's artifact) stays byte-for-byte unchanged.

import io, os, subprocess

BASE = r"C:\Claude\Personal\Gold-Dashboard-Public"
DASH = r"C:\Claude\Personal\Project Alchemy\gold-flip-dashboard.html"

# ---------------------------------------------------------------------------
# CROSS-REPO GUARD
#
# This is the ONE place two separate workstreams touch. DASH lives in the
# Project Alchemy repo, which another Claude session edits; everything else the
# build reads lives here in Gold-Dashboard-Public. So the failure mode is
# specific and silent: run the build while that file is mid-edit and you
# publish somebody's half-finished work straight onto the brother's live page,
# with nothing on screen admitting it.
#
# Committed means "a human decided it was done". So: refuse to build from an
# uncommitted DASH. Set GFH_ALLOW_DIRTY=1 to override when you are deliberately
# testing an in-progress dashboard locally.
# ---------------------------------------------------------------------------
def _dash_uncommitted():
    try:
        r = subprocess.run(
            ["git", "-C", os.path.dirname(DASH), "status", "--porcelain", "--", os.path.basename(DASH)],
            capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception:
        return ""          # no git available -> never block the build on tooling

_dirty = _dash_uncommitted()
if _dirty and os.environ.get("GFH_ALLOW_DIRTY") != "1":
    raise SystemExit(
        "REFUSING TO BUILD - the dashboard source has uncommitted changes:\n"
        "    %s\n\n"
        "That file lives in the Project Alchemy repo and another session edits it.\n"
        "Building now would publish work someone has not finished to the live page.\n\n"
        "Do one of these:\n"
        "  1. Let the other session commit, then build again  (normal case)\n"
        "  2. GFH_ALLOW_DIRTY=1 python build-public.py        (deliberate local test)\n"
        % _dirty)

# charset MUST be in the first 1024 bytes or the browser guesses Latin-1 → mojibake (●·—✅ garble).
head   = '<!DOCTYPE html>\n<meta charset="utf-8">\n<meta name="robots" content="noindex,nofollow">\n'
pin    = io.open(os.path.join(BASE, "_pin-overlay.html"), encoding="utf-8").read()
dash   = io.open(DASH, encoding="utf-8").read()
live   = io.open(os.path.join(BASE, "_supabase-live.html"), encoding="utf-8").read()

# Inject the hook right before the LAST `})();` (the main IIFE close) in the dashboard only.
marker = "})();"
idx = dash.rfind(marker)
if idx == -1:
    raise SystemExit("ERROR: could not find the IIFE close `})();` in the dashboard.")
hook = "\n  window.__gfhIngest = applySheet;   // public-page ingest hook (build-injected; unused in the artifact)\n"
dash_patched = dash[:idx] + hook + dash[idx:]

# Safety checks
assert "window.__gfhIngest = applySheet;" in dash_patched, "hook not injected"
assert dash_patched.count(marker) == dash.count(marker), "IIFE count changed"

out = head + pin + dash_patched + live
with io.open(os.path.join(BASE, "index.html"), "w", encoding="utf-8", newline="\n") as f:
    f.write(out)

print("Built index.html: %d bytes (dash %d + pin %d + live %d)" % (len(out), len(dash), len(pin), len(live)))
print("Hook injected before char offset %d (of %d)." % (idx, len(dash)))
