#!/bin/bash
# hicard セットアップ状態チェック（plugin 版）
# Claude が /setup の手順1で実行して、何が完了・未完了かを判断するためのスクリプト。
#
# 🔴 秘密鍵は一切見ない。一般メンバーに鍵は要らない（skills/setup/access_model.md）。
#    鍵が要るのは経理スクリプトを回す人だけで、それはこの配布物の対象外。
# 🔴 接続（Notion / Drive）はシェルからは判定できない。Claude がツールを呼んで確かめる。

NG=0
WARN=0
COL=20   # ラベル列の表示幅

# 日本語（全角）を2カラムとして数えたラベル幅に合わせて右側を空白で埋める。
# printf の %-20s はバイト数で数えるので、日本語ラベルだと列がずれる。
# 🔴 ${#s} はロケール依存（LANG 未設定だとバイト数を返す）。hook 経由で走ると
#    LANG が無いことがあるので、バイト数だけから表示幅を出す（ロケール非依存）。
pad() {
  local s="$1" total non ascii width
  total=$(printf '%s' "$s" | LC_ALL=C wc -c | tr -d ' ')
  non=$(printf '%s' "$s"   | LC_ALL=C tr -d '\000-\177' | LC_ALL=C wc -c | tr -d ' ')
  ascii=$(( total - non ))
  width=$(( ascii + (non / 3) * 2 ))         # UTF-8 の CJK は 3 バイト・表示 2 カラム
  printf '%s' "$s"
  [ "$width" -lt "$COL" ] && printf '%*s' $(( COL - width )) ''
}

row() { printf '%s ' "$1"; pad "$2"; printf ' %s\n' "$3"; }
check() {
  if [ "$2" = "ok" ]; then row "✅" "$1" "$3"; else row "❌" "$1" "$3"; NG=$((NG + 1)); fi
}
warn() { row "⚠️ " "$1" "$2"; WARN=$((WARN + 1)); }
info() { row "⏳" "$1" "$2"; }

echo "=== hicard セットアップ状態 ==="
echo ""
echo "【必須】"

# ── Claude Code ───────────────────────────────────────────────
# 🔴 command -v だけで判定しない。公式インストーラは ~/.local/bin に置くが、
#    そこが PATH に無いことがある。「入っているのに起動しない」状態を ⚠️ で拾う。
if command -v claude >/dev/null 2>&1; then
  check "Claude Code" "ok" "$(claude --version 2>/dev/null | head -1)"
elif [ -x "$HOME/.local/bin/claude" ]; then
  check "Claude Code" "ok" "$("$HOME/.local/bin/claude" --version 2>/dev/null | head -1)（~/.local/bin）"
  warn "PATH" "~/.local/bin が PATH に無い。次にターミナルを開くと claude が起動しない"
  echo "      直す → echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
else
  check "Claude Code" "ng" "未インストール → https://claude.com/product/claude-code"
fi

# ── git（プラグインの取得・更新に使う）──────────────────────────
if command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then
  check "git" "ok" "$(git --version)"
else
  # 🔴 xcode-select --install は GUI を出して即戻る。Claude が代わりに実行しても終わらない。
  check "git" "ng" "未インストール → ターミナルで xcode-select --install を実行し、出た画面を最後まで進める"
fi

# ── hicard プラグイン ─────────────────────────────────────────
# ${CLAUDE_PLUGIN_ROOT} はプラグイン経由で呼ばれたときだけ入る。
# 直接 bash で叩かれた場合はスクリプト自身の位置から遡って推定する。
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd -P)}"
if [ -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" ]; then
  VER=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("version","?"))' \
        "$PLUGIN_ROOT/.claude-plugin/plugin.json" 2>/dev/null || echo "?")
  check "hicard プラグイン" "ok" "v$VER"
else
  check "hicard プラグイン" "ng" "ターミナルで CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 claude plugin marketplace add hicard-inc/claude-plugins → claude plugin install hicard@hicard-plugins"
fi

# ── git の名乗り ─────────────────────────────────────────────
GIT_EMAIL=$(git config --global user.email 2>/dev/null)
GIT_NAME=$(git config --global user.name 2>/dev/null)
if [ -z "$GIT_EMAIL" ] || [ -z "$GIT_NAME" ]; then
  check "git の名乗り" "ng" "未設定 → 本人に聞いて git config --global user.email / user.name を設定する"
else
  # 🔴 すでに設定されている名乗りは、hicard のアドレスでなくても ⚠️ を出さない。
  #    変更も勧めない（2026-08-27 の運用判断）。Google の認可アドレスとは別の話。
  check "git の名乗り" "ok" "$GIT_NAME <$GIT_EMAIL>"
fi

