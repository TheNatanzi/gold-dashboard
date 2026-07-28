#!/usr/bin/env python3
# Build the brother's public index.html.
# Parts (in order): robots meta -> PIN curtain -> dashboard (with a tiny hook injected) -> Supabase live layer.
# The hook `window.__gfhIngest = applySheet;` is injected ONLY here, into the dashboard's final IIFE close,
# so the shared source file (Medi's artifact) stays byte-for-byte unchanged.

import io, os

BASE = r"C:\Claude\Personal\Gold-Dashboard-Public"
DASH = r"C:\Claude\Personal\Project Alchemy\gold-flip-dashboard.html"

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
