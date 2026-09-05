#!/usr/bin/env python3
"""追跡中の全ファイルに、置いてはいけない語（クライアント名・人名など）が無いか見る。

一覧は環境変数 BLOCKLIST（正規表現・`|` 区切り・大文字小文字を区別しない）で受け取る。
このリポジトリは public なので、一覧そのものはここに書かない（GitHub Actions の secret に置く）。
🔴 ログには「どのファイルの何行目か」しか出さない。当たった語も一覧も出さない（Actions のログは誰でも読める）。

使い方:
  BLOCKLIST='語1|語2' python3 hooks/check_blocklist.py
  一覧が空なら失敗する（守っていない状態で「通った」と見せないため）。
"""
import os
import re
import subprocess
import sys

TEXT_EXT = {".md", ".json", ".py", ".sh", ".yml", ".yaml", ".txt", ".js", ".ts", ".css", ".html", ".mjs", ".cjs", ""}


def main() -> int:
    raw = os.environ.get("BLOCKLIST", "").strip()
    if not raw:
        print("✗ BLOCKLIST が空です。禁止語チェックは何も守っていない状態なので通しません。")
        print("  → Owner が `gh secret set BLOCKLIST -R hicard-inc/claude-plugins` で一覧を入れる（CONTRIBUTING.md 7章）")
        return 1
    try:
        pat = re.compile(raw, re.IGNORECASE)
    except re.error as e:
        print("✗ BLOCKLIST が正規表現として読めません: %s" % e.msg)
        return 1

    files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True).stdout.split("\0")
    hits = []
    for path in filter(None, files):
        if os.path.splitext(path)[1].lower() not in TEXT_EXT:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    if pat.search(line):
                        hits.append("%s:%d" % (path, n))
        except (UnicodeDecodeError, OSError):
            continue

    if hits:
        print("✗ 置いてはいけない語が %d 箇所にあります（語は出しません。手元で BLOCKLIST を使って確認する）:" % len(hits))
        for h in hits:
            print("    " + h)
        return 1
    print("✓ 禁止語 なし（%d ファイル）" % sum(1 for p in files if p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
