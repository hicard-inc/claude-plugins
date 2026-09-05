#!/bin/bash
# Claude Code でこのリポジトリを開いたときに走る（.claude/settings.json の SessionStart）。
# (1) git の pre-push hook を有効にする（打ち忘れを無くす） (2) 禁止語一覧の有無を Claude に見せる。
# 標準出力は Claude の文脈に入る。鍵や一覧の中身は出さない。
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}" || exit 0
[ -f hooks/pre-push ] || exit 0

if [ "$(git config --get core.hooksPath)" != "hooks" ]; then
  git config core.hooksPath hooks && echo "hicard: git の pre-push hook を有効にした（core.hooksPath=hooks）"
else
  echo "hicard: pre-push hook 有効（core.hooksPath=hooks）"
fi

if [ -z "$(git config --get hicard.blocklist)" ]; then
  echo "hicard: 🔴 禁止語一覧（git config hicard.blocklist）が未設定。commit / push は止まる。Owner に一覧を聞いて設定する（CONTRIBUTING.md 8章）"
else
  echo "hicard: 禁止語一覧 設定済み（中身は出さない）"
fi
exit 0
