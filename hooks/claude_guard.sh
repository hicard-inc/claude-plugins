#!/bin/bash
# Claude Code が git commit / git push を打つ直前に走る（.claude/settings.json の PreToolUse・Bash）。
# ローカル pre-push と Actions と同じ3つの検査をここでもやり、落ちたら exit 2 でコマンドを止める。
# stderr が Claude に返るので、何が当たったかを Claude が本人に伝えられる。
#
# 手で確かめる: bash hooks/claude_guard.sh --self-test
#
# 禁止語一覧は git config hicard.blocklist（.git/config に入るだけで commit されない）。
#   git config hicard.blocklist '語1|語2'      ← 中身は Owner に聞く（public なのでリポジトリに書かない）
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" || exit 0
[ -f hooks/check_secrets.py ] || exit 0

if [ "$1" = "--self-test" ]; then
  CMD="git push"
else
  CMD="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null)"
fi

# git commit / git push 以外は見ない
echo "$CMD" | grep -Eq '(^|[;&|[:space:]])git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+(commit|push)([[:space:]]|$)' || exit 0

fail() { echo "$1" >&2; echo "" >&2; echo "→ 直してからやり直す。--no-verify での迂回はしない（CONTRIBUTING.md 7章）" >&2; exit 2; }

echo "$CMD" | grep -Eq -- '--no-verify' && fail "✗ --no-verify は使わない。hook を飛ばすと鍵と禁止語の検査が外れる"
if echo "$CMD" | grep -Eq 'git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+push'; then
  echo "$CMD" | grep -Eq -- '(--force|--force-with-lease|(^|[[:space:]])-f([[:space:]]|$)|[[:space:]]\+[A-Za-z])' \
    && fail "✗ force push は禁止（deny と branch protection でも止まる）"
fi

OUT=""
if [ -f hooks/check_versions.py ]; then
  R="$(python3 hooks/check_versions.py --quiet 2>&1)" || OUT="$OUT$R"$'\n'
fi
R="$(python3 hooks/check_secrets.py --all --quiet 2>&1)" || OUT="$OUT$R"$'\n'

BL="$(git config --get hicard.blocklist)"
if [ -z "$BL" ]; then
  OUT="$OUT✗ 禁止語一覧（git config hicard.blocklist）が未設定。Owner に一覧を聞いて次を実行する:"$'\n'"    git config hicard.blocklist '語1|語2'"$'\n'
else
  R="$(BLOCKLIST="$BL" python3 hooks/check_blocklist.py 2>&1)" || OUT="$OUT$R"$'\n'
fi

if [ -n "$OUT" ]; then
  fail "hicard の検査で止めました:"$'\n'"$OUT"
fi
if [ "$1" = "--self-test" ]; then
  HP="⚠ pre-push hook 未有効（git config core.hooksPath hooks を実行）"
  [ "$(git config --get core.hooksPath)" = "hooks" ] && HP="pre-push hook 有効"
  echo "✓ claude_guard: 版・鍵・禁止語 すべて通過（${HP}）"
fi
exit 0
