# -*- coding: utf-8 -*-
"""Checks alchemy_constants.parse() against the real dashboard source (python test_alchemy_constants.py)."""
import io, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alchemy_constants as ac

DASH = r"C:\Claude\Personal\Project Alchemy\gold-flip-dashboard.html"
c = ac.parse(io.open(DASH, encoding="utf-8").read())
fails = []
def t(name, cond):
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond: fails.append(name)

t("elemetal_pamp is a negative dollar offset", c["elemetal_pamp"] < 0 and c["elemetal_pamp"] > -200)
t("elemetal_generic is a negative dollar offset", c["elemetal_generic"] < 0 and c["elemetal_generic"] > -200)
t("call-in bonus read", c["call_in_bonus"] == 10)
t("online premium read", c["online_prem"] == 10)
t("June seed read", c["june_seed"]["price"] > 500 and len(c["june_seed"]["t"]) >= 10)
t("sheet date is a date", len(c["sheet_date"]) == 10)
names = [x["name"] for x in c["cards"]]
t("six OWNED cards in order", len(names) == 6 and names[0] == "Chase Ink Business" and names[-1] == "Citi Double Cash")
sm = [x for x in c["cards"] if x["lc"] == "4037"][0]
t("Smartly 4037: 4% then 2%, limit 10k", sm["card"] == 4.0 and sm["alt_card"] == 2.0 and sm["limit"] == 10000)
t("Rinad's 6584 carries owner Rinad", [x for x in c["cards"] if x["lc"] == "6584"][0]["owner"] == "Rinad")
t("Costco Visa: 2% + Taekus 1.8%", [x for x in c["cards"] if x["lc"] == "6848"][0]["tk"] == 1.8)
t("no card has a number longer than last-4", all(x["lc"] is None or len(x["lc"]) == 4 for x in c["cards"]))
t("Smartly 4037 carries its closing date", sm["closed"] == "2026-10-27")
t("every other card is open", all(x["closed"] is None for x in c["cards"] if x["lc"] != "4037"))
try:
    ac.parse("nothing here"); t("missing source raises", False)
except ValueError:
    t("missing source raises, never a guess", True)
print("ALL PASS" if not fails else "%d FAILED" % len(fails))
sys.exit(1 if fails else 0)
