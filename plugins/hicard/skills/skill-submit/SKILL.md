---
name: skill-submit
description: 自分が作った Skill を hicard の配布 plugin に入れてもらうため、fork から Pull Request を出す。管理者が確認してマージすると全メンバーに自動で届く
argument-hint: "[Skill のフォルダのパス、または名前]"
disable-model-invocation: true
---

# Skill を配布に出す: $ARGUMENTS

**fork（自分の GitHub 上の写し・public）に push し、本体へ PR を出す。**取り込むかは管理者が PR を見て決める。
判断の基準はリポジトリの `CONTRIBUTING.md` が正本（ここに書き写さない）。作業場所は `$HOME/work/claude-plugins-fork`（以下 `$F`）。
git はすべて `git -C "$F"` で打つ。**途中で止まったら迂回せず、理由をそのまま本人に見せる。**

## STEP 1 前提（どれかが欠けたら止まる）

- `gh auth status` が通ること。通らなければ `gh auth login` を案内して止まる（GitHub アカウントが要る）
- `git --version` と `python3 --version` が通ること

## STEP 2 作業場所を用意する

- `$F` が無い: `gh repo fork hicard-inc/claude-plugins --clone=false` → `git clone https://github.com/<自分のID>/claude-plugins "$F"`
  → `git -C "$F" remote add upstream https://github.com/hicard-inc/claude-plugins` → `git -C "$F" config core.hooksPath hooks`
- `$F` がある: `git -C "$F" status --short` が空であることを見る（空でなければ止まって聞く）
- 共通: `git -C "$F" fetch upstream` → `git -C "$F" switch -c skill/<名前> upstream/main`

## STEP 3 出してよいかを見る（ここが本題）

`$F/CONTRIBUTING.md` の **0章・1章・2章・3章・4章・5章** を読み、対象フォルダの**全ファイル**を開いて当てはめる
（SKILL.md だけで判断しない。grep で0件でも目視する）。結果を表で本人に見せる:

| 見るもの | 落ちる例 |
|---|---|
| 0章 入れてはいけないもの | 個人名・その人の状態・報酬・評価・取引先・財務の実データ・鍵・案件名 |
| 3章 関門1 | 自分しか使わない |
| 3章 関門3 | 配れないファイル・別リポジトリを読む |
| 3章 関門4 | 本人が1回動かして出力を見ていない（見ていなければ、今ここで1回動かしてもらう） |
| 4章・5章 | `${CLAUDE_PLUGIN_ROOT}` を使わないパス／`allowed-tools` に MCP ツール名 |
| 2章 サイズ | SKILL.md が 6,700 字超（≒5,000 トークン）。超えたら参照資料へ出す |
| 名前 | `$F/plugins/hicard/skills/` に同名がある |

**1つでも落ちたら、直し方を示して止まる。**一般化して直せるものは直した差分を見せ、本人の了承を取る。

## STEP 4 入れる・版を上げる・検査する

1. `$F/plugins/hicard/skills/<名前>/` へコピーし、参照パスを4章の形に直す
2. `plugins/hicard/.claude-plugin/plugin.json` と `.claude-plugin/marketplace.json` の `version` を**両方** patch +1（python で JSON として書き換える）
3. `$F` で次を全部通す。落ちたら直す（`--no-verify` は使わない）:
   `python3 hooks/check_versions.py` / `python3 hooks/check_secrets.py --all` /
   `claude plugin validate --strict plugins/hicard` / `claude plugin validate --strict .`

## STEP 5 push と PR（本人の確認を取ってから）

**push した瞬間に public の fork で誰でも読める。**`git -C "$F" diff --stat upstream/main` と STEP 3 の表を見せ、
AskUserQuestion で「push して PR を出す／やめる」を聞く。出すと決まったら:

1. `git -C "$F" add plugins/hicard/skills/<名前> plugins/hicard/.claude-plugin/plugin.json .claude-plugin/marketplace.json` → commit
2. `git -C "$F" push -u origin skill/<名前>`
3. `gh pr create -R hicard-inc/claude-plugins --base main --head <自分のID>:skill/<名前>`。
   本文は `$F/.github/pull_request_template.md` の形で、**何をする Skill か・誰が使うか（関門1）・関門4 の実行出力**を書く

## STEP 6 報告

PR の URL を出し、次を伝える: 初めての PR は管理者が Actions の実行を承認するまで検査が「待ち」になる／
マージされると全メンバーに自動で届く／届いたら手元の元の Skill は退避してよい（同名が2つ並ぶため）。
