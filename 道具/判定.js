// 判定の表を引いて、設備ごとに 要る／要らない／条件次第／判定できない を出す。AIは使わない。
// 画面（早見.html に埋め込み）と試験（node 試験_判定.js）の両方で同じものを使う。

var 質問 = [
  { id: "宿泊", 文: "利用者を入居・宿泊させる？", 型: "はい", 出す: function (a) { return /^6[ハ]/.test(a.用途); } },
  { id: "介助主", 文: "介助がなければ避難できない人を主として入所させる？", 型: "はい", 出す: function (a) { return /^6ロ[245]$/.test(a.用途); } },
  { id: "火気", 文: "火を使う設備や器具がある？（防火上有効な措置をしたものは除く）", 型: "はい", 出す: function (a) { return /^3/.test(a.用途); } },
  { id: "延べ", 文: "延べ面積は何㎡？", 型: "数" },
  { id: "地上", 文: "地上の階数は？（地階を除く）", 型: "数" },
  { id: "地下", 文: "地階の階数は？（無ければ0）", 型: "数" },
  { id: "床_地階無窓", 文: "地階か無窓階のうち、一番広い階の床面積は何㎡？（どちらも無ければ0）", 型: "数" },
  { id: "床_3階", 文: "3階の床面積は何㎡？", 型: "数", 自動: function (a) { return a.地上 !== undefined && a.地上 !== null && a.地上 < 3 ? 0 : undefined; } },
  { id: "床_11以上", 文: "11階以上のうち、一番広い階の床面積は何㎡？（11階以上が無ければ0）", 型: "数", 自動: function (a) { return a.地上 !== undefined && a.地上 !== null && a.地上 < 11 ? 0 : undefined; } },
  { id: "床_4以上", 文: "4階〜10階のうち、一番広い階の床面積は何㎡？（4階以上が無ければ0）", 型: "数", 自動: function (a) { return a.地上 !== undefined && a.地上 !== null && a.地上 < 4 ? 0 : undefined; } },
  { id: "構造", 文: "建物の造りは？（耐火＝耐火建築物、準耐火＝準耐火建築物）", 型: "選ぶ", 選択: ["耐火", "準耐火", "その他"] },
  { id: "内装", 文: "壁と天井の内装は難燃材料（またはそれ以上）？", 型: "はい" },
  { id: "収容", 文: "建物全体の収容人員は何人？", 型: "数" },
  { id: "収容_地階無窓", 文: "地階と無窓階の収容人員は合わせて何人？", 型: "数", 自動: function (a) { return a.床_地階無窓 === 0 ? 0 : undefined; } },
  { id: "収容_階最大", 文: "2階以上の階か地階のうち、収容人員が一番多い階は何人？（避難階と11階以上は除く）", 型: "数", 自動: function (a) { return a.地上 === 1 && a.地下 === 0 ? 0 : undefined; } },
  { id: "直通1", 文: "3階以上の階か地階（避難階は除く）から、避難階か地上へ直通する階段が1つしかない？（その1つが屋外階段か、避難上有効な構造の階段なら「いいえ」）", 型: "はい", 自動: function (a) { return typeof a.地上 === "number" && a.地上 <= 2 && a.地下 === 0 ? false : undefined; } },
  { id: "収容_3階以上地階最大", 文: "3階以上の階か地階のうち、収容人員が一番多い階は何人？（避難階と11階以上は除く。そういう階が無ければ0）", 型: "数", 自動: function (a) { return typeof a.地上 === "number" && a.地上 < 3 && a.地下 === 0 ? 0 : undefined; } },
  { id: "収容_直通1階", 文: "避難階か地上へ直通する階段が2つ以上ない階（3階以上。二項・三項は2階以上。避難階と11階以上は除く）のうち、収容人員が一番多い階は何人？（そういう階が無ければ0）", 型: "数", 自動: function (a) { if (typeof a.地上 !== "number") return undefined; if (a.地上 <= 1) return 0; var u = a.用途 || ""; if (a.地上 === 2 && !(/^[23]/.test(u) || (u === "16イ" && (!複合か(a) || 派生.二三あり(a))))) return 0; return undefined; } },
  // 第2段（残り11設備）で足した質問
  { id: "床_1と2階", 文: "1階と2階の床面積の合計は何㎡？（平屋なら1階だけ）", 型: "数", 自動: function (a) { return (a.地上 === 1 || a.地上 === 2) && a.地下 === 0 && typeof a.延べ === "number" ? a.延べ : undefined; } },
  { id: "床_地階合計", 文: "地階の床面積の合計は何㎡？", 型: "数", 自動: function (a) { return a.地下 === 0 ? 0 : undefined; } },
  { id: "延べ_地上", 文: "地階を除いた延べ面積は何㎡？", 型: "数", 自動: function (a) { return a.地下 === 0 && typeof a.延べ === "number" ? a.延べ : undefined; } },
  { id: "敷地", 文: "敷地の面積は何㎡？", 型: "数" },
  { id: "高さ31超", 文: "建物の高さは31mを超える？", 型: "はい" },
  { id: "鉄網", 文: "壁・床・天井に、下地（間柱・根太・野縁など）が準不燃材料でない鉄網入り（ラスモルタルなど）のものがある？", 型: "はい" },
  { id: "契約50超", 文: "電気の契約電流容量（契約が複数なら一番大きいもの）は50アンペアを超える？", 型: "はい" },
  { id: "特殊部分", 文: "次のどれかの部分がある？ 駐車場・自動車の修理や整備の場所・発電機や変圧器の部屋・ボイラー室など火を多く使う部屋・通信機器室・屋上のヘリポート・車が通る道路の部分", 型: "はい", 自動: function (a) { return a.用途 === "13イ" ? true : undefined; } },
  { id: "危険物類", 文: "少量危険物（指定数量の5分の1以上で指定数量未満の危険物）か、指定可燃物（危険物の規制に関する政令 別表第4の数量以上）を貯蔵・取り扱う？", 型: "はい" },
  // 「判定できない」を減らすために足した質問（効くときだけ出る）
  { id: "指可倍_全部", 文: "指定可燃物は、危険物の規制に関する政令 別表第4の数量の何倍？（可燃性液体類も入れた数。指定可燃物が無ければ0）", 型: "数", 補足: "品名が2つ以上あるときの数え方は、管轄の決まりで", 出す: function (a) { return a.危険物類 === true; } },
  { id: "指可倍_液除く", 文: "そのうち、可燃性液体類を除いた指定可燃物は何倍？（無ければ0）", 型: "数", 出す: function (a) { return a.危険物類 === true; } },
  { id: "省令部分", 文: "手術室・分娩室・透析室・レントゲン室などのうち、防火の区画をした部分の床面積は、合わせて何㎡？（無ければ0）", 型: "数", 補足: "数えるのは、規則13条の5の2に当たる部分だけ。準耐火構造の壁・床と防火戸で区画した部分か、不燃材料の壁・柱・床・天井と戸で区画し、隣が全部スプリンクラーの有効範囲内の部分。床面積1,000㎡以上の地階・無窓階と、1,500㎡以上の4階〜10階にある部分は数えない", 出す: function (a) { return /^6イ[12]$|^6ロ/.test(a.用途 || ""); } },
  { id: "床_舞台部", 文: "舞台部の床面積は何㎡？（舞台と、舞台につながった大道具室・小道具室の合計。舞台が無ければ0）", 型: "数", 出す: function (a) { return /^1/.test(a.用途 || "") && !/^1[0-9]/.test(a.用途 || ""); } },
  { id: "舞台_地階無窓4階", 文: "その舞台は、地階・無窓階・4階以上の階のどれかにある？", 型: "はい", 出す: function (a) { return /^1[イロ]/.test(a.用途 || ""); }, 自動: function (a) { return typeof a.地上 === "number" && a.地上 < 4 && a.床_地階無窓 === 0 ? false : undefined; } },
  { id: "ラック10m超", 文: "天井の高さが10mを超えるラック式倉庫？（ラック式倉庫＝棚などを設け、昇降機で収納物を運ぶ装置を備えた倉庫。天井が無ければ屋根の下面までの高さ）", 型: "はい", 出す: function (a) { return a.用途 === "14"; } },
  { id: "床特_準地下街", 文: "特定用途の部分（一項〜四項・五項イ・六項・九項イ）の床面積は、合わせて何㎡？", 型: "数", 出す: function (a) { return a.用途 === "16の3"; } },
  { id: "収容_無窓3階以上地階最大", 文: "地階か、3階以上の無窓階のうち、収容人員が一番多い階は何人？（避難階と11階以上は除く。そういう階が無ければ0）", 型: "数", 出す: function (a) { return /^12|^15$/.test(a.用途 || ""); }, 自動: function (a) { if (a.床_地階無窓 === 0) return 0; if (typeof a.地上 === "number" && a.地上 < 3 && typeof a.収容_3階以上地階最大 === "number") return a.収容_3階以上地階最大; return undefined; } },
  { id: "地下街_六項イロ", 文: "地下街の中に、六項イ(1)・(2)（病院・有床診療所の一部）か六項ロ（特別養護老人ホームなど）の用途の部分がある？", 型: "はい", 出す: function (a) { return a.用途 === "16の2"; } },
  { id: "地下街_自火報の部分", 文: "地下街の中に、二項ニ（カラオケボックスなど）・五項イ（旅館・ホテルなど）・六項イ(1)〜(3)・六項ロ・利用者を入居か宿泊させる六項ハの用途の部分がある？", 型: "はい", 出す: function (a) { return a.用途 === "16の2"; } },
  // 複合ビル（16項イ）の建物全体で聞く質問（令9条かっこ書きの号に効く）
  { id: "特定_避難階以外", 文: "特定用途の部分（一項〜四項・五項イ・六項・九項イ）が、3階以上の階か地階にある？", 型: "はい", 出す: function (a) { return 複合イか(a); }, 自動: function (a) { return typeof a.地上 === "number" && a.地上 <= 2 && a.地下 === 0 ? false : undefined; } },
  { id: "床23_地階無窓", 文: "地階か無窓階のうち、二項・三項の部分の床面積の合計が一番大きい階では、その合計は何㎡？（そういう階が無ければ0）", 型: "数", 出す: function (a) { return 複合イか(a) && 派生.二三あり(a); }, 自動: function (a) { return a.床_地階無窓 === 0 ? 0 : undefined; } },
  { id: "床特_地階無窓", 文: "地階か無窓階のうち、特定用途の部分（一項〜四項・五項イ・六項・九項イ）が一番広い階では、その部分は何㎡？（そういう階が無ければ0）", 型: "数", 出す: function (a) { return 複合イか(a); }, 自動: function (a) { return a.床_地階無窓 === 0 ? 0 : undefined; } },
  { id: "床特_4以上", 文: "4階〜10階のうち、特定用途の部分（一項〜四項・五項イ・六項・九項イ）が一番広い階では、その部分は何㎡？（無ければ0）", 型: "数", 出す: function (a) { return 複合イか(a); }, 自動: function (a) { return typeof a.地上 === "number" && a.地上 < 4 ? 0 : undefined; } },
  { id: "床特_地階合計", 文: "地階にある特定用途の部分（一項〜四項・五項イ・六項・九項イ）の床面積の合計は何㎡？（地階が無ければ0）", 型: "数", 出す: function (a) { return 複合イか(a); }, 自動: function (a) { return a.地下 === 0 ? 0 : undefined; } },
  { id: "床特_4以上_二四階", 文: "4階〜10階のうち、二項か四項の部分がある階で、特定用途の部分（一項〜四項・五項イ・六項・九項イ）が一番広い階では、その部分は何㎡？（そういう階が無ければ0）", 型: "数", 出す: function (a) { return 複合イか(a) && 派生.二四あり(a); }, 自動: function (a) { return typeof a.地上 === "number" && a.地上 < 4 ? 0 : undefined; } },
  // 複合ビルの部分ごとに聞く質問（令25条1項1号・2号のかっこ書き）
  { id: "下階特定", 文: "この部分がある階より下の階に、一項〜四項・九項・十二項イ・十三項イ・十四項・十五項の部分がある？", 型: "はい", 部分だけ: true, 出す: function (o) { return /^[56]/.test(o.用途); }, 自動: function (o) { if (!o._親) return false; return o._親.部分.some(function (p, j) { return j !== o._i && 用途に当たる(["1*", "2*", "3*", "4", "9*", "12イ", "13イ", "14", "15"], p.用途); }) ? undefined : false; } }
];
// 複合ビルでは文を替える質問
(function () {
  var 替え = {
    延べ: "延べ面積は何㎡？（用途の部分の合計に、廊下・階段などの共用部分も足した面積）",
    収容: "建物全体の収容人員は何人？（全部の用途の部分の合計）",
    収容_直通1階: "避難階か地上へ直通する階段が2つ以上ない階（3階以上。2階に二項・三項の部分があれば2階以上。避難階と11階以上は除く）のうち、収容人員が一番多い階は何人？（そういう階が無ければ0）"
  };
  質問.forEach(function (q) { if (替え[q.id]) q.文_複合 = 替え[q.id]; });
})();

