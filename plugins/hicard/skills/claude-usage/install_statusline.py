#!/usr/bin/env python3
"""statusline に使用率の記録を差し込む・外す（claude-usage Skill から、本人が同意したときだけ呼ばれる）。

  python3 install_statusline.py status              … 今の状態を表示するだけ
  python3 install_statusline.py install --dry-run   … 変更前後の statusLine を表示するだけ（何も書かない）
  python3 install_statusline.py install             … 記録スクリプトをコピーし、~/.claude/settings.json の statusLine を書き換える
  python3 install_statusline.py uninstall           … 差し込む前の statusLine に戻す

🔴 statusLine が指すのは、差し込んだ時点で ~/.claude/usage-log/ にコピーした記録スクリプト。
配布元（自動更新される）を直接指さないので、配布元が更新されても応答のたびに動くコードは変わらない。
記録スクリプトを新しくしたいときは、本人がもう一度 install を実行する。

元の statusline があれば、その表示はそのまま残す（記録したあと同じ入力で元のコマンドを動かす）。
元が無ければ、記録だけして何も表示しない（見た目は変わらない）。
差し込む前の statusLine は ~/.claude/usage-log/statusline_original.json に、
settings.json 全体は ~/.claude/usage-log/settings.json.bak-<日時> に退避する。
"""
import datetime as dt
import filecmp
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys

HOME = pathlib.Path.home()
SETTINGS = HOME / ".claude/settings.json"
STATE_DIR = HOME / ".claude/usage-log"
ORIGINAL = STATE_DIR / "statusline_original.json"
BUNDLED = pathlib.Path(__file__).resolve().parent / "statusline_logger.py"
FIXED = STATE_DIR / "statusline_logger.py"
MARK = "statusline_logger.py"
STALE_DAYS_EMPTY = 1  # 差し込みからこの日数たっても記録が無ければ注意を出す
STALE_DAYS_LAST = 7   # 最後の記録からこの日数たったら注意を出す


def load_settings():
    if not SETTINGS.exists():
        return {}
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def save_settings(s):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS.exists():
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(SETTINGS, STATE_DIR / f"settings.json.bak-{stamp}")
    tmp = SETTINGS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))  # 壊れた JSON で置き換えない
    os.replace(tmp, SETTINGS)


def installed(sl):
    return isinstance(sl, dict) and MARK in str(sl.get("command", ""))


def run_check(command):
    """rate_limits を含まない入力で動かす（記録は書かれない）。終了コードと表示を返す。"""
    sample = json.dumps({"model": {"display_name": "check"}, "workspace": {"current_dir": str(HOME)}})
    r = subprocess.run(command, shell=True, input=sample.encode(), capture_output=True, timeout=15)
    return r.returncode, r.stdout.decode(errors="replace").strip()


def show(label, sl):
    print(f"{label}: {json.dumps(sl, ensure_ascii=False) if sl else '（statusline の設定なし）'}")


def cmd_status():
    sl = load_settings().get("statusLine")
    log = STATE_DIR / "rate_limits.jsonl"
    print(f"記録の差し込み: {'あり' if installed(sl) else 'なし'}")
    show("現在の statusLine", sl)
    if FIXED.exists():
        same = filecmp.cmp(FIXED, BUNDLED, shallow=False) if BUNDLED.exists() else None
        print(f"記録スクリプト（コピー）: あり・配布版と{'同じ' if same else '違う（install をもう一度実行すると新しくなる）'}")
    last = None
    if log.exists():
        lines = log.read_text(encoding="utf-8").splitlines()
        last = dt.datetime.fromisoformat(json.loads(lines[-1])["ts"]) if lines else None
        print(f"記録ファイル: {len(lines)} 行・最終 {last.isoformat() if last else '-'}")
    else:
        print("記録ファイル: まだ無い")
    for line in stale_warning(installed(sl), last):
        print(line)
    return 0


