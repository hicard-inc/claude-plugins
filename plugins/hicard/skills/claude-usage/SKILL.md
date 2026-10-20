---
name: claude-usage
description: 自分の Claude Code の週次使用量を集計し、確認のうえ Notion [TMP] ClaudeUsage に自分の行を1行書く。使用率の記録（statusline への差し込み）を始める・止める・状態を見る
disable-model-invocation: true
argument-hint: "[空欄=先週 / 週開始日 YYYY-MM-DD（月曜） / 記録を始める / 記録を止める / 状態]"
---

# Claude 使用量の週次報告: $ARGUMENTS

契約プランを見直す判断材料として、各自の使用量を1人×1週の1行で Notion に集める。
**数値は Python が作る。Claude は数値を作らない・書き換えない。**Notion へは**本人が確認してから**書く。

| | |
|---|---|
| 書き込み先 data source | `collection://a081bb09-7c76-4c1f-8e09-72e8deaba501`（`[TMP] ClaudeUsage`） |
| スクリプト | `${CLAUDE_PLUGIN_ROOT}/skills/claude-usage/` の `claude_usage.py`（集計）・`install_statusline.py`（記録の差し込み） |
| 列の定義・よくある症状 | `${CLAUDE_PLUGIN_ROOT}/skills/claude-usage/reference.md`（必要になったときだけ読む） |

🔴 Notion に送ってよいのは、スクリプトが出した `properties` の値と、Name・メンバーだけ。
`model_breakdown` は画面確認用で Notion に書かない。パス・プロンプト・セッションIDは送らない。

## 何をするか

| `$ARGUMENTS` | 動き |
|---|---|
| 空欄 | 先週（月〜日・JST）を報告（A） |
| `YYYY-MM-DD`（月曜） | その週を報告（A） |
| `記録を始める` | 使用率の記録を差し込む（B） |
| `記録を止める` | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-usage/install_statusline.py" uninstall` を実行し、出力をそのまま見せる |
| `状態` | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-usage/install_statusline.py" status` を実行し、出力をそのまま見せる |

## A. 週次の報告

### A1. 集計する

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-usage/claude_usage.py" [--week-start <日付>]
```

日付が無ければ `--week-start` を付けない。終了コードが0以外なら、エラー文をそのまま見せて止まる。

### A2. プランを聞く

AskUserQuestion で「今のプランはどれか」を**必ず**聞く（選択肢: `Pro` / `Max 5x` / `Max 20x`）。推測で埋めない。
Pro換算の期待値 =（Pro=1・Max 5x=5・Max 20x=20）× `週次上限の使用率` ÷ 100。使用率が空なら期待値も空。

### A3. ツールを読み込み、自分と既存行を調べる

🔴 Notion のツール名は環境で前置きが変わるので、決め打ちせず先に読み込む：

```
ToolSearch  query: "+notion query data sources create pages update page fetch self"
```

1. `notion-get-self` で自分のユーザーIDと名前を取る
2. `notion-query-data-sources` の **rows モード**で既存行を探す。条件は「`週開始日` が `date_is` で週開始日」かつ「`メンバー` が `person_contains` で `relative: me`」
   - 0件 → 新規。1件 → その行を更新。**2件以上 → 書かずに止まり、行のURLを見せる**

### A4. 書く前に確認する

次を表で見せ、AskUserQuestion で「この内容で書く / 書かない」を聞く。「書かない」なら何もせず終わる。

- 新規か更新か（更新なら行のURLと、変わる列の旧値→新値）
- Name（`<name_prefix> <自分の名前>`）・メンバー・全 `properties`・Pro換算の期待値
- `notes` の全文
- 参考の `model_breakdown`（Notion には書かないと明記）

### A5. 書く

- 新規: `notion-create-pages`（parent は `{"type":"data_source_id","data_source_id":"a081bb09-7c76-4c1f-8e09-72e8deaba501"}`）
- 更新: `notion-update-page`（`update_properties`）
- 週開始日は `date:週開始日:start` に日付・`date:週開始日:is_datetime` に `0`。メンバーは自分のユーザーIDの配列。数値は数値のまま
- 値が `null` の列は、新規なら送らない・更新なら `null` を送る
- 書き込み権限が無いと言われたら、止まって「管理者に編集権限を頼む」と伝える（迂回しない）

### A6. 読み直して確かめる

`notion-fetch` で書いた行を読み直し、送った全列が一致すること、**`Pro換算` が A2 の期待値と一致すること**を見る。
違う列は「列名・送った値・読めた値」を報告する。**勝手に再送しない。**

### A7. 報告する

行のURL・新規か更新か・一致した列数・`notes`。
`notes` に「使用率の記録が無い週」があれば、`install_statusline.py status` を実行し、差し込みが「なし」なら
「使用率の列が空なので判定に使えない。記録を始めるなら `/claude-usage 記録を始める`」と1行添える。

## B. 使用率の記録を始める（本人の同意が必須）

使用率は statusline にしか届かないため、statusline に記録を差し込む。**応答のたびに動く処理を本人の設定に足す変更**なので、
**AskUserQuestion で本人が「始める」を選んだときだけ**実行する。黙って入れない・他の手順のついでに入れない。

1. `python3 "${CLAUDE_PLUGIN_ROOT}/skills/claude-usage/install_statusline.py" install --dry-run` を実行し、変更前後をそのまま見せる
2. 次を説明してから AskUserQuestion で「始める / やめておく」を聞く
   - 記録するのは5時間枠と週次の使用率・リセット時刻だけ（会話・フォルダ・モデルは記録しない）。記録は自分のマシンの中だけ
   - 今の statusline の表示は変わらない。記録スクリプトは `~/.claude/usage-log/` にコピーしたものが動き、配布元の更新では変わらない
   - やめるときは `/claude-usage 記録を止める` で元に戻る
3. 「始める」なら `install`（`--dry-run` なし）を実行する。`OK` の行が出たら合格。`NG` なら出力をそのまま見せて止まる
4. 「次に Claude が応答した後から記録が始まる。数回やり取りした後に `/claude-usage 状態` で `記録ファイル: N 行` が出れば動いている」と伝える

🔴 実行が権限や確認ダイアログで拒否されたら、迂回せず止まり、拒否された旨をそのまま伝える。