var 不明 = "わからない";
var 自動で入れた = {}; // 階数などから機械が入れた答え（画面で「自動」と出す）

function 用途に当たる(tokens, code) {
  for (var i = 0; i < tokens.length; i++) {
    var t = tokens[i];
    if (t === "*") return true;
    if (t.slice(-1) === "*") {
      var p = t.slice(0, -1);
      if (code.indexOf(p) === 0) {
        var nx = code.charAt(p.length);
        if (!/^[0-9]+$/.test(p) || (!/[0-9]/.test(nx) && nx !== "の")) return true;
      }
    } else if (t === code) return true;
  }
  return false;
}

function 値(a, name) {
  // 答えと、答えから出せる値
  if (name.indexOf("max:") === 0) {
    var xs = name.slice(4).split(","), m = -1;
    for (var i = 0; i < xs.length; i++) {
      var v = 値(a, xs[i]);
      if (v === undefined || v === null || v === 不明) return v === 不明 ? 不明 : undefined;
      if (v > m) m = v;
    }
    return m;
  }
  if (name === "平屋以外") {
    if (a.地上 === undefined || a.地上 === 不明) return a.地上;
    if (a.地上 >= 2) return true;
    if (a.地下 === undefined || a.地下 === 不明) return a.地下;
    return a.地下 >= 1 ? 不明 : false; // 地上1階・地階ありは平屋かどうか条文だけでは決めない
  }
  if (派生[name] && 複合か(a)) return 派生[name](a);
  if (name === "下階特定" && !a._親) return false; // 用途が1つの建物では、下の階に別の用途は無い
  return a[name];
}

