// ヘッドレス Chromium の実体を探す。
// 🔴 版番号（chromium_headless_shell-1223）とアーキテクチャ（mac-arm64）を
//    ハードコードすると、playwright を更新した人・Intel Mac の人で必ず落ちる。
//    キャッシュを実際に走査して、見つかったものを使う。
const fs = require('fs');
const path = require('path');

module.exports = function findChromium() {
  // ① 明示指定が最優先
  if (process.env.PLAYWRIGHT_CHROMIUM_PATH) return process.env.PLAYWRIGHT_CHROMIUM_PATH;

  const roots = [
    process.env.PLAYWRIGHT_BROWSERS_PATH,
    path.join(process.env.HOME || '', 'Library/Caches/ms-playwright'), // macOS
    path.join(process.env.HOME || '', '.cache/ms-playwright'),         // Linux
  ].filter(Boolean);

  const found = [];
  for (const root of roots) {
    let dirs = [];
    try { dirs = fs.readdirSync(root); } catch { continue; }
    for (const d of dirs) {
      if (!/^chromium/.test(d)) continue;
      // chrome-headless-shell-<os>-<arch>/chrome-headless-shell か
      // chrome-<os>/Chromium.app/Contents/MacOS/Chromium
      const base = path.join(root, d);
      let subs = [];
      try { subs = fs.readdirSync(base); } catch { continue; }
      // 版番号はディレクトリ名からだけ取る。
      // 🔴 フルパスから正規表現で拾うと、親ディレクトリの数字（/tmp/claude-501 等）を
      //    版番号と誤認する。実際にそれで古い版を選んでいた。
      const rev = parseInt((d.match(/-(\d+)$/) || [])[1] || '0', 10);
      for (const s of subs) {
        // headless shell を優先する（軽い。元の実装もこれを使っていた）
        const leaves = [
          { p: path.join(base, s, 'chrome-headless-shell'), rank: 0 },
          { p: path.join(base, s, 'chrome'), rank: 1 },
          { p: path.join(base, s, 'Chromium.app/Contents/MacOS/Chromium'), rank: 1 },
        ];
        for (const leaf of leaves) {
          if (fs.existsSync(leaf.p)) found.push({ path: leaf.p, rev, rank: leaf.rank });
        }
      }
    }
  }
  // headless shell を先に、次に版番号が新しい方を使う
  found.sort((a, b) => a.rank - b.rank || b.rev - a.rev);
  if (found.length) return found[0].path;

  // ② 見つからなければ undefined を返す。呼び出し側は executablePath を渡さず
  //    playwright-core 自身の解決に任せる（それでも落ちたら下のメッセージを出す）
  return undefined;
};

module.exports.hint =
  'Chromium が見つかりません。次を1回だけ実行してください:\n' +
  '  npx playwright install chromium\n' +
  '（別の場所にある場合は PLAYWRIGHT_CHROMIUM_PATH に実体のパスを入れてください）';
