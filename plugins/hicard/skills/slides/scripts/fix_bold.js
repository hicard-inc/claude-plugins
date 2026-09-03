// 和文の太字が閉じない行を直す。
// 「。」「」」「）」などの直後で ** を閉じ、次が日本語だと CommonMark は閉じない。
// 句読点を ** の外に出すと閉じる。和文組版としてもそちらが正しい。
const fs = require('fs');
const md = require('markdown-it')({ html: true, linkify: true });

// 自動で外に出してよいのは「文の終わり」の記号だけ。
// 閉じ括弧を外に出すと **「かぎ括弧**」 になり、開き括弧と対にならない（組版として誤り）。
// 括弧の場合は言い回しを変えるしかないので、直さずに報告する。
const PUNCT = ['。', '、', '？', '！'];
const MANUAL = ['」', '）', '』', '】', '〉', '”'];
const literalCount = (line) => (md.render(line).match(/\*\*/g) || []).length;

const path = process.argv[2];
const src = fs.readFileSync(path, 'utf8');

let fixed = 0;
const out = src.split('\n').map((line, i) => {
  if (!line.includes('**') || literalCount(line) === 0) return line;
  let cur = line;
  for (let pass = 0; pass < 8; pass++) {
    const before = literalCount(cur);
    if (before === 0) break;
    let best = null;
    for (const mark of PUNCT) {
      const needle = mark + '**';
      let idx = -1;
      while ((idx = cur.indexOf(needle, idx + 1)) !== -1) {
        const cand = cur.slice(0, idx) + '**' + mark + cur.slice(idx + needle.length);
        // 描画して literal ** が減る入れ替えだけを採用する（開始側の「。**」は触らない）
        if (literalCount(cand) < before) { best = cand; break; }
      }
      if (best) break;
    }
    if (!best) break;
    cur = best;
  }
  if (cur !== line) { fixed++; console.log(`L${i + 1} 直した`); }
  else if (literalCount(cur) > 0 && MANUAL.some((m) => cur.includes(m + '**'))) {
    console.log(`L${i + 1} 🔴 手で直す（閉じ括弧の直後で閉じている。言い回しを変える）`);
    console.log(`     ${cur.trim().slice(0, 90)}`);
  }
  return cur;
}).join('\n');

fs.writeFileSync(path, out);
console.log(`--- 直した行: ${fixed} ---`);
