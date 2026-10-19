---
name: tasks
description: Notion [PJ] Tasks の状況を確認する。メンバーを指定するとその人の未完了タスクを、指定しなければ誰のタスクを見るか質問してから表示する。プロジェクト・ステータス別にも表示できる
argument-hint: "[メンバー名 / 自分 / 全員 / プロジェクト別 / 要記入]（空欄なら誰のタスクか質問する）"
---

# タスク確認: $ARGUMENTS

**すべての値は 2026-10-19 に実測して確認済み**（初回 2026-08-21）。推測で書き換えないこと。
**このスキルは読むだけ。**ステータス変更・起票・コメントはしない。タスクを**作る**ときは `task-add` スキルを使う。

| | |
|---|---|
| Database | `https://app.notion.com/p/8dac7c0c458242f3a3ff29a3c55b6f85` |
| **Tasks の data source** | **`collection://633304e7-495e-4a00-a41e-d53e369dc238`** |
| Epics の data source | `collection://36827ee8-8d3d-4192-8103-63c06ac3a22e`（Epic 名は `Name` 列） |

## STEP 0｜ツールを読み込む

🔴 **Notion のツール名は環境によって前置きが変わる**（プラグイン経由なら `mcp__plugin_hicard_notion__`、
claude.ai コネクタ経由なら `mcp__claude_ai_Notion__`）。**素の名前で決め打ちせず、先に読み込む**：

```
ToolSearch  query: "+notion query data sources users self fetch"
```

## STEP 1｜何を見るかを決める

| `$ARGUMENTS` | 動き |
|---|---|
| **空欄** | 🔴 **必ず AskUserQuestion で「誰のタスクを見るか」を聞く**（下の「質問の出し方」）。全件を出して済ませない |
| `自分` `me` `my` `私` | `notion-get-self` の user ID で STEP 3A |
| `全員` `all` | STEP 3B（担当者別の件数サマリ） |
| `プロジェクト別` / `要記入` `抜け` | STEP 3C（保存済みビュー） |
| ステータス名（下の6つ） | 全員分をそのステータスで絞って STEP 3A の表で出す |
| それ以外 | メンバー名として照合する（下） |

### メンバー名の照合

`notion-get-users`（`page_size: 100`）でワークスペースの一覧を取り、**`type: "person"` だけ**を候補にする。
`name` と、`email` の `@` より前を、大文字小文字を無視して部分一致で照合する。
Notion の表示名はローマ字のことが多いので、**日本語で来たら読みをローマ字にして照合する**（漢字の姓 → ローマ字の姓）。

- **1人に決まった** → 「<name> のタスクを取得します」と1行書いて STEP 3A へ
- **0人・2人以上** → 🔴 推測で選ばない。AskUserQuestion で候補（最大4人）を出して聞く

### 質問の出し方（空欄のとき）

```
AskUserQuestion
  question: "誰のタスクを取得しますか？（メンバー: <person の name をカンマ区切りで全員>）"
  header: "担当者"
  options:
    - label: "自分"           description: "<notion-get-self の name> の未完了タスク"
    - label: "全員（サマリ）"  description: "担当者別の未完了件数・期限切れ件数"
  （他のメンバーは「Other」に名前を入れてもらい、上の照合にかける）
```

## STEP 2｜列名を確かめる

叩く前に `notion-fetch` で Tasks の data source を取り、`<sqlite-table>` に
`Title` / `Status` / `Assignee` / `Epics` / `userDefined:ID` / **`date:Due by:start`** があることを見る。
🔴 **列名は何度も変わっている**（期限は `Due by` → `Due Date` → `Due by`）。無ければ `<sqlite-table>` の実名に読み替え、
報告の最後に「列名が変わっていた」と書く。**`Priority` 列は無い**（2026-10-19）。

## STEP 3A｜1人分（またはステータス指定）の一覧

```
notion-query-data-sources
  data:
    data_source_urls: ["collection://633304e7-495e-4a00-a41e-d53e369dc238"]
    query: |
      SELECT "userDefined:ID" AS id, "Title", "Status",
             "date:Due by:start" AS due, "Epics", "Assignee", url
      FROM "collection://633304e7-495e-4a00-a41e-d53e369dc238"
      WHERE "Assignee" LIKE ? AND COALESCE("Status",'') NOT IN ('Done','Archive')
      ORDER BY due IS NULL, due
    params: ["%<user id>%"]
```

- **`Assignee` は person 型で、返るのは名前ではなく `["user://<id>", ...]`。**必ず user ID で当てる
- 🔴 `Status` が空の行がある。`"Status" NOT IN (...)` だけだと空の行が黙って落ちるので `COALESCE` を外さない
- ステータス指定のときは `Assignee` の条件を外し、`"Status" = ?` にする
- `has_more: true` が返ったら、全件取れていないことを表の上に書く

