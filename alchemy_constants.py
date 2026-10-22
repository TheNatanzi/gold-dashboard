# -*- coding: utf-8 -*-
"""
alchemy_constants.py - read the numbers Sabz needs out of gold-flip-dashboard.html.

build-public.py calls parse(dash) on every publish and upserts the result into the gold DB
table alchemy_constants (migration 032). Sabz's buyingPower.ts reads that row instead of its
hand copies. Every value is read from the source; a missing value raises, never a guess.

Test: python test_alchemy_constants.py
"""
import re

def _num(pat, s, label):
    m = re.search(pat, s)
    if not m:
        raise ValueError("alchemy_constants: could not find " + label)
    return float(m.group(1))

def _buyer_offset(s, key):
    return _num(r'\{key:"' + re.escape(key) + r'",[^}]*?offset:\s*(-?\d+(?:\.\d+)?)', s, key + " offset")

def _owned(s):
    i = s.find("const OWNED = [")
    if i < 0:
        raise ValueError("alchemy_constants: could not find OWNED")
    j = s.find("];", i)
    block = s[i:j]
    cards = []
    for m in re.finditer(r'\{name:"([^"]+)"(.*?)(?=\n\s*\{name:"|\Z)', block, re.S):
        name, rest = m.group(1), m.group(2)
        def f(k, cast=float, req=True):
            mm = re.search(r'\b' + k + r':\s*"?([^",}\s]+)"?', rest)
            if not mm:
                if req:
                    raise ValueError("alchemy_constants: card %s has no %s" % (name, k))
                return None
            return cast(mm.group(1))
        alt = re.search(r'alt:\{card:\s*(\d+(?:\.\d+)?)', rest)
        owner = None
        if "Rinad" in name:
            owner = "Rinad"
        cards.append({
            "name": name,
            "lc": f("lc", str, False),
            "net": f("net", str),
            "card": f("card"),
            "tk": f("tk"),
            "alt_card": float(alt.group(1)) if alt else None,
            "type": f("type", str),
            "limit": f("limit"),
            "owner": owner,
        })
    if not cards:
        raise ValueError("alchemy_constants: OWNED parsed empty")
    return cards

def parse(s):
    sheet = re.search(r'var ELEM_SHEET_DATE = "(\d{4}-\d{2}-\d{2})"', s)
    june = re.search(r'junePrice:(\d+(?:\.\d+)?), juneTime:"([^"]+)"', s)
    if not sheet or not june:
        raise ValueError("alchemy_constants: sheet date or June seed missing")
    return {
        "elemetal_pamp": _buyer_offset(s, "elemetal_pamp"),
        "elemetal_generic": _buyer_offset(s, "elemetal_generic"),
        "call_in_bonus": _num(r'const CALL_IN_BONUS = (\d+(?:\.\d+)?);', s, "CALL_IN_BONUS"),
        "online_prem": _num(r'onlinePrem:(\d+(?:\.\d+)?)', s, "onlinePrem"),
        "june_seed": {"price": float(june.group(1)), "t": june.group(2)},
        "sheet_date": sheet.group(1),
        "cards": _owned(s),
    }
