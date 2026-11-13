---
name: skill-submit
description: 自分が作った Skill（またはコマンドの .md）を hicard の配布 plugin に入れてもらうため、fork から Pull Request を出す。コマンドは Skill の形に変えて出す。管理者が確認してマージすると全メンバーに自動で届く
argument-hint: "[Skill のフォルダ・コマンドの .md のパス、または名前]"
disable-model-invocation: true
---

# Skill・コマンドを配布に出す: $ARGUMENTS

**fork（自分の GitHub 上の写し・public）に push し、本体へ PR を出す。**取り込むかは管理者が PR を見て決める。
判断の基準はリポジトリの `CONTRIBUTING.md` が正本（ここに書き写さない）。作業場所は `$HOME/work/claude-plugins-fork`（以下 `$F`）。
git はすべて `git -C "$F"` で打つ。**途中で止まったら迂回せず、理由をそのまま本人に見せる。**

## STEP 1 前提（どれかが欠けたら止まる）

- `gh auth status` が通ること。通らなければ `gh auth login` を案内して止まる（GitHub アカウントが要る）
- `git --version` と `python3 --version` が通ること

## STEP 2 対象を決め、作業場所を用意する

- 対象: パスならそれを使う。名前だけなら `~/.claude/skills/<名前>/` → `~/.claude/commands/<名前>.md` の順に探す（両方あれば本人に聞く。どちらも無ければ止まる）
- **コマンド（.md 1枚）なら Skill の形に変えて出す。**Skill とコマンドは同じ `/<名前>` で動く（STEP 3 で変換する）

- `$F` が無い: `gh repo fork hicard-inc/claude-plugins --clone=false` → `git clone https://github.com/<自分のID>/claude-plugins "$F"`
  → `git -C "$F" remote add upstream https://github.com/hicard-inc/claude-plugins` → `git -C "$F" config core.hooksPath hooks`
- `$F` がある: `git -C "$F" status --short` が空であることを見る（空でなければ止まって聞く）
- 共通: `git -C "$F" fetch upstream` → `git -C "$F" switch -c skill/<名前> upstream/main`

## STEP 3 fork にコピーする

`$F/plugins/hicard/skills/<名前>/` へコピーする（`$F/plugins/hicard/skills/` に同名があれば止まる）。
**コマンドの場合**は `<名前>.md` を `skills/<名前>/SKILL.md` として置き、frontmatter に `name: <名前>` と `description:`（無ければ本文から1文で書き、本人に見せる）を足す。
元の frontmatter（`argument-hint`・`allowed-tools` など）と本文・`$ARGUMENTS` は消さずに残す。以降の書き換えはすべてコピー先で行い、元のファイルには触らない。

## STEP 4 配布前レビュー（ここが本題）

`${CLAUDE_PLUGIN_ROOT}/skills/skill-review/SKILL.md` を読み、**STEP 2〜6 をコピー先に当てる**（関門1・4の確認、機械の点検、独立レビュー、本人の了承を取って直す）。
「落とす」が1件でも残ったら、直し方を示して止まる（PR は出さない）。

## STEP 5 版を上げて検査する

1. `plugins/hicard/.claude-plugin/plugin.json` と `.claude-plugin/marketplace.json` の `version` を**両方** patch +1（python で JSON として書き換える）
2. `git -C "$F" add plugins/hicard/skills/<名前> plugins/hicard/.claude-plugin/plugin.json .claude-plugin/marketplace.json`（add しないと新しいファイルが検査に入らない）
3. `$F` で次を全部通す。落ちたら直す（`--no-verify` は使わない）:
   `python3 hooks/check_versions.py` / `python3 hooks/check_secrets.py --all` /
   `claude plugin validate --strict plugins/hicard` / `claude plugin validate --strict .`

## STEP 6 push と PR（本人の確認を取ってから）

**push した瞬間に public の fork で誰でも読める。**

1. PR の本文を作る。形は `$F/plugins/hicard/skills/skill-submit/pr_body.md`（**見出しと表の行の名前を変えない**。必須チェック `blocklist` が確かめる）。
   確認者が**ファイルを開かずに本文だけで取り込むかを決められる**ように、全部の節を埋める（無いものは「なし」）:
   STEP 4 の関門1・4 の答えと実行出力、7観点それぞれの区分（直した後）と根拠「ファイル:行」、直した点、残した要確認。
   個人名・手元のパス・ID は伏せる（PR は誰でも読める）。`$F` の外の一時ファイル（`mktemp`）に書く
2. `git -C "$F" diff --cached --stat upstream/main` と本文の全文を見せ、AskUserQuestion で「push して PR を出す／やめる」を聞く。出すと決まったら:
3. `git -C "$F" commit`（STEP 5 で add 済み）→ `git -C "$F" push -u origin skill/<名前>`
4. `gh pr create -R hicard-inc/claude-plugins --base main --head <自分のID>:skill/<名前> --title "<名前> を追加" --body-file <1 の一時ファイル>`

## STEP 7 報告

PR の URL を出し、次を伝える: 必須チェック `blocklist` が赤なら、検査の Details（Summary）に足りない見出し・空欄が出る。
本文を直して `gh pr edit <番号> -R hicard-inc/claude-plugins --body-file <ファイル>` で上書きすると自動でやり直される／
初めての PR は管理者が Actions の実行を承認するまで検査が「待ち」になる／
マージされると全メンバーに自動で届く／届いたら手元の元の Skill・コマンドは退避してよい（同名が2つ並ぶため）。