function 倍率(a) {
  if (a.構造 === undefined || a.構造 === 不明) return a.構造;
  if (a.構造 === "その他") return 1;
  if (a.内装 === undefined || a.内装 === 不明) return a.内装;
  if (a.構造 === "耐火") return a.内装 ? 3 : 2;
  return a.内装 ? 2 : 1; // 準耐火
}

// 条件1つ: true / false / null（まだ） / 不明
function 条件を見る(c, a, row) {
  var name = c[0], op = c[1], v = c[2];
  var x = 値(a, name);
  if (x === undefined || x === null || x === 不明) {
    // 複合ビルの部分などは、建物の値が上限になる。上限が線に届かなければ聞かずに決まる
    var ub = 上限(a, name);
    if (typeof ub === "number") {
      var 線0 = op === ">=倍" && row && row.特例 ? Math.min(v, 1000) : v;
      if ((op === ">=" || op === ">=倍") && ub < 線0) return { r: false };
      if (op === ">" && ub <= v) return { r: false };
      if (op === "<" && ub < v) return { r: true };
    }
  }
  if (x === undefined || x === null) return { r: null, 要: [name] };
  if (x === 不明) return { r: 不明, 要: [name] };
  if (op === ">=倍") {
    if (x < v) return { r: false }; // 倍率は1以上なので、倍にする前の線より小さければ造りを聞かずに外れる
    var f = 倍率(a);
    if (f === undefined || f === null) return { r: null, 要: ["構造", "内装"] };
    if (f === 不明) return { r: 不明, 要: ["構造", "内装"] };
    var hi = v * f;
    if (row.特例 && f > 1) {
      // 令11条2項かっこ書き: 3倍（2倍）の数値と「1,000㎡＋規則13条の5の2の部分（延べ面積の2分の1まで）」の小さい方
      var lo = Math.min(hi, 1000), cap = Math.min(hi, 2000), X = 値(a, "省令部分");
      if (typeof X === "number") { var L = Math.min(hi, 1000 + X, 2000); return { r: x >= L, 線: L, 倍: f, 線文: L === hi ? null : (L === 2000 ? "省令で定める部分は延べ面積の2分の1まで（規則13条の5の2）。2,000㎡で判定（令11条2項）" : "1,000㎡＋省令で定める部分" + X + "㎡＝" + L + "㎡で判定（令11条2項）") }; }
      if (x >= cap) return { r: true };
      if (x < lo) return { r: false };
      if (X === undefined || X === null) return { r: null, 要: ["省令部分"] };
      return { r: 不明, 要: ["省令部分"], 説明: "六項ロなどは「1,000㎡＋省令で定める部分の床面積」と比べた小さい方で読む（令11条2項）。その部分の床面積しだい" };
    }
    return { r: x >= hi, 線: hi, 倍: f };
  }
  if (op === ">=") return { r: x >= v };
  if (op === ">") return { r: x > v };
  if (op === "<") return { r: x < v };
  if (op === "==") return { r: x === v };
  return { r: 不明 };
}

