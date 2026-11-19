// 例題（条文から手で出した答え）と、判定の仕組みの答えを突き合わせる。1件でも違えば失敗で終わる。
const fs = require("fs"), path = require("path");
const J = require("./判定.js");
const dir = path.join(__dirname, "..", "判定表");
const 表たち = fs.readdirSync(dir).filter(f => f.endsWith(".json")).map(f => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")));
const 例題 = JSON.parse(fs.readFileSync(path.join(__dirname, "例題.json"), "utf8"));
let ng = 0, n = 0;
for (const e of 例題) {
  const a = Object.assign({}, e.答え);
  J.自動で埋める(a); J.次の質問(表たち, a); // 自動で埋まる答えを埋める
  const res = J.全部を判定(表たち, a);
  for (const [k, v] of Object.entries(e.期待)) {
    n++;
    const r = res.find(x => x.設備 === k);
    if (!r || r.状態 !== v) { ng++; console.log(`違う: ${e.名前} / ${k}: 期待 ${v} → 出た ${r ? r.状態 : "なし"}` + (r && r.待ち.length ? `（待ち: ${r.待ち.map(w => w.要.join("・")).join(" / ")}）` : "")); }
  }
}
console.log(`例題 ${例題.length}件・見た答え ${n}個・違い ${ng}個`);
process.exit(ng ? 1 : 0);
