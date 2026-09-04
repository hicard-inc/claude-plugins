# hicard-inc/claude-plugins

株式会社hicard の **Claude Code 設定（Skill・MCP）の配布元**。
Claude Code の plugin marketplace として動く。

🔒 **private リポジトリ。**インストールした人のマシンに**この中身が丸ごと落ちる**ので、
**個人名・報酬・契約・評価・財務の実データは絶対に入れない**（→ [CONTRIBUTING.md](CONTRIBUTING.md)）。

## 導入（メンバー各自が1回だけ）

```
/plugin marketplace add hicard-inc/claude-plugins
/plugin install hicard@hicard-plugins
```

そのあと **Claude Code を再起動**（`/exit` → `claude`）してから：

```
/setup
```

`/setup` が Notion と Google ドライブへの接続を最後まで通し、**実際に中身が読めることを確かめる**。

`/setup` は**運用ルール（[RULES.md](RULES.md)）を `~/.claude/rules/hicard.md` に置くところまでやる**。
🔴 **プラグインは道具しか配れない。**Claude Code の仕様上、plugin から `CLAUDE.md` と
許可設定（`permissions`）は配布できないので、**ルールはこの経路で入れる**。

> private リポジトリなので、`marketplace add` には GitHub の認証が必要。
> 通らないときは `gh auth login` を実行する。

## 更新（月1回くらい）

```
/plugin marketplace update hicard-plugins
/plugin update hicard@hicard-plugins
```

**2行で一組。**1行目で配布元を取り直し、2行目で入れ直す。
1行目を飛ばすと、**新しい版が出ていても `already at the latest version` と言われる。**

**ルールは1行目だけで最新になる。**`~/.claude/rules/hicard.md` は配布元の
[RULES.md](RULES.md) への symlink なので、版番号を上げなくても更新が届く。

🔴 **さらに、更新だけでは差し替わらない。**動いているセッションは古いまま走り続ける。
**`/exit` → `claude`（または `/reload-plugins`）までが一組。**

## 中身

| Skill | 何をするもの | 起動 |
|---|---|---|
| `setup` | hicard の Claude を使えるようにする（Notion・Google ドライブの接続を通す） | `/setup`（**人が呼ぶだけ**） |
| `research` | 調査を始める前・レポートを出す前に踏む手順 | `/research` ／ Claude の自己判断でも起動する |
| `slides` | 登壇・社内共有のスライドを1本作る手順 | `/slides`（**人が呼ぶだけ**） |
| `tasks` | Notion `[PJ] Tasks` の状況を見る | `/tasks` ／ Claude の自己判断でも起動する |

配っている MCP サーバー（[plugins/hicard/.mcp.json](plugins/hicard/.mcp.json)）:

| 名前 | 実体 | 認証 |
|---|---|---|
| `notion` | `https://mcp.notion.com/mcp` | **各自の OAuth**。鍵は配らない |
| `gdrive` | `https://drivemcp.googleapis.com/mcp/v1` | **各自の OAuth**。鍵は配らない |
| `gsheets` | `https://sheetsmcp.googleapis.com/mcp/v1` | **各自の OAuth**。鍵は配らない |

🔴 **3つとも本人のアカウントとして入る。**サービスアカウント鍵・Notion Integration トークンは
**この配布物に一切含まれない**（理由は [plugins/hicard/skills/setup/access_model.md](plugins/hicard/skills/setup/access_model.md)）。
見える範囲は本人の権限そのままなので、**この plugin を入れても新しい権限は増えない。**

## 構成

```
RULES.md                            ← 運用ルール。/setup が ~/.claude/rules/ へ symlink する
.claude-plugin/marketplace.json     ← marketplace の定義
plugins/hicard/
  .claude-plugin/plugin.json        ← plugin の定義
  .mcp.json                         ← 配る MCP サーバー
  skills/<名前>/SKILL.md            ← 本体。補助ファイルは同じフォルダに置く
hooks/                              ← pre-push hook の配布物（下記）
```

## このリポジトリを直す人へ

**粒度の基準（4層＋3関門）とレビュー手順は [CONTRIBUTING.md](CONTRIBUTING.md) が正本。**
**読まずに足すと必ず混ざる。**

`main` を守る仕組みは [hooks/](hooks/) にある（Free プランでは branch protection が使えないため）。
**clone した人が各自1回**これを有効にする：

```bash
git config core.hooksPath hooks
```

これで **`main` への直 push が止まり、シークレットらしき文字列の混入も push 前に検出される。**