// ---- 複合ビル（16項イ・ロ）: 令9条により、用途ごとの部分を1つの建物とみなして判定する ----
// 答えの形: a.部分 = [{用途:"3ロ", 延べ:800}, …]。部分ごとの答えは "p0_収容" のように p{番号}_ を付けて平らに持つ。
// 判定表の行に "令9" が付いた行（令9条かっこ書きの号と、建物の値で決まる号）だけ建物全体で1回判定し、ほかは部分ごとに判定する。
var 特定の用途 = ["1*", "2*", "3*", "4", "5イ", "6*", "9イ"];
var 引き継ぐ = ["構造", "内装", "地上", "地下", "鉄網", "契約50超", "敷地", "高さ31超", "直通1", "特殊部分", "危険物類", "指可倍_全部", "指可倍_液除く"];
var 部分の問 = ["宿泊", "介助主", "火気", "床_地階無窓", "床_3階", "床_11以上", "床_4以上", "収容", "収容_地階無窓", "収容_階最大", "収容_3階以上地階最大", "収容_直通1階", "床_1と2階", "床_地階合計", "延べ_地上", "下階特定", "省令部分", "床_舞台部", "舞台_地階無窓4階", "ラック10m超", "収容_無窓3階以上地階最大"];
var 部分の文 = {
  床_地階無窓: "地階か無窓階のうち、この部分が一番広い階では、その部分は何㎡？（無ければ0）",
  床_3階: "3階にあるこの部分は何㎡？（無ければ0）",
  床_11以上: "11階以上のうち、この部分が一番広い階では、その部分は何㎡？（無ければ0）",
  床_4以上: "4階〜10階のうち、この部分が一番広い階では、その部分は何㎡？（無ければ0）",
  収容: "この部分の収容人員は何人？",
  収容_地階無窓: "地階と無窓階にあるこの部分の収容人員は、合わせて何人？（無ければ0）",
  収容_階最大: "2階以上の階か地階のうち、この部分の収容人員が一番多い階では何人？（避難階と11階以上は除く。無ければ0）",
  収容_3階以上地階最大: "3階以上の階か地階のうち、この部分の収容人員が一番多い階では何人？（避難階と11階以上は除く。無ければ0）",
  床_1と2階: "1階と2階にあるこの部分の床面積の合計は何㎡？",
  床_地階合計: "地階にあるこの部分の床面積の合計は何㎡？（無ければ0）",
  延べ_地上: "地階を除いた、この部分の床面積の合計は何㎡？",
  床_舞台部: "この部分の舞台部の床面積は何㎡？（舞台と、舞台につながった大道具室・小道具室の合計。舞台が無ければ0）",
  省令部分: "この部分の手術室・分娩室・透析室・レントゲン室などのうち、防火の区画をした部分の床面積は、合わせて何㎡？（無ければ0）",
  収容_無窓3階以上地階最大: "地階か、3階以上の無窓階のうち、この部分の収容人員が一番多い階では何人？（避難階と11階以上は除く。無ければ0）"
};
var 複合の上限 = { 床特_4以上_二四階: ["特定面積", "床特_4以上"], 床23_地階無窓: ["二三面積", "床_地階無窓"], 床特_地階無窓: ["特定面積", "床_地階無窓"], 床特_4以上: ["特定面積", "床_4以上"], 床特_地階合計: ["特定面積", "床_地階合計"] };
var 上限の表 = { 床_舞台部: ["延べ"], 床特_準地下街: ["延べ"], 指可倍_液除く: ["指可倍_全部"], 収容_無窓3階以上地階最大: ["収容_3階以上地階最大", "収容_地階無窓"] };
// 令11条2項かっこ書きの読み替え（六項イ(1)(2)・ロの屋内消火栓2号と、それを準用する行）。11階以上の建物は令12条1項3号の建物で1号の建物から除かれるので使わない
function 特例か(表, row, a) { return /^6イ[12]$|^6ロ/.test(a.用途 || "") && !(typeof a.地上 === "number" && a.地上 >= 11) && ((表.設備 === "屋内消火栓" && row.号 === "令11条1項2号") || !!row.倍特例); }
var すき間の理由 = "建物全体では線を超えるが、用途ごとの部分ではどれも超えない。令9条は用途ごとに判定すると書いている。建物全体でも判定するかは条文に書いていないので、管轄で確かめる";

