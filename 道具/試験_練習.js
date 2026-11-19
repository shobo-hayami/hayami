// 練習問題の試験。1つでも違えば失敗で終わり、画面に練習問題の入口を出さない（早見の本体は出る）。
// 見ること: 画面の答え＝判定の結果／例題を入れ直して食い違わない／表の名前と単位がある／聞いた設備で質問が残らない／
// 段が決まる／線の問題が線ちょうどで要る・1つ手前で要らない／複合ビルの表に (16)イ・(16)ロ が出ない
const fs = require("fs"), path = require("path"), vm = require("vm");
const D = __dirname;
const ctx = { module: undefined, console };
vm.createContext(ctx);
for (const f of ["判定.js", "語.js", "練習.js"]) vm.runInContext(fs.readFileSync(path.join(D, f), "utf8"), ctx, { filename: f });
const 表たち = fs.readdirSync(path.join(D, "..", "判定表")).filter(f => f.endsWith(".json")).map(f => JSON.parse(fs.readFileSync(path.join(D, "..", "判定表", f), "utf8")));
const 例題 = JSON.parse(fs.readFileSync(path.join(D, "例題.json"), "utf8"));
const 境目 = JSON.parse(fs.readFileSync(path.join(D, "例題_境目.json"), "utf8"));
ctx.表たち = 表たち; ctx.例題 = 例題; ctx.境目 = 境目;
let ng = 0, n = 0;
const 違う = m => { ng++; console.log("違う: " + m); };

// 段が決まらない例題が無い（境目の例題は別のファイル）
for (const e of 例題) { n++; if (vm.runInContext(`練習の段を決める(${JSON.stringify(e)})`, ctx) === null) 違う("段が決まらない " + e.名前); }

const 問 = vm.runInContext("練習の問題を作る(例題, 境目, 表たち)", ctx);
let 行数 = 0;
for (const 段 of Object.keys(問)) for (const p of 問[段]) {
  const e = p.例;
  ctx.__e = e;
  const r = vm.runInContext("例題を入れる(__e)", ctx);
  n++; if (r.食い違い.length) 違う(`入れ直しで食い違う ${e.名前}: ${r.食い違い.join("・")}`);
  const 表 = vm.runInContext("練習の表(__e)", ctx);
  for (const x of 表) {
    n++; if (!x.名あり || !x.単位あり) 違う(`表の名前か単位が無い ${e.名前}: ${x.id}`);
    n++; if (/16イ|16ロ|\(16\)イ|\(16\)ロ|（16）/.test(x.名 + x.値)) 違う(`表に答えの手がかり ${e.名前}: ${x.名}`);
  }
  // 表に出した値と自動で入った値で、例題の答えが過不足なく戻る（この建物で聞かない質問の値は除く）
  for (const id of r.手) { n++; if (r.a[id] !== e.答え[id]) 違う(`表の値が答えと違う ${e.名前}: ${id}`); }
  if (段 === "線") {
    const res = vm.runInContext(`全部を判定(表たち.filter(t => t.設備 === ${JSON.stringify(p.設備)}), 例題を入れる(__e).a)[0]`, ctx);
    const m = res.境目 && res.境目.主, x = e.期待.主;
    n++; if (!m || m.名 !== x.名 || m.線 !== x.線 || m.号 !== x.号) 違う(`線の問題の線が例題と違う ${e.名前}`);
    continue;
  }
  for (const row of p.行) {
    行数++;
    const res = vm.runInContext(`全部を判定(表たち.filter(t => t.設備 === ${JSON.stringify(row.設備)}), 例題を入れる(__e).a)[0]`, ctx);
    n++; if (res.状態 !== row.期待) 違う(`画面の答えが判定と違う ${e.名前} / ${row.設備}: 期待 ${row.期待} → ${res.状態}`);
  }
  // 聞いた設備だけで、残る質問が無い
  const q = vm.runInContext(`次の質問(表たち.filter(t => ${JSON.stringify(p.行.map(x => x.設備))}.includes(t.設備)), 例題を入れる(__e).a)`, ctx);
  n++; if (q) 違う(`聞いた設備で質問が残る ${e.名前}: ${q.id}`);
}
const 数 = Object.keys(問).map(k => `${k}${問[k].length}`).join("・");
console.log(`練習問題 ${数}・設備の行 ${行数}・見たもの ${n}個・違い ${ng}個`);
process.exit(ng ? 1 : 0);
