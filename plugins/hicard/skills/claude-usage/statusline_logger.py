#!/usr/bin/env python3
"""statusline の入力 JSON から rate_limits だけを取り出してローカルに追記する。

Claude Code が statusline を描くたびに呼ばれる（install_statusline.py が設定する）。
  python3 statusline_logger.py                  … 記録だけして何も表示しない
  python3 statusline_logger.py --then '<元の statusline コマンド>'
                                                … 記録したあと、同じ入力で元のコマンドを動かし、その表示をそのまま出す
記録するのは使用率とリセット時刻だけ（cwd・モデル・セッションIDは記録しない）。
前回と値が同じで、日付（JST）も同じなら書かない。
記録で何が失敗しても表示は壊さない（例外は握りつぶし、終了コードは元のコマンドに合わせる）。
"""
import datetime as dt
import json
import os
import subprocess
import sys

LOG = os.path.expanduser("~/.claude/usage-log/rate_limits.jsonl")
JST = dt.timezone(dt.timedelta(hours=9))


def last_line(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 4096))
            lines = f.read().splitlines()
            return json.loads(lines[-1]) if lines else None
    except Exception:
        return None


def record(raw):
    data = json.loads(raw)
    rl = data.get("rate_limits")
    if not isinstance(rl, dict):
        return
    fh = rl.get("five_hour") or {}
    sd = rl.get("seven_day") or {}
    rec = {
        "fh": fh.get("used_percentage"),
        "fh_reset": fh.get("resets_at"),
        "sd": sd.get("used_percentage"),
        "sd_reset": sd.get("resets_at"),
    }
    if rec["fh"] is None and rec["sd"] is None:
        return
    now = dt.datetime.now(dt.timezone.utc)
    prev = last_line(LOG)
    if prev:
        same = all(prev.get(k) == v for k, v in rec.items())
        prev_day = dt.datetime.fromisoformat(prev["ts"]).astimezone(JST).date()
        if same and prev_day == now.astimezone(JST).date():
            return
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": now.isoformat(timespec="seconds"), **rec}) + "\n")


def main():
    raw = sys.stdin.buffer.read()
    try:
        record(raw)
    except Exception:
        pass
    if len(sys.argv) == 3 and sys.argv[1] == "--then":
        try:
            r = subprocess.run(sys.argv[2], shell=True, input=raw, stdout=subprocess.PIPE, timeout=10)
            sys.stdout.buffer.write(r.stdout)
            return r.returncode
        except Exception:
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