function 合計(a, toks) { var s = 0; (a.部分 || []).forEach(function (p) { if (用途に当たる(toks, p.用途)) s += p.延べ; }); return s; }
var 派生 = {
  特定面積: function (a) { return 合計(a, 特定の用途); },
  二三面積: function (a) { return 合計(a, ["2*", "3*"]); },
  二三あり: function (a) { return a.部分.some(function (p) { return 用途に当たる(["2*", "3*"], p.用途); }); },
  二四あり: function (a) { return a.部分.some(function (p) { return 用途に当たる(["2*", "4"], p.用途); }); },
  一項あり: function (a) { return a.部分.some(function (p) { return 用途に当たる(["1*"], p.用途); }); }
};
function 複合か(a) { return !!(a && a.部分 && a.部分.length); }
function 複合イか(a) { return 複合か(a) && a.用途 === "16イ"; }
function 複合の用途(部分) { return 部分.some(function (p) { return 用途に当たる(特定の用途, p.用途); }) ? "16イ" : "16ロ"; }
function 部分の名(a, i) { var c = a.部分[i].用途; return (typeof 用途の名 !== "undefined" && 用途の名[c]) ? 用途の名[c] : c; }

function 部分の答(a, i) {
  var p = a.部分[i], o = { 用途: p.用途, 延べ: p.延べ, _親: a, _i: i }, pre = "p" + i + "_";
  引き継ぐ.forEach(function (k) { if (a[k] !== undefined) o[k] = a[k]; });
  Object.keys(a).forEach(function (k) { if (k.indexOf(pre) === 0) o[k.slice(pre.length)] = a[k]; });
  return o;
}

// 答えが無いときに使える上限。部分の面積は部分の延べ面積と建物のその階の値を、部分の人数は建物の人数を超えない
function 上限(a, name) {
  if (name.indexOf("max:") === 0) {
    var xs = name.slice(4).split(","), m = -1;
    for (var i = 0; i < xs.length; i++) { var x = 値(a, xs[i]); var u = typeof x === "number" ? x : 上限(a, xs[i]); if (typeof u !== "number") return undefined; if (u > m) m = u; }
    return m;
  }
  var ns = [];
  if (a._親) {
    var b = a._親[name];
    if (/^床_|^延べ_地上$/.test(name)) { ns.push(a.延べ); if (typeof b === "number") ns.push(b); }
    else if (/^収容/.test(name)) { if (typeof b === "number") ns.push(b); if (typeof a._親.収容 === "number") ns.push(a._親.収容); if (name !== "収容" && typeof a.収容 === "number") ns.push(a.収容); }
  } else if (複合か(a) && 複合の上限[name]) {
    var xs2 = 複合の上限[name]; ns.push(値(a, xs2[0])); if (typeof a[xs2[1]] === "number") ns.push(a[xs2[1]]);
  }
  // 用途が1つの建物でも使う上限（舞台部は延べ面積を超えない、など）
  (上限の表[name] || []).forEach(function (k) { var u = 値(a, k); if (typeof u === "number") ns.push(u); });
  return ns.length ? Math.min.apply(null, ns) : undefined;
}

// 1行を見る: {種: "要る"|"待ち"|"できない"|"注記"|null, …}
function 行を見る(表, row, a) {
  if (!用途に当たる(row.用途, a.用途)) return { 種: null };
  if (row.結果 === "注記") return { 種: "注記", row: row };
  if (row.結果 === "判定できない") {
    var hit = true, nd = [];
    (row.条件 || []).forEach(function (c) { var r = 条件を見る(c, a, row); if (r.r === false) hit = false; else if (r.r !== true) { if (hit) hit = null; nd = nd.concat(r.要 || []); } });
    if (hit === true) return { 種: "できない", row: row };
    if (hit === null) return { 種: "待ち", row: row, 要: nd, 説明: [] };
    return { 種: null };
  }
  if (特例か(表, row, a)) row = Object.assign({}, row, { 特例: true });
  var ok = true, need = [], 説明 = [], 線 = [];
  for (var i = 0; i < row.条件.length; i++) {
    var r = 条件を見る(row.条件[i], a, row);
    if (r.r === false) { ok = false; break; }
    if (r.r !== true) { ok = null; need = need.concat(r.要 || []); if (r.説明) 説明.push(r.説明); }
    if (r.線文) 線.push(r.線文); else if (r.線 && r.倍 > 1) 線.push("構造と内装により基準を" + r.倍 + "倍に読み替え（" + r.線 + "㎡で判定）");
  }
  if (ok === true) return { 種: "要る", row: Object.assign({ 線: 線 }, row) };
  if (ok === null) return { 種: "待ち", row: row, 要: need, 説明: 説明 };
  return { 種: null };
}

function 状態を決める(要る, 待ち, できない) { return 要る.length ? "要る" : 待ち.length ? "条件次第" : できない.length ? "判定できない" : "要らない"; }

// 待ちの質問の名前を、実際に聞く質問のidにする（部分の質問は p{番号}_ を付ける）
function 聞くid(n, i) {
  var xs = n.indexOf("max:") === 0 ? n.slice(4).split(",") : n === "平屋以外" ? ["地上", "地下"] : [n];
  return xs.map(function (x) { return (i === undefined || 部分の問.indexOf(x) < 0) ? x : "p" + i + "_" + x; });
}

