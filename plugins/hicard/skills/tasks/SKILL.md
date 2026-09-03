---
name: tasks
description: Notion [PJ] Tasks の状況を確認する。フィルタ指定で担当者・プロジェクト・ステータス別に表示できる
argument-hint: "[フィルタ: 担当者名 / プロジェクト名 / ステータス / 空欄=全件]"
---

# タスク確認: $ARGUMENTS

**すべての値は 2026-08-21 に実測して確認済み。**推測で書き換えないこと。

| | |
|---|---|
| Database | `https://app.notion.com/p/8dac7c0c458242f3a3ff29a3c55b6f85` |
| **data source** | **`collection://633304e7-495e-4a00-a41e-d53e369dc238`** |
| 件数 | 294 件（2026-08-21 実測。**数百件あるので `page_size: 100` では1ページに収まらない**） |

## STEP 1｜データ取得

**`notion-query-data-sources` を使う。**
（旧 `notion-query-database-view` は**廃止済みで存在しない**。2026-08-21 に踏んだ）

🔴 **Notion のツール名は環境によって前置きが変わる**（プラグイン経由なら `mcp__plugin_hicard_notion__`、
claude.ai コネクタ経由なら `mcp__claude_ai_Notion__`）。**素の名前で決め打ちせず、先に読み込む**：

```
ToolSearch  query: "+notion query data sources users"
```

### 引数なし／プロジェクト別 → ビューモード

```
notion-query-data-sources
  data: {"mode":"view","view_url":"<下の表の URL>","page_size":100}
```

| 引数 | 使うビュー | view_url |
|---|---|---|
| 空欄・その他 | **All Tasks** | `https://www.notion.so/8dac7c0c458242f3a3ff29a3c55b6f85?v=3adc0c27-b8ad-469a-b5f0-93d5a489ce9e` |
| 「自分の」「my」 | **My Tasks**（`Assignee = me` で絞られている） | `...?v=3ab521c2-efa0-43b9-867e-6a9a5afed312` |
| 「プロジェクト別」 | **By Project**（`[PJ]Epics` でグループ化） | `...?v=aeeae019-24c7-442a-a0ee-b970b5f4ca5a` |
| 「要記入」「抜け」 | **🔧 要記入（Epic / Status）** | `...?v=3c1c972c-2bcb-813f-bf5b-000cbb49bb6f` |

🔴 **「ボード」ビューは存在しない。**旧 skill にあった `view://fccc968f-...` は**実在しない ID**だった。
ステータス別に見せたいときは、All Tasks を取って STEP 3 で自分でまとめる。

### 担当者・ステータスで絞る → SQL モード

**`Assignee` は person 型で、返るのは名前ではなく user ID。**先に ID を引く。

```
notion-get-users   query: "<担当者名>"
```

そのうえで：

```
notion-query-data-sources
  data:
    data_source_urls: ["collection://633304e7-495e-4a00-a41e-d53e369dc238"]
    query: |
      SELECT "Title", "Status", "Priority", "userDefined:ID",
             "date:Due by:start" AS due, "[PJ]Epics"
      FROM "collection://633304e7-495e-4a00-a41e-d53e369dc238"
      WHERE "Assignee" LIKE ? AND "Status" NOT IN ('Done','Archive')
      ORDER BY due
    params: ["%<user id>%"]
```

## STEP 2｜フィルタ

$ARGUMENTS が空でなければ絞る。

**ステータスは次の6つだけ**（実測）：

```
Not started / Ready / In progress / Review / Done / Archive
```

🔴 **`Blocked` は存在しない。**旧 skill に書かれていたが、スキーマに無い。
**未設定（null）の行が5件ある**ので、集計では「未設定」として別に数える。

## STEP 3｜表示

```
| ID | タスク名 | ステータス | 優先度 | 担当者 | 期限 | Epic |
```

表の後に：
- 合計件数
- **ステータス別の内訳**（`Done` と `Archive` は最後に置く）
- **期限切れ**（`date:Due by:start` が今日より前で、`Status` が `Done`/`Archive` でないもの）があれば警告

## 踏んだ穴（2026-08-21 実測）

| # | 事実 | どうする |
|---|---|---|
| 1 | **`notion-query-database-view` は存在しない** | `notion-query-data-sources` を使う |
| 2 | **`view://fccc968f-...`（Board）は存在しない** | 上の表の4つだけが実在 |
| 3 | **`Blocked` というステータスは無い** | 上の6つ |
| 4 | **`[PJ]Projects` は rollup。値が読めない**（`rollupResult://...` が返る） | **`[PJ]Epics`（relation）を使う** |
| 5 | 日付は `Date` ではなく `date:Due by:start` で引く | SQL の列名は `<sqlite-table>` を見る |

**この skill を直したら、実際に1回叩いて件数が返ることを確認すること。**
