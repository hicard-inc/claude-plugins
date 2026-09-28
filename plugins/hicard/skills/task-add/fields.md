# task-add の参照資料（列の書式・SQL・理由）

`SKILL.md` は手順だけ。**ここは読まれるまで0トークン**なので、理由と実例はこちらに置く。

## 必須5列（STEP 1 で存在と型を見る）

| 列 | 型 | `notion-create-pages` の `properties` に書く値 |
|---|---|---|
| `Title` | title | `"〇〇を作る"` |
| `Assignee` | person | `"[\"user://<user id>\"]"`（**JSON 配列を文字列にしたもの**。複数可） |
| `Epics` | relation → [PJ] Epics | `"[\"https://app.notion.com/p/<32桁のID>\"]"`（**JSON 配列を文字列にしたもの**） |
| `Due Date` | date | `"date:Due Date:start": "2026-10-02"` と `"date:Due Date:is_datetime": 0` |
| `Status` | status | `"Not started"`（ほかに `Ready` / `In progress` / `Review`。`Done` `Archive` で作らない） |

## 任意の列（会話にあるときだけ入れる）

| 列 | 値 |
|---|---|
| `Priority` | `"⭐️⭐️⭐️"` / `"⭐️⭐️"` / `"⭐️"`（高い順） |
| `Start Date` | `"date:Start Date:start": "YYYY-MM-DD"`、`"date:Start Date:is_datetime": 0` |
| `Est. hours` | `"0.1h"` `"0.5h"` `"1h"` `"2h"` `"4h"` `"8h"` `"16h"` のどれか（それ以外は入らない） |
| `PR` | 広報に関わるタスクなら `"__YES__"`、それ以外は書かない |
| `URL` | 列名は `"userDefined:URL"` |
| `Notes` | 1〜2行の補足。本文に書けるものは本文へ |

**書かない列**: `ID`（自動採番）・`Projects`（rollup。Epic から自動で決まる）・`Parent Task` / `Sub Task`・`Actual hours`（実績は終わってから）。

## SQL

`Epics` は **URL の形が2種類ある**（`https://app.notion.com/p/<ID>` と `https://app.notion.com/<ID>`）。
一致を見るときは URL 全体ではなく **32桁の ID を `LIKE '%<ID>%'`** で当てる。

### Epic の検索（STEP 3）

```sql
SELECT url, "Name", "Status", "Updated"
FROM "collection://36827ee8-8d3d-4192-8103-63c06ac3a22e"
WHERE COALESCE("Status",'') NOT IN ('Done','Archive')
  AND "Name" LIKE ?
ORDER BY "Updated" DESC LIMIT 5
-- params: ["%<会話に出た固有名詞>%"]
```

手がかりが無いとき（自分が Lead・メンバーの Epic）：

```sql
SELECT url, "Name", "Status", "Updated"
FROM "collection://36827ee8-8d3d-4192-8103-63c06ac3a22e"
WHERE COALESCE("Status",'') NOT IN ('Done','Archive')
  AND ("Lead" LIKE ? OR "Assignees" LIKE ?)
ORDER BY "Updated" DESC LIMIT 5
-- params: ["%<自分の user id>%", "%<自分の user id>%"]
```

🔴 `Status` が空の Epic がある。`"Status" NOT IN (...)` だけだと**空の行が黙って落ちる**ので `COALESCE` を外さない。

### 重複チェック（STEP 5）

```sql
SELECT "userDefined:ID", "Title", "Status"
FROM "collection://633304e7-495e-4a00-a41e-d53e369dc238"
WHERE "Epics" LIKE ? AND "Title" = ?
  AND COALESCE("Status",'') NOT IN ('Done','Archive')
-- params: ["%<Epic の32桁ID>%", "<Title>"]
```

### 作成後の確認（STEP 7）

```sql
SELECT "userDefined:ID", "Title", "Status", "Assignee", "Epics", "date:Due Date:start"
FROM "collection://633304e7-495e-4a00-a41e-d53e369dc238"
WHERE url LIKE ?
-- params: ["%<作成したページの32桁ID>%"]
```

`userDefined:ID` は数字で返る。画面の表示は `TAS-<数字>`。

## なぜこの5つが必須か

- **Title・Assignee・Epics**: 無いと「誰の・どの仕事か」が分からず、`My Tasks`・`By Project` ビューに出てこない
- **Due Date**: 無いと期限切れの警告（`tasks` スキル）が効かない。以前は期限の入っていないタスクが多数を占めていたので、起票の入口で揃える
- **Status**: 空だとステータス別の集計で「未設定」に落ちる。既定値 `Not started` で埋めるので、本人に手間は掛からない

任意項目を聞かないのは、**聞く項目が増えるほど起票そのものをしなくなる**から。入れたければ会話で言えば入る。

## 踏んだ穴

| # | 事実 | どうする |
|---|---|---|
| 1 | Tasks の期限の列は `Due Date`。**`Due by` は Epics 側の列**（名前が似ている） | STEP 1 で列名を実物と照らす |
| 2 | Epic の列は `Epics`。以前は `[PJ]Epics` という名前だった | 同上。古い名前で書かない |
| 3 | テンプレート（`template_id`）と本文（`content`）は同時に指定できない | テンプレートは使わず、同じ見出しを本文に書く |
| 4 | 曜日から日付への変換を暗算すると1日ずれる | `date` か `python3` で確かめてからプレビューに出す |