function 設備を判定(表, a) {
  var 要る = [], 待ち = [], できない = [], 注記 = [], 候補 = (表.候補 || []).slice(), 内訳 = null;
  if (!複合か(a)) {
    表.行.forEach(function (row) {
      var x = 行を見る(表, row, a);
      if (x.種 === "要る") 要る.push(x.row); else if (x.種 === "待ち") 待ち.push({ row: x.row, 要: x.要, 説明: x.説明 });
      else if (x.種 === "できない") できない.push(x.row); else if (x.種 === "注記") 注記.push(x.row);
    });
  } else {
    内訳 = [];
    var 組 = [{ どこ: "建物全体", 答: a, 行: 表.行.filter(function (r) { return r.令9; }), i: undefined }];
    a.部分.forEach(function (p, i) { 組.push({ どこ: 部分の名(a, i) + "の部分", 答: 部分の答(a, i), 行: 表.行.filter(function (r) { return !r.令9; }), i: i }); });
    var 当たり = {}; // 部分ごとの行の結果（すき間を見るため）
    組.forEach(function (g) {
      var 要 = [], 待 = [], 不 = [];
      g.行.forEach(function (row) {
        var x = 行を見る(表, row, g.答);
        if (g.i !== undefined && x.種) { var k = 表.行.indexOf(row); 当たり[k] = 当たり[k] || {}; 当たり[k][x.種] = true; }
        if (x.種 === "要る") 要.push(Object.assign({ どこ: g.どこ }, x.row));
        else if (x.種 === "待ち") 待.push({ row: x.row, 要: [].concat.apply([], (x.要 || []).map(function (n) { return 聞くid(n, g.i); })), 説明: x.説明, どこ: g.どこ });
        else if (x.種 === "できない") 不.push(Object.assign({ どこ: g.どこ }, x.row));
        else if (x.種 === "注記" && g.i === undefined) 注記.push(x.row);
      });
      要る = 要る.concat(要); 待ち = 待ち.concat(待); できない = できない.concat(不);
      内訳.push({ どこ: g.どこ, 状態: 状態を決める(要, 待, 不), 要る: 要, 待ち: 待, できない: 不 });
    });
    // 部分の注記は、部分の用途で当たるものを1回だけ
    表.行.forEach(function (row, k) { if (!row.令9 && row.結果 === "注記" && 当たり[k] && 当たり[k].注記 && 注記.indexOf(row) < 0) 注記.push(row); });
    // すき間: 全部の用途にかかる号で、どの部分も当たらないのに建物全体では当たる
    表.行.forEach(function (row, k) {
      if (row.令9 || (row.結果 && row.結果 !== "要る") || row.用途.indexOf("*") < 0) return;
      var h = 当たり[k] || {};
      if (h.要る || h.待ち) return;
      var x = 行を見る(表, row, a);
      var 全 = 内訳[0];
      if (x.種 === "要る") { var y = Object.assign({ どこ: "建物全体" }, row, { 理由: すき間の理由 }); できない.push(y); 全.できない.push(y); 全.状態 = 状態を決める(全.要る, 全.待ち, 全.できない); }
      else if (x.種 === "待ち") { var w = { row: row, 要: [].concat.apply([], x.要.map(function (n) { return 聞くid(n); })), 説明: [], どこ: "建物全体" }; 待ち.push(w); 全.待ち.push(w); 全.状態 = 状態を決める(全.要る, 全.待ち, 全.できない); }
    });
  }
  var 状態 = 状態を決める(要る, 待ち, できない);
  if (状態 === "要らない" && 表.未収録 && 表.未収録.length) {
    状態 = "判定できない";
    できない.push({ 号: 表.条[0] + "の" + 表.未収録.join("・") + "号", 理由: "判定表にまだ入れていない号がある" });
  }
  要る.forEach(function (r) { if (r.候補 && 候補.indexOf(r.候補) < 0) 候補.push(r.候補); });
  return { 設備: 表.設備, 状態: 状態, 要る: 要る, 待ち: 待ち, できない: できない, 注記: 注記, 候補: 候補, 札: 表.札, 変わった: 表.変わった || [], 内訳: 内訳, 既存: 既存の印(表.設備, a.用途), 境目: 状態 === "要らない" ? 境目を出す(表, a) : null };
}

