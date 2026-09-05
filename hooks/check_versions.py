#!/usr/bin/env python3
"""marketplace.json と plugin.json の version が食い違っていないか見る。

版は2箇所に書く決まりだが、**#3〜#7 は5回続けて片方だけ上げていた**（marketplace.json が
0.1.2 のまま止まっていた）。人が覚えておく方式は既に失敗しているので機械で見る。

- marketplace.json が無いリポジトリでは何もせず 0 を返す（pre-push から常に呼べるように）
- 使い方: python3 hooks/check_versions.py [--quiet]
"""
import json
import os
import sys

QUIET = "--quiet" in sys.argv


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mp = os.path.join(root, ".claude-plugin", "marketplace.json")
    if not os.path.exists(mp):
        return 0

    try:
        market = json.load(open(mp, encoding="utf-8"))
    except Exception as e:
        print("✗ .claude-plugin/marketplace.json が読めません: %s" % e)
        return 1

    ng = 0
    checked = 0
    for entry in market.get("plugins", []):
        name = entry.get("name", "(名前なし)")
        source = entry.get("source", "")
        if not isinstance(source, str) or not source.startswith("./"):
            continue  # 外部リポジトリ参照は対象外
        pj = os.path.join(root, source, ".claude-plugin", "plugin.json")
        if not os.path.exists(pj):
            print("✗ %s: %s が見つかりません" % (name, os.path.relpath(pj, root)))
            ng += 1
            continue
        try:
            plugin = json.load(open(pj, encoding="utf-8"))
        except Exception as e:
            print("✗ %s: plugin.json が読めません: %s" % (name, e))
            ng += 1
            continue

        mv, pv = entry.get("version"), plugin.get("version")
        checked += 1
        if mv != pv:
            print("✗ %s の version が食い違っています" % name)
            print("    marketplace.json: %r" % mv)
            print("    plugin.json:      %r" % pv)
            print("  → **両方を上げる。**片方だけだと配布側と実体がずれる")
            ng += 1

    if ng:
        return 1
    if not QUIET:
        print("✓ version 一致 %d件" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
