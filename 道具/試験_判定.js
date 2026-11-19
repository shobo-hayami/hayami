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
// 既存の建物の印: 条文から手で出した期待（消防法17条の2の5・令34条・令34条の4）
const 既存の例 = [["15","屋内消火栓","B"],["15","消火器","A"],["15","自動火災報知","B"],["17","自動火災報知","A"],["17","屋内消火栓","B"],["5ロ","誘導灯","A"],["5ロ","スプリンクラー","B"],["6ロ1","スプリンクラー","A"],["16イ","屋内消火栓","A"],["16ロ","自動火災報知","B"],["12イ","漏電","A"],["12イ","避難器具","A"],["12イ","非常警報","A"],["7","ガス漏れ","A"],["13ロ","特殊消火","B"],["16の2","無線通信補助","A"],["16の3","排煙","A"],["9イ","連結送水管","A"],["9ロ","連結送水管","B"]];
for (const [u, e, x] of 既存の例) { n++; const m = J.既存の印(e, u); if (!m || m.印 !== x) { ng++; console.log(`違う: 既存の印 ${u} / ${e}: 期待 ${x} → 出た ${m && m.印}`); } }
// 総当たり: 6設備はどの用途でもA／特定の用途はどの設備でもA／自動火災報知は特定か17でA／ほかはB
const 特定 = c => /^(1[イロ]|2[イロハニ]|3[イロ]|6[イロハニ])/.test(c) || ["4","5イ","9イ","16イ","16の2","16の3"].includes(c);
const 全A = ["消火器","避難器具","漏電","非常警報","誘導灯","ガス漏れ"];
const 用途たち = ["1イ","1ロ","2イ","2ロ","2ハ","2ニ","3イ","3ロ","4","5イ","5ロ","6イ1","6イ2","6イ3","6イ4","6ロ1","6ロ2","6ロ3","6ロ4","6ロ5","6ハ1","6ハ2","6ハ3","6ハ4","6ハ5","6ニ","7","8","9イ","9ロ","10","11","12イ","12ロ","13イ","13ロ","14","15","16イ","16ロ","16の2","16の3","17","18","19","20"];
for (const t of 表たち) for (const u of 用途たち) {
  n++;
  const x = 全A.includes(t.設備) || 特定(u) || (t.設備 === "自動火災報知" && u === "17") ? "A" : "B";
  const m = J.既存の印(t.設備, u);
  if (!m || m.印 !== x) { ng++; console.log(`違う: 既存の印の総当たり ${u} / ${t.設備}: 期待 ${x} → 出た ${m && m.印}`); }
}
// 境目までの距離: 主の線（名・線・あと・号・どこ）と、近いかどうか
const 境目の例 = JSON.parse(fs.readFileSync(path.join(__dirname, "例題_境目.json"), "utf8"));
for (const e of 境目の例) {
  n++;
  const a = JSON.parse(JSON.stringify(e.答え)); J.自動で埋める(a); J.次の質問(表たち, a);
  const b = J.全部を判定(表たち.filter(t => t.設備 === e.設備), a)[0].境目, x = e.期待;
  let ok = true;
  if (x === null) ok = !b || !b.主;
  else {
    if (x.主 === null) ok = !b || !b.主; else ok = !!(b && b.主) && ["名", "線", "あと", "号"].every(k => b.主[k] === x.主[k]) && (!x.主.どこ || (x.主.どこ === "部分0" ? /の部分$/.test(b.主.どこ) : b.主.どこ === x.主.どこ));
    if (x.近い !== undefined && b) ok = ok && b.近い === x.近い;
    if (x.未あり) ok = ok && !!b && b.未.length > 0;
    if (x.切替) ok = ok && !!b && x.切替.every(k => b.切替.some(y => y.名 === k));
    if (x.すき間) ok = ok && !!b && b.すき間.some(y => ["名", "線", "あと", "号"].every(k => y[k] === x.すき間[k]));
  }
  if (!ok) { ng++; console.log(`違う: ${e.名前} / ${e.設備}: 期待 ${JSON.stringify(x)} → 出た ${JSON.stringify(b && b.主)}`); }
}
// 境目の総当たり: 全部の例題で、主の線の値をちょうど線にすると「要らない」でなくなる（線の1つ手前は要らないのまま）
let 境目を試した = 0;
for (const e of 例題.concat(境目の例.map(x => ({ 名前: x.名前, 答え: x.答え })))) {
  const a0 = JSON.parse(JSON.stringify(e.答え)); J.自動で埋める(a0); J.次の質問(表たち, a0);
  for (const r of J.全部を判定(表たち, a0)) {
    const m = r.境目 && r.境目.主; if (!m || /^max:/.test(m.名) || (m.どこ && m.どこ !== "建物全体")) continue;
    if (["延べ", "地上", "地下", "特定面積", "二三面積"].includes(m.名)) continue; // 階数・延べ面積は自動で入る値が連れて動き、特定面積などは部分の面積から出すので、ここでは見ない
    const t = 表たち.filter(x => x.設備 === r.設備);
    const a1 = JSON.parse(JSON.stringify(e.答え)); a1[m.名] = m.線; J.自動で埋める(a1); J.次の質問(表たち, a1);
    const s1 = J.全部を判定(t, a1)[0].状態;
    n++; 境目を試した++;
    if (s1 === "要らない") { ng++; console.log(`違う: 境目の総当たり ${e.名前} / ${r.設備}: ${m.名}を${m.線}にしても要らない`); }
  }
}
console.log(`例題 ${例題.length}件・境目 ${境目の例.length}件（線ちょうどで変わるか ${境目を試した}件）・見た答え ${n}個・違い ${ng}個`);
process.exit(ng ? 1 : 0);
