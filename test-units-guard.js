// ============================================================================
// Regression test for the 2026-07-28 units bug.
//
//   node test-units-guard.js
//   (portable node lives at C:\dev\tools\node-v24.18.0-win-x64\node.exe)
//
// WHAT WENT WRONG: gold_prices.premium is the scraper's premium over SPOT as a
// PERCENT — it reads `([\d.]+)%` straight off the Costco listing, so 2.9 means
// 2.9%. CFG.onlinePrem is a DOLLAR figure: how much cheaper the register is than
// the web listing, $10 by Medi's own measurement. The live layer mapped one onto
// the other, so implied-in-store came out as 4159.99 − 2.90 = $4157.09 instead
// of − $10 = $4149.99. That invented a $7.10 disagreement with June's quote and
// pushed BUY $7.10 high, making every $/bar figure ~$6.86 too pessimistic. No
// exception was thrown anywhere.
//
// WHY A RANGE CHECK CANNOT SAVE US: $2.90 is a perfectly sane dollar amount. The
// value was never the problem — the UNIT was. So the guard declares units rather
// than checking magnitudes, and this file proves the guard actually fires by
// replaying the real bad payload through it.
//
// This lifts the guard out of _supabase-live.html rather than duplicating it, so
// the test cannot drift away from the shipped code.
// ============================================================================
const fs = require("fs");
const path = require("path");

const page = fs.readFileSync(path.join(__dirname, "_supabase-live.html"), "utf8");
const src = /<script>([\s\S]*)<\/script>/.exec(page)[1];

function lift(name, kind) {
  const start = src.indexOf((kind === "var" ? "var " : "function ") + name);
  if (start < 0) throw new Error("could not find " + name + " in _supabase-live.html");
  let depth = 0, end = -1;
  for (let j = src.indexOf("{", start); j < src.length; j++) {
    if (src[j] === "{") depth++;
    else if (src[j] === "}") { depth--; if (!depth) { end = j + 1; break; } }
  }
  return src.slice(start, end) + (kind === "var" ? ";" : "");
}

let mBuyText = "";
const fakeEl = (id) => (id === "mBuy" ? { textContent: mBuyText } : null);
const { guardIngest, checkBuyPrice } = new Function("el", [
  lift("INGEST_CONTRACT", "var"),
  lift("INGEST_FORBIDDEN", "var"),
  lift("guardIngest", "fn"),
  lift("checkBuyPrice", "fn"),
  "return { guardIngest, checkBuyPrice };",
].join("\n"))(fakeEl);

let pass = 0, fail = 0;
const t = (name, cond, detail) => {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; console.log("  FAIL  " + name + (detail ? "  -> " + detail : "")); }
};

console.log("\n--- 1. the actual bug: a percent sent as online_premium ---");
let m = { online_price: { v: "4159.99" }, online_premium: { v: "2.9" } };
let bad = guardIngest(m);
t("online_premium is stripped from the map", m.online_premium === undefined);
t("and it is reported, not silent", bad.length === 1, JSON.stringify(bad));
t("the reason names PERCENT vs DOLLARS", /PERCENT/.test(bad[0]) && /DOLLARS/.test(bad[0]), bad[0]);
t("the good key survives", m.online_price !== undefined);

console.log("\n--- 2. any brand-new undeclared key ---");
m = { some_future_field: { v: "123" } };
bad = guardIngest(m);
t("undeclared key stripped", m.some_future_field === undefined);
t("and reported", bad.length === 1 && /no declared unit/.test(bad[0]), JSON.stringify(bad));

console.log("\n--- 3. a normal healthy payload passes untouched ---");
m = { june_price: { v: "4139.99" }, gold_spot: { v: "4050.10" },
      online_price: { v: "4159.99" }, online_instock: { v: "yes" } };
bad = guardIngest(m);
t("no complaints", bad.length === 0, JSON.stringify(bad));
t("all four keys kept", Object.keys(m).length === 4);

console.log("\n--- 4. a price that is obviously not a gold price ---");
m = { gold_spot: { v: "2.9" } };
bad = guardIngest(m);
t("$2.90 rejected as a spot price", m.gold_spot === undefined && bad.length === 1, JSON.stringify(bad));

console.log("\n--- 5. checkBuyPrice: the end-to-end money assertion ---");
const online = { price: 4159.99 }, june = { price: 4139.99 };
mBuyText = "$4,157.09";                       // <-- exactly what the bug produced
t("catches the buggy BUY of $4157.09", checkBuyPrice(online, june) !== null,
  String(checkBuyPrice(online, june)));
mBuyText = "$4,149.99";                       // online - $10, correct
t("accepts online minus $10", checkBuyPrice(online, june) === null);
mBuyText = "$4,139.99";                       // June's register price, also legal
t("accepts June's price", checkBuyPrice(online, june) === null);
mBuyText = "$4,200.00";
t("catches an out-of-nowhere BUY", checkBuyPrice(online, june) !== null);

console.log("\n=======================================");
console.log(fail === 0 ? `ALL ${pass} CHECKS PASSED` : `${pass} passed, ${fail} FAILED`);
console.log("=======================================");
process.exit(fail === 0 ? 0 : 1);