// ---- 境目までの距離: 「要らない」の設備に、ほかの答えを変えずにその値だけ増えたら「要る」になる線を出す。状態は変えない ----
var 切替の名 = ["宿泊", "介助主", "火気", "平屋以外", "鉄網", "契約50超", "高さ31超", "直通1", "特定_避難階以外", "危険物類", "下階特定", "ラック10m超", "舞台_地階無窓4階", "地下街_六項イロ", "地下街_自火報の部分"];
var 近いの切り = 0.3; // 残りが線の3割以内を「近い」とする（仮の値。使ってみて直す）
function 行の境目(表, row0, a, どこ) {
  if (!用途に当たる(row0.用途, a.用途) || (row0.結果 && row0.結果 !== "要る")) return null;
  var row = row0;
  if (特例か(表, row, a)) row = Object.assign({}, row, { 特例: true });
  var F = [], U = [];
  row.条件.forEach(function (c) { var r = 条件を見る(c, a, row); if (r.r === false) F.push(c); else if (r.r !== true) U.push(c); });
  if (F.length !== 1) return null; // 2つ以上外れた行は、その値だけ増えても要るにならない
  if (U.length) return { 未: true, 号: row.号, 名: U.map(function (c) { return c[0]; }), どこ: どこ };
  var c = F[0], name = c[0], op = c[1], v = c[2];
  if (op === "==") return (v === true && 切替の名.indexOf(name) >= 0 && (name !== "下階特定" || a._親)) ? { 種: "切替", 名: name, 号: row.号, どこ: どこ } : null;
  if (op === "<") return null; // 減らすと要るになる線は出さない
  var x = 値(a, name);
  if (typeof x !== "number") return null; // 部分の値を聞かずに決まったときなど、今の値が分からない
  var L = v, 種 = "数", 倍 = null;
  if (op === ">=倍") {
    倍 = 倍率(a);
    if (typeof 倍 !== "number") return null; // 造りと内装を聞かずに外れたときは、線が決まらない
    L = v * 倍;
    if (row.特例 && 倍 > 1) { var X = 値(a, "省令部分"); if (typeof X === "number") L = Math.min(L, 1000 + X, 2000); else { L = Math.min(L, 1000); 種 = "場合あり"; } }
  }
  if (op === ">") 種 = "超";
  for (var i = 0; i < row.条件.length; i++) { var d = row.条件[i]; if (d !== c && d[0] === name && d[1] === "<" && !(L < d[2])) return null; }
  return { 種: 種, 名: name, 今: x, 線: L, あと: L - x, 比: L ? (L - x) / L : 1, 倍: 倍, 元: v, 号: row.号, 範囲: row.範囲, 理由: row.理由, どこ: どこ };
}
function 境目を出す(表, a) {
  var out = [];
  function 足す(x) { if (!x) return; var k = [x.種, x.名, x.線, x.号, x.どこ].join("|"); if (!out.some(function (y) { return [y.種, y.名, y.線, y.号, y.どこ].join("|") === k; })) out.push(x); }
  if (!複合か(a)) 表.行.forEach(function (r) { 足す(行の境目(表, r, a)); });
  else {
    表.行.filter(function (r) { return r.令9; }).forEach(function (r) { 足す(行の境目(表, r, a, "建物全体")); });
    a.部分.forEach(function (p, i) {
      var o = 部分の答(a, i);
      表.行.filter(function (r) { return !r.令9; }).forEach(function (r) {
        var x = 行の境目(表, r, o, 部分の名(a, i) + "の部分");
        if (x && !x.未 && 引き継ぐ.concat(["平屋以外"]).indexOf(x.名) >= 0) x.どこ = "建物全体"; // 建物から引き継ぐ値は1本にまとめる
        足す(x);
      });
    });
    // すき間: 全部の用途にかかる号を建物全体の値でも見る（越えると「判定できない」に変わる）
    表.行.filter(function (r) { return !r.令9 && r.結果 === "要る" && r.用途.indexOf("*") >= 0; }).forEach(function (r) { var x = 行の境目(表, r, a, "建物全体"); if (x && !x.未 && x.種 !== "切替") { x.すき間 = true; 足す(x); } });
  }
  var 未 = out.filter(function (x) { return x.未; }), 切替 = [], 数 = [];
  out.forEach(function (x) { if (x.未) return; if (x.種 === "切替") { if (!切替.some(function (y) { return y.名 === x.名 && y.どこ === x.どこ; })) 切替.push(x); } else 数.push(x); });
  // 主の線: 今の値が0でない数の線。同じ値の線は一番低いものだけ。線に対する残りの割合が小さい順
  var 候補 = 数.filter(function (x) { return !x.すき間 && x.今 > 0 && (x.種 === "数" || x.種 === "場合あり"); });
  候補 = 候補.filter(function (x) { return !候補.some(function (y) { return y !== x && y.名 === x.名 && y.どこ === x.どこ && y.線 < x.線; }); });
  候補.sort(function (p, q) { return p.比 - q.比; });
  var 主 = 候補[0] || null;
  var 近すき間 = 数.filter(function (x) { return x.すき間 && x.今 > 0 && (!主 || x.比 < 主.比); });
  var ほか = 数.filter(function (x) { return x !== 主 && 近すき間.indexOf(x) < 0; });
  if (!主 && !近すき間.length && !切替.length && !ほか.length && !未.length) return null;
  return { 主: 主, すき間: 近すき間, 切替: 切替, ほか: ほか, 未: 未, 近い: !!(主 && 主.比 <= 近いの切り) };
}

// ---- 既存の建物の印（消防法17条の2の5・令34条・令34条の4）。判定の状態は変えない ----
// A＝前から建っている建物にも今の基準／B＝前の基準を当てはめる場合がある。複合ビルは建物の用途（16イ・16ロ）で決める
var 既存_特定 = ["1*", "2*", "3*", "4", "5イ", "6*", "9イ", "16イ", "16の2", "16の3"]; // 特定防火対象物（法17条の2の5第2項4号・令34条の4）
var 既存_設備 = { 消火器: "消防法17条の2の5第1項・令34条1号", 避難器具: "消防法17条の2の5第1項", ガス漏れ: "令34条4号", 漏電: "令34条5号", 非常警報: "令34条6号", 誘導灯: "令34条7号" };
function 既存の印(設備, 用途) {
  if (typeof 既存の変わった !== "undefined" && 既存の変わった.length) return { 印: "見直し中" };
  if (!用途) return null;
  if (既存_設備[設備]) return { 印: "A", 理由: "設備", 根拠: 既存_設備[設備] };
  if (設備 === "自動火災報知" && (用途に当たる(既存_特定, 用途) || 用途 === "17")) return { 印: "A", 理由: "設備", 根拠: "令34条3号" };
  if (用途に当たる(既存_特定, 用途)) return { 印: "A", 理由: "用途", 根拠: "消防法17条の2の5第2項4号・令34条の4" };
  return { 印: "B", 根拠: "消防法17条の2の5第1項" };
}

