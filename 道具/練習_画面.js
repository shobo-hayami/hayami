// ---- 練習問題の画面（早見の UI に埋め込む）。記録は画面を開いている間だけ持ち、端末に残さず、外へ送らない ----
var 練習問 = null, 練習 = { 段: null, 並び: [], 位置: 0, 下書き: {}, 記録: {} };
// 例題を入れる は自動で入れた値の印を作り直すので、早見の答えの印を守って呼ぶ
function 練守る(fn){ var k = 自動で入れた; var r = fn(); 自動で入れた = k; return r; }
function 練入れる(e){ return 練守る(function(){ return 例題を入れる(e); }); }
function 練習の問題(){ if(!練習問) 練習問 = 練守る(function(){ return 練習の問題を作る(練習の例題, 練習の境目, 表たち); }); return 練習問; }
function 練習のキー(p){ return p.段 + p.番号; }
function 練習の今(pos){ return 練習の問題()[練習.段][練習.並び[pos]]; }
function 練習の名(p){ return 練習の段[p.段].名 + ' ' + p.番号 + '／' + 練習の問題()[p.段].length; }
function 練習の設備名(e){
  var t = 表たち.filter(function(x){ return x.設備 === e; })[0], k = t && t.条 && t.条[0], s = null;
  if(k && 条文[k]){ var m = /（([^）]+)）/.exec(条文[k].split('\n')[0]); if(m) s = m[1].replace(/に関する基準$/, '').replace(/を設置すべき防火対象物$/, ''); }
  return e + (k ? '（' + (s ? s + '・' : '') + 条を読む(k) + '）' : '');
}
function 練習を始める(段, 混ぜる, から){
  var ps = 練習の問題()[段], idx = ps.map(function(p, i){ return i; });
  if(混ぜる){ for(var i = idx.length - 1; i > 0; i--){ var j = Math.floor(Math.random() * (i + 1)), t = idx[i]; idx[i] = idx[j]; idx[j] = t; } idx = idx.slice(0, 10); }
  else idx = idx.slice(Math.max(0, Math.min(ps.length, (から || 1)) - 1));
  練習.段 = 段; 練習.並び = idx; 練習.位置 = 0;
  進む({画面:'練問', 位置: 0, 用途:null, 部分:null, 設備:null, 見る:null, 練習から:false});
}
function 練習の何番から(段){ var v = parseInt(document.getElementById('in_from').value, 10); 練習を始める(段, false, isNaN(v) ? 1 : v); }
function 練習の表を出す(p){
  var a = p.例.答え, h = '<div class="ptbl">';
  if(a.部分) h += '<div class="pr"><b>用途</b><span>複合ビル（用途が2つ以上）</span></div><div class="pr"><b>入っている用途</b><span>' + esc(部分の札(a.部分).join('・')) + '</span></div>';
  else { var nn = 番号と名(a.用途); h += '<div class="pr"><b>用途</b><span>' + nn[0] + ' ' + nn[1] + '</span></div>'; }
  練守る(function(){ return 練習の表(p.例); }).forEach(function(x){ h += '<div class="pr" onclick="練習の行を開く(this, \'' + x.id + '\')"><b>' + esc(x.名) + '</b><span>' + esc(x.値) + '</span></div>'; });
  return h + '</div><div class="note">行を押すと、質問の文が開く</div>';
}
function 練習の行を開く(el, id){
  var nx = el.nextElementSibling; if(nx && nx.classList.contains('inline')){ nx.remove(); return; }
  var p = 練習の今(今().位置), r = 練入れる(p.例), q = 質問を引く(id, r.a), d = document.createElement('div');
  d.className = 'inline'; d.textContent = (q ? q.文 : id) + (q && q.補足 ? ' ／ ' + q.補足 : ''); el.after(d);
}
function 練習で選ぶ(i, s){ var p = 練習の今(今().位置), k = 練習のキー(p); 練習.下書き[k] = 練習.下書き[k] || {}; 練習.下書き[k][p.行[i].設備] = s; var y = window.scrollY; 描く(); window.scrollTo(0, y); }
function 練習の答え合わせ(){
  var g = 今(), p = 練習の今(g.位置), k = 練習のキー(p), d = 練習.下書き[k] || {}, 合 = 0;
  p.行.forEach(function(r){ if(d[r.設備] === r.期待) 合++; });
  練習.記録[k] = { 段: p.段, 番号: p.番号, idx: 練習.並び[g.位置], 答: Object.assign({}, d), 合: 合, 個: p.行.length };
  進む({画面:'練答', 位置: g.位置});
}
function 練習の線を答える(){
  var g = 今(), p = 練習の今(g.位置), el = document.getElementById('in_line'), v = parseFloat(el.value), er = document.getElementById('err');
  if(el.value === '' || isNaN(v)){ er.textContent = '数字を入れて'; el.focus(); return; }
  if(v < 0){ er.textContent = '0以上の数字を入れて'; el.focus(); return; }
  練習.記録[練習のキー(p)] = { 段: p.段, 番号: p.番号, idx: 練習.並び[g.位置], 答: v, 合: v === p.線.線 ? 1 : 0, 個: 1 };
  進む({画面:'練答', 位置: g.位置});
}
function 練習の次(){ var g = 今(); if(g.位置 + 1 < 練習.並び.length) 進む({画面:'練問', 位置: g.位置 + 1}); else 進む({画面:'練まとめ'}); }
function 練習を開く(pos, i){
  var p = 練習の今(pos), r = 例題を入れる(p.例), e = p.段 === '線' ? p.設備 : p.行[i].設備;
  答 = r.a; 自動で入れた = r.自動; 調べた = p.段 === '線' ? [p.設備] : p.行.map(function(x){ return x.設備; });
  進む({画面:'設備', 用途: 答.用途, 部分: 答.部分 || null, 見る: e, 設備: e, 結果から: true, 練習から: true});
}
function 練習に戻る(){ var i = -1; 道.forEach(function(x, j){ if(x.画面 === '練答') i = j; }); if(i >= 0) 何段か戻る(道.length - 1 - i); }
function 練見出し(r, a){ var k = 答; 答 = a; var s = 見出し(r), ns = 効く注記(r); 答 = k; return [s, ns]; }
function 練原文(号){ return '<button class="vb" onclick="号を開く(this, \'' + esc(号) + '\')">' + esc(号) + 'の原文</button>'; }
function 練習の決まり文(){ return '<div class="foot">条文の案内で、実際の建物の判断ではない。最終の判断は管轄の消防署へ。</div>'; }
function 練習の画面(g){
  var h = '';
  if(g.画面 === '練入口'){
    h += '<div class="qt">練習問題</div><div class="note">建物の例を見て、設備が要るか要らないかを答える。答え合わせで、当たった号と条文の原文を読む。</div>';
    if(練習.段 && Object.keys(練習.記録).length && 練習.位置 < 練習.並び.length){
      var pc = 練習の今(練習.位置);
      h += ボタン('続きから（' + esc(練習の段[pc.段].名) + ' ' + pc.番号 + '番）', "進む({画面:'練問', 位置:" + 練習.位置 + "})", 'go') + ボタン('記録を消してはじめから', '練習 = {段:null, 並び:[], 位置:0, 下書き:{}, 記録:{}}; 描く();', 'lite');
    }
    var 休 = 表たち.filter(function(t){ return t.変わった && t.変わった.length; }).map(function(t){ return t.設備; });
    if(休.length) h += '<div class="note">' + esc(休.join('・')) + 'は、根拠の条文が変わったので問題を休んでいる</div>';
    練習の段の順.forEach(function(k){ var s = 練習の段[k], n = 練習の問題()[k].length; if(!n) return; h += '<button class="rb" onclick="進む({画面:\'練段\', 段:\'' + k + '\'})"><b>' + esc(s.名) + '</b> <span class="kj">' + s.級 + '・' + n + '問</span><span class="kj">' + esc(s.中身) + '</span><span class="st">›</span></button>'; });
    h += '<div class="foot">練習用に作った建物。答えは今の条文の条件だけで出していて、条例・特例は入っていない。記録は画面を閉じると消え、どこにも送らない。</div>';
  } else if(g.画面 === '練段'){
    var s = 練習の段[g.段], n = 練習の問題()[g.段].length;
    h += '<div class="qt">' + esc(s.名) + '（' + n + '問）</div>';
    h += ボタン('順番どおりに全部（1番から）', "練習を始める('" + g.段 + "', false, 1)");
    h += '<div class="q"><div class="step">何番から始める？（1〜' + n + '）</div><input id="in_from" type="number" inputmode="numeric" min="1" max="' + n + '" value="1"><button class="b go" onclick="練習の何番から(\'' + g.段 + '\')">この番号から</button></div>';
    h += ボタン('順番を混ぜて10問' + (n < 10 ? '（' + n + '問）' : ''), "練習を始める('" + g.段 + "', true)");
  } else if(g.画面 === '練問'){
    練習.位置 = g.位置;
    var p = 練習の今(g.位置), key = 練習のキー(p), done = 練習.記録[key], d = 練習.下書き[key] || {};
    h += '<div class="step">' + esc(練習の名(p)) + '</div>';
    if(p.段 === '線'){
      var m = p.線, u = /^max:/.test(m.名) ? '㎡' : 単位(m.名);
      h += '<div class="qt">この建物に' + esc(練習の設備名(p.設備)) + 'は要らない。ほかの条件を変えずに、' + esc(値の名(m)) + 'だけが増えるとき、何' + esc(u) + '以上で要るに変わる？</div>' + 練習の表を出す(p);
      if(done) h += '<div class="ans">あなたの答え <b>' + esc(練習の数(done.答) + u) + '</b></div>' + ボタン('答え合わせを見る', "進む({画面:'練答', 位置:" + g.位置 + "})", 'go');
      else h += '<div class="q"><div id="err" class="err"></div><input id="in_line" type="number" inputmode="decimal" min="0" onkeydown="if(event.key===\'Enter\')練習の線を答える()"><button class="b go" onclick="練習の線を答える()">決める</button></div>' + ボタン('この問題をとばす', '練習の次()', 'lite');
    } else {
      h += '<div class="qt">この建物に、次の設備は要る？</div>' + 練習の表を出す(p);
      p.行.forEach(function(r, i){
        var v = done ? done.答[r.設備] : d[r.設備];
        h += '<div class="prow"><div class="pn">' + esc(練習の設備名(r.設備)) + '</div>' + ['要る', '要らない'].map(function(s2){ return '<button class="b' + (v === s2 ? ' was' : '') + '"' + (done ? ' disabled' : '') + ' onclick="練習で選ぶ(' + i + ',\'' + s2 + '\')">' + s2 + '</button>'; }).join('') + '</div>';
      });
      h += '<div class="note">ここに無い設備は、聞いていないだけ。書いていないもの（温泉の設備、同じ敷地の別の建物など）は、無いものとして答える。</div>';
      var all = p.行.every(function(r){ return (done ? done.答 : d)[r.設備]; });
      if(done) h += ボタン('答え合わせを見る', "進む({画面:'練答', 位置:" + g.位置 + "})", 'go');
      else h += (all ? ボタン('答え合わせ', '練習の答え合わせ()', 'go') : '<div class="note">全部の設備に答えると、答え合わせが押せる</div>') + ボタン('この問題をとばす', '練習の次()', 'lite');
    }
    h += ボタン('やめてまとめを見る', "進む({画面:'練まとめ'})", 'lite');
  } else if(g.画面 === '練答'){
    var p = 練習の今(g.位置), rec = 練習.記録[練習のキー(p)], a = 練入れる(p.例).a;
    if(!rec) return '<div class="note">この問題にはまだ答えていない</div>' + ボタン('問題へ', "進む({画面:'練問', 位置:" + g.位置 + "})");
    h += '<div class="step">' + esc(練習の名(p)) + (p.段 !== '線' ? '　合った ' + rec.合 + '／' + rec.個 : '') + '</div>';
    if(a.部分) h += '<div class="also">この建物は ' + esc(用途の名[a.用途]) + ' になる（' + esc(a.用途 === '16ロ' ? '特定用途の部分が無いため' : 短い名(a.部分.filter(function(x){ return 用途に当たる(特定の用途, x.用途); })[0].用途) + 'があるため') + '）。用途ごとの部分を1つの建物とみなして判定する（令9条）</div>';
    if(p.段 === '線'){
      var r = 全部を判定(表たち.filter(function(t){ return t.設備 === p.設備; }), a)[0], m = p.線, u = /^max:/.test(m.名) ? '㎡' : 単位(m.名);
      h += '<div class="rr ' + (rec.合 ? '' : 'bad') + '"><div class="rh"><b>' + esc(練習の設備名(p.設備)) + '</b><span>' + (rec.合 ? '○ 合っている' : '× 違う') + '</span></div>'
        + '<div class="why">あなたの答え: ' + esc(練習の数(rec.答) + u) + '<br>条文の条件での線: ' + esc(練習の数(m.線) + u) + '<br>' + esc(境目の文(m)) + '</div>' + 練原文(m.号) + '</div>';
      h += ボタン('この設備を早見で開く', '練習を開く(' + g.位置 + ', 0)', 'lite');
      h += '<div class="note">線は、ほかの値を変えずに、その値だけが増えた場合。</div>';
    } else {
      var 並 = p.行.map(function(row, i){ return { row: row, i: i, ok: rec.答[row.設備] === row.期待 }; });
      並.sort(function(x, y){ return (x.ok ? 1 : 0) - (y.ok ? 1 : 0) || x.i - y.i; });
      並.forEach(function(x){
        var r = 全部を判定(表たち.filter(function(t){ return t.設備 === x.row.設備; }), a)[0], mh = 練見出し(r, a), st = 見た目(r), body = '';
        if(st === '要る') body = r.要る.map(function(y){ return (y.どこ ? '【' + esc(y.どこ) + '】' : '') + esc(y.号) + (y.理由 ? '（' + esc(y.理由) + '）' : '') + (y.範囲 === '階' ? '（その階に設置）' : y.範囲 === '舞台部' ? '（舞台部に設置）' : y.範囲 === 'その部分' ? '（その部分に設置）' : '') + (y.線 && y.線.length ? '<br>' + esc(y.線.join('・')) : '') + '<br>' + 練原文(y.号); }).join('<br>');
        else body = '設置が要る条件のどれにも当たらない' + (r.境目 ? 境目の箱(r) + (r.境目.主 ? 練原文(r.境目.主.号) : '') : '<div class="kj">基準: ' + esc(表から基準(x.row.設備, a.用途)) + '</div>');
        if(mh[1].length) body += '<div class="also">こうなら要る・あわせて確かめること: ' + mh[1].map(function(y){ return esc(y.理由); }).join(' ／ ') + '</div>';
        if(!x.ok) body += '<div class="note">' + (x.row.期待 === '要る' ? '当たった号を見落としている。原文を開いて、どの条件に当たったかを読む' : (r.境目 && r.境目.主 ? 'いちばん近い線は「' + esc(境目の文(r.境目.主)) + '」。この建物はまだ届いていない' : '')) + '</div>';
        body += ボタン('この設備を早見で開く', '練習を開く(' + g.位置 + ', ' + x.i + ')', 'lite');
        var head = '<div class="rh"><b>' + esc(練習の設備名(x.row.設備)) + '</b><span>' + (x.ok ? '○ 合っている' : '× 違う') + '</span></div><div class="why">あなたの答え: ' + esc(rec.答[x.row.設備]) + '／条文の条件での答え: ' + esc(mh[0]) + '</div>';
        h += '<div class="rr ' + 色[st] + (x.ok ? '' : ' bad') + '">' + (x.ok ? '<details><summary>' + head + '</summary>' + body + '</details>' : head + body) + '</div>';
      });
    }
    h += ボタン(g.位置 + 1 < 練習.並び.length ? '次の問題' : 'まとめを見る', '練習の次()', 'go');
    if(g.位置 + 1 < 練習.並び.length) h += ボタン('やめてまとめを見る', "進む({画面:'練まとめ'})", 'lite');
    h += 練習の決まり文();
    if(公開版.公開 && 公開版.知らせ先) h += '<a class="nb lite" href="' + esc(公開版.知らせ先) + '" target="_blank" rel="noopener">誤りを知らせる（名前・連絡先・建物の名前や住所は書かない。個別の相談には答えない）</a>';
  } else if(g.画面 === '練まとめ'){
    var 記 = Object.keys(練習.記録).map(function(k){ return 練習.記録[k]; }), 設 = 記.filter(function(r){ return r.段 !== '線'; }), 線 = 記.filter(function(r){ return r.段 === '線'; });
    var sum = function(xs, k){ return xs.reduce(function(s, r){ return s + r[k]; }, 0); };
    h += '<div class="qt">まとめ</div>';
    h += '<div class="ans">答えた ' + 設.length + '問・設備 ' + sum(設, '個') + '個のうち 合った ' + sum(設, '合') + '個</div>';
    if(線.length) h += '<div class="ans">線を答える ' + 線.length + '問のうち 合った ' + sum(線, '合') + '問</div>';
    h += '<div class="note">合った数は、条文を読めた数。</div>';
    var 違 = 記.filter(function(r){ return r.合 < r.個; });
    if(違.length){ h += '<div class="step">違った問題（押すと答え合わせ）</div>'; 違.forEach(function(r){ h += '<button class="vb" onclick="練習.段 = \'' + r.段 + '\'; 練習.並び = [' + r.idx + ']; 進む({画面:\'練答\', 位置: 0});">' + esc(練習の段[r.段].名 + ' ' + r.番号) + '</button>'; }); }
    var 同 = 違.filter(function(r){ return r.段 === 練習.段; });
    if(同.length) h += ボタン('違った問題だけもう一度', '練習.並び = [' + 同.map(function(r){ return r.idx; }).join(',') + ']; [' + 同.map(function(r){ return "'" + r.段 + r.番号 + "'"; }).join(',') + '].forEach(function(k){ delete 練習.記録[k]; delete 練習.下書き[k]; }); 練習.位置 = 0; 進む({画面:\'練問\', 位置: 0});');
    if(練習.段) h += ボタン('同じ段をはじめから', "Object.keys(練習.記録).forEach(function(k){ if(練習.記録[k].段 === 練習.段){ delete 練習.記録[k]; delete 練習.下書き[k]; } }); 練習を始める(練習.段, false, 1);", 'lite');
    h += ボタン('段を選び直す', "進む({画面:'練入口'})", 'lite');
  }
  return h;
}