def stale_warning(is_installed, last, now=None):
    """差し込み済みなのに記録が無い・止まっているときの注意（表示用の行）。

    差し込んだ時刻は statusline_original.json の更新時刻で見る（install が毎回書き直す。
    記録スクリプトのコピーは copy2 で配布元の時刻を引き継ぐので使えない）。
    """
    if not is_installed:
        return []
    now = now or dt.datetime.now(dt.timezone.utc)
    if last is None:
        if not ORIGINAL.exists():
            return []
        since = dt.datetime.fromtimestamp(ORIGINAL.stat().st_mtime, dt.timezone.utc)
        days = (now - since).days
        if days < STALE_DAYS_EMPTY:
            return []
        head = f"⚠ 差し込みから {days} 日たっても記録が1行も無い。"
    else:
        days = (now - last).days
        if days < STALE_DAYS_LAST:
            return []
        head = f"⚠ 最後の記録から {days} 日、記録が増えていない（その間 Claude を使っていたなら止まっている）。"
    return [
        head,
        "  考えられる原因: statusline を表示しない画面で使っている（VS Code 拡張・デスクトップアプリ等。未確認）／"
        "statusline に使用率が届かないプラン・ログイン方法",
        "  確かめ方: ターミナルで claude を起動して数回やり取りし、もう一度「状態」を見る。"
        "それでも増えなければ管理者に相談する",
    ]


def cmd_install(dry):
    if not BUNDLED.exists():
        print(f"NG  配布版の記録スクリプトが無い: {BUNDLED}")
        return 1
    s = load_settings()
    sl = s.get("statusLine")
    if installed(sl):
        if not dry:
            shutil.copy2(BUNDLED, FIXED)
            print("OK  既に差し込み済み。記録スクリプトのコピーだけ配布版で置き換えた（statusLine は変えていない）")
        else:
            print("（dry-run）既に差し込み済み。install を実行すると記録スクリプトのコピーだけ置き換える")
        show("現在の statusLine", sl)
        return 0
    if sl is not None and (not isinstance(sl, dict) or sl.get("type") != "command" or not sl.get("command")):
        print("NG  statusLine が command 形式ではないため自動では差し込めない。管理者に相談する。")
        show("現在の statusLine", sl)
        return 1
    base = f"python3 {shlex.quote(str(FIXED))}"
    new = dict(sl) if sl else {"type": "command"}
    new["command"] = f"{base} --then {shlex.quote(sl['command'])}" if sl else base
    show("変更前", sl)
    show("変更後", new)
    if dry:
        print(f"（dry-run: 何も書いていない。install を実行すると {FIXED} にコピーしてから書き換える）")
        return 0

    before = run_check(sl["command"]) if sl else (0, "")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BUNDLED, FIXED)
    ORIGINAL.write_text(json.dumps({"statusLine": sl}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    s["statusLine"] = new
    save_settings(s)

    # 書いた手段とは別に確かめる: settings.json を読み直し、新しいコマンドの表示が元と同じか動かして見る
    if load_settings().get("statusLine") != new:
        print("NG  読み直した statusLine が書いた値と違う。元に戻す。")
        cmd_uninstall()
        return 1
    after = run_check(new["command"])
    if after != before:
        print(f"NG  表示が変わった（前: {before} / 後: {after}）。元に戻す。")
        cmd_uninstall()
        return 1
    print(f"OK  差し込んだ。読み直し一致・表示は元と同じ（終了コード {after[0]}）")
    print(f"    元の設定の退避先: {ORIGINAL}")
    return 0


def cmd_uninstall():
    s = load_settings()
    if not installed(s.get("statusLine")):
        print("OK  差し込まれていない（何も変えていない）")
        return 0
    if not ORIGINAL.exists():
        print(f"NG  元の設定（{ORIGINAL}）が無いので戻せない。管理者に相談する。")
        return 1
    orig = json.loads(ORIGINAL.read_text(encoding="utf-8")).get("statusLine")
    if orig is None:
        s.pop("statusLine", None)
    else:
        s["statusLine"] = orig
    save_settings(s)
    show("OK  元に戻した", load_settings().get("statusLine"))
    print("    これまでの記録（~/.claude/usage-log/rate_limits.jsonl）は残してある")
    return 0


def main():
    args = sys.argv[1:]
    try:
        load_settings()
    except ValueError as e:
        print(f"NG  {SETTINGS} が JSON として読めない（{e}）。何も変えていない。管理者に相談する。")
        return 1
    if args[:1] == ["status"]:
        return cmd_status()
    if args[:1] == ["install"]:
        return cmd_install("--dry-run" in args)
    if args[:1] == ["uninstall"]:
        return cmd_uninstall()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