function 全部を判定(表たち, a) {
  return 表たち.map(function (t) { return 設備を判定(t, a); });
}

function 質問の文(q, a) { return 複合か(a) && q.文_複合 ? q.文_複合 : q.文; }
function 部分の質問(a, i, q) {
  return { id: "p" + i + "_" + q.id, 文: "〔" + 部分の名(a, i) + "の部分〕" + (部分の文[q.id] || q.文), 型: q.型, 選択: q.選択, 部分: i, 元: q.id };
}
// id から質問を引く（部分の質問は p{番号}_ 付き）
function 質問を引く(id, a) {
  var m = /^p(\d+)_(.+)$/.exec(id);
  for (var j = 0; j < 質問.length; j++) {
    var q = 質問[j];
    if (m && q.id === m[2] && a && a.部分 && a.部分[+m[1]]) return 部分の質問(a, +m[1], q);
    if (!m && q.id === id) return Object.assign({}, q, { 文: 質問の文(q, a) });
  }
  return null;
}
function 名前(id, a) {
  var q = 質問を引く(id, a);
  return q ? q.文 : id;
}

// 階数などから決まる答えを、決まるだけ全部入れる（部分の答えも）
function 自動で埋める(a) {
  var moved = true;
  while (moved) {
    moved = false;
    質問.forEach(function (q) {
      if (q.部分だけ || a[q.id] !== undefined || !q.自動 || (q.出す && !q.出す(a))) return;
      var v = q.自動(a); if (v !== undefined) { a[q.id] = v; 自動で入れた[q.id] = true; moved = true; }
    });
    if (!複合か(a)) continue;
    a.部分.forEach(function (p, i) {
      var o = 部分の答(a, i);
      部分の問.forEach(function (id) {
        var pid = "p" + i + "_" + id; if (a[pid] !== undefined) return;
        var q = null; 質問.forEach(function (x) { if (x.id === id) q = x; });
        if (!q || (q.出す && !q.出す(o))) return;
        var v = 上限(o, id) === 0 ? 0 : q.自動 ? q.自動(o) : undefined;
        if (v !== undefined) { a[pid] = v; o[id] = v; 自動で入れた[pid] = true; moved = true; }
      });
    });
  }
}

// 次に聞く質問: まだ決まっていない設備の判定に効く質問だけ
function 次の質問(表たち, a) {
  if (!a.用途) return null;
  if (複合か(a)) 自動で埋める(a);
  var res = 全部を判定(表たち, a), 効く = {};
  res.forEach(function (r) { if (r.状態 === "条件次第") r.待ち.forEach(function (w) { w.要.forEach(function (n) { 効く[n] = true; }); }); });
  // max: の中身や、平屋以外は元の質問に分ける
  if (効く["平屋以外"]) { 効く.地上 = true; 効く.地下 = true; }
  Object.keys(効く).forEach(function (k) { if (k.indexOf("max:") === 0) k.slice(4).split(",").forEach(function (x) { 効く[x] = true; }); });
  if (複合か(a)) {
    // 部分の値は建物の値が上限。先に建物の値を聞くと、部分を聞かずに決まることが多い
    Object.keys(効く).forEach(function (k) {
      var m = /^p\d+_(.+)$/.exec(k); if (m && 部分の問.indexOf(m[1]) >= 0 && m[1] !== "下階特定" && !/^(宿泊|介助主|火気)$/.test(m[1]) && a[m[1]] === undefined) 効く[m[1]] = true;
      if (複合の上限[k] && a[複合の上限[k][1]] === undefined) 効く[複合の上限[k][1]] = true;
    });
  }
  for (var i = 0; i < 質問.length; i++) {
    var q = 質問[i];
    if (q.部分だけ || a[q.id] !== undefined) continue;
    if (q.出す && !q.出す(a)) continue;
    if (q.自動) { var v = q.自動(a); if (v !== undefined) { a[q.id] = v; 自動で入れた[q.id] = true; return 次の質問(表たち, a); } }
    if (効く[q.id]) return 質問を引く(q.id, a);
  }
  if (複合か(a)) {
    for (var pi = 0; pi < a.部分.length; pi++) {
      for (var j = 0; j < 部分の問.length; j++) {
        var pid = "p" + pi + "_" + 部分の問[j];
        // 建物のその値を「わからない」と答えたときは、部分の値も分からないとみて聞かない（設備の画面からは答えられる）
        if (a[部分の問[j]] === 不明 && !/^(宿泊|介助主|火気|下階特定)$/.test(部分の問[j])) continue;
        if (a[pid] === undefined && 効く[pid]) return 質問を引く(pid, a);
      }
    }
  }
  return null;
}

if (typeof module !== "undefined") module.exports = { 既存の印: 既存の印, 質問: 質問, 全部を判定: 全部を判定, 次の質問: 次の質問, 不明: 不明, 名前: 名前, 質問を引く: 質問を引く, 自動で埋める: 自動で埋める, 複合の用途: 複合の用途, 部分の答: 部分の答 };
