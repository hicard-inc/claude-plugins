#!/usr/bin/env python3
"""push される中身に鍵・置いてはいけないファイル・巨大ファイルが無いか見る。

hicard-inc/claude の scripts/ci/run_checks.py を、どのリポジトリでも動くよう
単一ファイルに切り出したもの（Python3 標準ライブラリのみ / 追加インストール不要）。

使い方:
  python3 check_secrets.py --range origin/main..HEAD   # push される範囲
  python3 check_secrets.py --all                       # 追跡中の全ファイル
除外したい行には ci:allow-secret と書く（テスト用の偽データ等）。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True).stdout.strip() or ".")

# ── 1. 鍵らしい文字列 ──────────────────────────────────────────────
SECRET_PATTERNS = [
    ("Notion トークン",        re.compile(r"\b(?:ntn_|secret_)[A-Za-z0-9]{30,}")),
    ("Slack トークン",         re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Slack Webhook",         re.compile(r"hooks\.slack\.com/services/T[A-Za-z0-9/_-]{10,}")),
    ("GitHub トークン",        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Figma トークン",         re.compile(r"\bfigd_[A-Za-z0-9_-]{30,}")),
    ("AWS アクセスキー",        re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # ── 以下は移植時に追加（TypeScript / Next.js / Vercel 構成で実際に使う鍵）──
    ("Google APIキー",         re.compile(r"\bAIza[0-9A-Za-z_-]{35,}")),
    ("Google OAuthシークレット", re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{20,}")),
    ("Anthropic APIキー",      re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI APIキー",         re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}")),
    ("Stripe 鍵",             re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("npm トークン",           re.compile(r"\bnpm_[A-Za-z0-9]{36}\b")),
    ("JWT（Supabase等の鍵）",   re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}")),
    ("鍵らしい代入",            re.compile(r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)\s*[=:]\s*['\"][^'\"\s]{16,}['\"]")),
]

# 「ヘッダだけ」は手順書がよく書く。実体（base64 の本文）が続くときだけ本物とみなす。
PEM_HEADER = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----")
PEM_BODY = re.compile(r"^[A-Za-z0-9+/=]{40,}$")
SA_TYPE = re.compile(r'"type"\s*:\s*"service_account"')
SA_KEY = re.compile(r'"private_key"\s*:\s*"')

ALLOW_MARK = "ci:allow-secret"

# ── 2. そもそも git に入れてはいけない場所 ─────────────────────────
ENV_OK = re.compile(r"(?i)\.env\.(example|sample|template|dist)$")
FORBIDDEN_PATHS = [
    (re.compile(r"^secrets/"),                      "secrets/ は絶対に commit しない"),
    (re.compile(r"(?i)(^|/)\.env(\.|$)"),           ".env は鍵そのもの（.env.example だけ入れてよい）"),
    (re.compile(r"(?i)(^|/)\.dev\.vars$"),          ".dev.vars は Workers のローカル鍵"),
    (re.compile(r"(?i)(^|/)google_credentials\.json$"), "サービスアカウント鍵は git に入れない"),
    (re.compile(r"(?i)\.(pem|p12|pfx|keystore|jks|mobileprovision)$"), "証明書・秘密鍵ファイルは git に入れない"),
    (re.compile(r"(?i)(^|/)id_(rsa|dsa|ecdsa|ed25519)$"), "SSH 秘密鍵は git に入れない"),
    (re.compile(r"(?i)(^|/)\.npmrc$"),              ".npmrc は npm トークンが入る"),
]

# サイズ上限は --max-kb で指定する。既定 0 = 無効。
# 元実装（claude リポジトリ）は 1MB 固定だが、動画・画像を扱う制作リポジトリでは
# 初日から素材が引っかかり hook 自体を外される。目的（鍵の防御）を守るため既定を外した。
DEFAULT_MAX_KB = 0

# 走査しない拡張子（バイナリ）。※元実装は「テキスト拡張子の許可リスト」方式だったが、
#   .tsx / .swift / .css 等が漏れて中身を見ないまま通ってしまうため、除外リスト方式にした。
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".svg",
    ".pdf", ".zip", ".gz", ".tar", ".dmg", ".mp4", ".mov", ".mp3", ".wav",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".psd", ".ai", ".sketch",
    ".xcuserstate", ".car", ".framework", ".a", ".o", ".dylib", ".so",
}


def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout


def changed_files(mode, rng):
    if mode == "range":
        out = run("git", "diff", "--name-only", "--diff-filter=ACMR", rng)
    else:
        out = run("git", "ls-files")
    return [f for f in out.split("\n") if f]


def content_of(path, mode, rng):
    if mode == "range":
        head = rng.split("..")[-1] if ".." in rng else rng
        return run("git", "show", f"{head}:{path}")
    p = ROOT / path
    return p.read_text(errors="ignore") if p.exists() else ""


def check_paths(files, mode, rng, problems):
    for f in files:
        if ENV_OK.search(f):
            continue
        for pat, why in FORBIDDEN_PATHS:
            if not pat.search(f):
                continue
            # 中身に ci:allow-secret があれば意図的な例外として通す
            # （例: 1Password の op:// 参照だけを書いた .env）
            if ALLOW_MARK in content_of(f, mode, rng)[:2000]:
                break
            problems.append((f, why))
            break


def check_secrets(files, mode, rng, problems):
    for f in files:
        if Path(f).suffix.lower() in BINARY_SUFFIXES:
            continue
        text = content_of(f, mode, rng)
        if not text or len(text) > 2_000_000:
            continue
        lines = text.split("\n")

        for i, line in enumerate(lines, 1):
            if ALLOW_MARK in line or not PEM_HEADER.search(line):
                continue
            if any(PEM_BODY.match(l.strip()) for l in lines[i:i + 3]):
                problems.append((f"{f}:{i}", "秘密鍵（PEM）の本体が含まれています"))

        if SA_TYPE.search(text) and SA_KEY.search(text) and ALLOW_MARK not in text:
            problems.append((f, "Google サービスアカウント鍵の JSON です"))

        for i, line in enumerate(lines, 1):
            if ALLOW_MARK in line:
                continue
            for label, pat in SECRET_PATTERNS:
                if pat.search(line):
                    problems.append((f"{f}:{i}", f"{label} らしき文字列が含まれています"))
                    break


def check_size(files, mode, rng, problems, max_kb):
    """作業ツリーではなく、実際に push される中身のサイズを見る。"""
    if max_kb <= 0:
        return
    limit = max_kb * 1000
    for f in files:
        if mode == "range":
            head = rng.split("..")[-1] if ".." in rng else rng
            out = run("git", "cat-file", "-s", f"{head}:{f}").strip()
            n = int(out) if out.isdigit() else 0
        else:
            p = ROOT / f
            n = p.stat().st_size if p.exists() else 0
        if n > limit:
            problems.append((f, f"{n // 1000}KB あります（上限 {max_kb}KB）"))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--range")
    g.add_argument("--all", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--max-kb", type=int, default=DEFAULT_MAX_KB,
                    help="1ファイルの上限KB。0で無効（既定）")
    a = ap.parse_args()

    mode = "range" if a.range else "all"
    files = changed_files(mode, a.range or "")
    if not files:
        if not a.quiet:
            print("チェック対象なし")
        return 0

    problems = []
    check_paths(files, mode, a.range or "", problems)
    check_secrets(files, mode, a.range or "", problems)
    check_size(files, mode, a.range or "", problems, a.max_kb)

    for where, why in problems:
        print(f"  ✗ {where}\n      {why}")

    if problems:
        print(f"\n{len(problems)} 件見つかりました。直してからやり直してください。")
        return 1
    if not a.quiet:
        print(f"✓ {len(files)} ファイル チェック OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