# ── 許可設定（deny）──────────────────────────────────────────
# 🔴 読むだけ。このスクリプトは settings.json を書き換えない（Claude はそもそも書けない）。
#    中身の作り方と「わざと1回止める」手順は skills/setup/access_model.md の 4。
DENY_JSON="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/deny.json"   # 推奨設定の正本（deny・bypass 禁止・自動更新。access_model.md もこれを指す）
SETTINGS_LINES=$(python3 - "$HOME/.claude/settings.json" "$DENY_JSON" <<'PYEOF' 2>/dev/null
import json, os, sys
def ng_all(msg):
    for k in ("deny", "bypass", "update"):
        print("%s\tng\t%s" % (k, msg))
    raise SystemExit
try:
    want = json.load(open(sys.argv[2], encoding="utf-8"))["permissions"]["deny"]
except Exception as e:
    ng_all("deny.json（推奨設定の正本）が読めない（%s）" % type(e).__name__)
p = sys.argv[1]
if not os.path.exists(p):
    ng_all("~/.claude/settings.json が無い")
try:
    s = json.load(open(p, encoding="utf-8"))
except Exception as e:
    ng_all("JSON として壊れている（%s）。直すまで1件も効かない" % type(e).__name__)
perms = s.get("permissions") or {}
deny = perms.get("deny") or []
missing = [w for w in want if w not in deny]
if len(missing) == len(want):
    print("deny\tng\tdeny が1件も入っていない")
elif missing:
    print("deny\twarn\t足りない %d 件: %s" % (len(missing), " ".join(missing)))
else:
    print("deny\tok\tdeny %d 件（推奨 %d 件すべて）" % (len(deny), len(want)))
# bypass 禁止: --dangerously-skip-permissions と Shift+Tab の bypass を封じる（user 設定でも効く・公式）
if perms.get("disableBypassPermissionsMode") == "disable":
    print("bypass\tok\tdisableBypassPermissionsMode: disable")
else:
    print("bypass\tng\tpermissions.disableBypassPermissionsMode が無い")
# 自動更新: 第三者 marketplace は既定で切れている（公式）。無いと新しい版が届かない
mk = (s.get("extraKnownMarketplaces") or {}).get("hicard-plugins") or {}
if mk.get("autoUpdate") is True:
    print("update\tok\tautoUpdate: true（新しい版は次の起動で入る）")
else:
    print("update\tng\textraKnownMarketplaces.hicard-plugins.autoUpdate が無い（新しい版が届かない）")
PYEOF
)
[ -z "$SETTINGS_LINES" ] && SETTINGS_LINES=$'deny\tng\t判定できなかった（python3 が無い）'
while IFS=$'\t' read -r KEY ST MSG; do
  [ -z "$KEY" ] && continue
  case "$KEY" in
    bypass) LABEL="bypass 禁止" ;;
    update) LABEL="自動更新" ;;
    *)      LABEL="許可設定（deny）" ;;
  esac
  case "$ST" in
    ok)   check "$LABEL" "ok"  "$MSG" ;;
    warn) warn  "$LABEL"       "$MSG" ;;
    *)    check "$LABEL" "ng"  "$MSG → access_model.md の 4 を本人の手で貼る" ;;
  esac
done <<< "$SETTINGS_LINES"

echo ""
echo "【/setup には要らないが、/slides には必須】"
# 🔴 「任意」と書くと、/slides を使う人が入れずに始めて node: command not found で止まる。
#    /setup に要らない = 任意 ではない。どちらの意味かを行に書く。
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  row "・" "Node.js / npm" "$(node --version) / $(npm --version)"
elif command -v node >/dev/null 2>&1; then
  row "・" "Node.js / npm" "node $(node --version) はあるが npm が無い → /slides の画像化が落ちる"
else
  row "・" "Node.js / npm" "未インストール。🔴 /slides を使うなら必須（brew install node か nodejs.org の LTS）"
fi

echo ""
echo "【接続（このスクリプトでは判定できない。Claude がツールを呼んで確認する）】"
info "Notion"       "notion-get-users user_id:self を呼ぶ。認証エラーなら出てくる URL で認可する"
info "Google Drive" "検索ツールを ToolSearch し、query:\"owner = 'me'\" で呼んで返る owner を読む"
echo "   🔴 Notion は必ず「hicard」ワークスペースを選ぶ。個人側を選ぶと空になる。"
echo "   🔴 Google は Drive に招待されているアカウント。@hicard.studio とは限らない"
echo "      （個人 Gmail で招待されている人が実在する）。違う方で認可すると、接続は成功するのに中身が空になる。"
echo "   🔴 ドライブはこの plugin では配っていない（0.1.7 で外した）。claude.ai のコネクタで各自が有効にする。"
echo "      検索ツールが1つも無いときは本人の権限の問題ではない → skills/setup/troubleshooting.md"
echo "   🔴 「Connected」で終わらせない。実際に1件読めることまで確認する。"

echo ""
echo "【一般メンバーに要らないもの（❌ が出ても無視してよい、ではなく最初から見ていない）】"
echo "   ・秘密鍵（.env / google_credentials.json）… 経理スクリプト専用。管理者に要求しない"

echo ""
echo "────────────────────────────────"
if [ "$NG" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  echo "必須項目はすべて完了。あとは上の【接続】を Claude が確認する。"
  echo "SETUP_OK"
elif [ "$NG" -eq 0 ]; then
  echo "必須は完了。ただし ⚠️ が $WARN 件ある。⚠️ も直すこと（放置すると次回起動で壊れる）。"
  echo "SETUP_OK_WITH_WARN"
else
  echo "未完了が $NG 件。上の ❌ を先に直す。"
  echo "SETUP_NG"
fi