**Epic 名を引く**: `Epics` は URL の配列。URL の形が2種類ある（`https://app.notion.com/p/<ID>` と `https://app.notion.com/<ID>`）ので、
末尾の**32桁の ID** を重複なしで取り出し、Epics の data source を `WHERE url LIKE ? OR url LIKE ? ...`（`params: ["%<ID>%", ...]`）で引いて `Name` を使う。

共同担当者の名前は STEP 1 の一覧で引く。一覧に無い user ID（ゲスト等。`user_id` を指定しても空が返る）は `不明(<ID先頭8桁>)` と出す。

## STEP 3B｜全員（担当者別サマリ）

未完了は数百件あるので**一覧は出さず、件数だけ**出す。

```sql
SELECT COALESCE(j.value,'(未割当)') AS assignee,
       COUNT(*) AS open_n,
       SUM(CASE WHEN t."date:Due by:start" < ? THEN 1 ELSE 0 END) AS overdue_n,
       SUM(CASE WHEN t."date:Due by:start" IS NULL THEN 1 ELSE 0 END) AS nodue_n
FROM "collection://633304e7-495e-4a00-a41e-d53e369dc238" t
LEFT JOIN json_each(t."Assignee") j
WHERE COALESCE(t."Status",'') NOT IN ('Done','Archive')
GROUP BY 1 ORDER BY open_n DESC
-- params: ["<今日 YYYY-MM-DD>"]
```

共同担当のタスクは担当者ごとに1件ずつ数えるので、**列の合計はタスク件数より大きくなる**（表の下に注記する）。
表示後に「特定の人の一覧を見ますか？」と聞き、名前が返ったら STEP 3A を回す。

## STEP 3C｜保存済みビュー

```
notion-query-data-sources
  data: {"mode":"view","view_url":"<下の URL>","page_size":100}
```

| 引数 | ビュー | view_url |
|---|---|---|
| 「プロジェクト別」 | **By Project**（`Epics` でグループ化） | `https://www.notion.so/8dac7c0c458242f3a3ff29a3c55b6f85?v=aeeae019-24c7-442a-a0ee-b970b5f4ca5a` |
| 「要記入」「抜け」 | **🔧 要記入（Epic / Status）** | `...?v=3c1c972c-2bcb-813f-bf5b-000cbb49bb6f` |

`has_more: true` なら `next_cursor` を `start_cursor` に渡して続きを取る（全件は100件に収まらない）。

## STEP 4｜表示

今日の日付は `date +%F` で取る（暗算しない）。

```
## <name> の未完了タスク（<件数>件・<YYYY-MM-DD> 時点）

| ID | タスク名 | ステータス | 期限 | Epic | 共同担当 |
|---|---|---|---|---|---|
```

- 並び順は期限の古い順、期限なしは最後。`ID` は `TAS-<数字>`、タスク名は `url` へのリンクにする
- 期限が今日より前の行は期限の前に ⚠️ を付ける

表の後に:
- **ステータス別の内訳**。ステータスは `Not started` / `Ready` / `In progress` / `Review` / `Done` / `Archive` の6つだけで、空は「未設定」として別に数える
- **期限切れ**の件数と ID（0件なら書かない）
- **期限未設定**の件数

## 踏んだ穴（2026-08-21・09-28・10-19 実測）

| # | 事実 | どうする |
|---|---|---|
| 1 | **`notion-query-database-view` は存在しない** | `notion-query-data-sources` を使う |
| 2 | **Board ビュー（`view://fccc968f-...`）は存在しない** | STEP 3C の2つと All Tasks・My Tasks だけが実在 |
| 3 | **`Blocked` というステータスは無い** | STEP 4 の6つ |
| 4 | **`Projects` は rollup。値が読めない**（`rollupResult://...` が返る） | **`Epics`（relation）を使う** |
| 5 | **列名が変わる**。期限は `Due by`→`Due Date`→`Due by`、`[PJ]Epics`→`Epics`。旧 SQL はそのたびに失敗した | STEP 2 で `<sqlite-table>` と照らす |
| 6 | 引数なしで全件（数百件）を出すと、誰も読まない | 空欄なら誰のタスクかを聞く（STEP 1） |
| 7 | `notion-get-users` に出てこない担当者がいる（ゲスト・退出者） | 名前では引けない。全員サマリに `不明(<ID先頭8桁>)` で出る |

**この skill を直したら、実際に1回叩いて件数が返ることを確認すること。**
