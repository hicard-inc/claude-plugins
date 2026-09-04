# hicard-inc/claude-plugins

株式会社hicard の **Claude Code 設定（Skill・MCP）の配布元**。
Claude Code の plugin marketplace として動く。

🔒 **private リポジトリ。**インストールした人のマシンに**この中身が丸ごと落ちる**ので、
**個人名・報酬・契約・評価・財務の実データは絶対に入れない**（→ [CONTRIBUTING.md](CONTRIBUTING.md)）。

## 導入（メンバー各自が1回だけ）

**ターミナルで**（Claude Code の中ではなく）：

```bash
claude plugin marketplace add hicard-inc/claude-plugins
claude plugin install hicard@hicard-plugins
```

そのあと `claude` で立ち上げて：

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

**ターミナルで**（Claude Code を閉じてから）：

```bash
claude plugin marketplace update hicard-plugins
claude plugin update hicard@hicard-plugins
```

**2行で一組。**1行目で配布元を取り直し、2行目で入れ直す。
1行目を飛ばすと、**新しい版が出ていても `already at the latest version` と言われる。**

🔴 **`/plugin` を開かない。上のシェル版だけを使う。**

Claude Code 2.1.260 の `/plugin` は**引数を取らず、対話ブラウザが開くだけ**
（VSCode 拡張ではこの `/plugin` 自体が使えない）。**しかも危険なのは開いたあと。**

**一覧で Enter を押すと、選択中の plugin がその場でインストールされる。**
2026-09-04 に zono のマシンで**意図しない plugin が2つ入った**（実測）:

| 入ったもの | 常時コスト |
|---|---|
| `superpowers@claude-plugins-official`（Skill 14本） | **~690 tok/セッション** |
| `code-review@claude-plugins-official` | ~22 tok/セッション |

`hicard` plugin 自体の常時コストが **~314 tok** なので、**その2倍が意図せず乗っていた。**
`/plugin update ...` と打った結果として一覧が開き、そのまま Enter を押した形。

**入ってしまったら外す**（何が入っているかは `claude plugin list`）:

```bash
claude plugin uninstall <plugin>@<marketplace>
```

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
