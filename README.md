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

**インストール先は user スコープでも local スコープでも構わない。**
`~/.claude/settings.json` を触りたくない人は、そのプロジェクトの `.claude/settings.local.json`
に入る local スコープでよい（2026-09-05 実測で両方通る）。

### 前提条件（🔴 `gh auth login` では足りない）

| | 何が要るか | 無いとどうなるか |
|---|---|---|
| **SSH 鍵** | GitHub に登録済みの SSH 鍵 | 🔴 **`marketplace add` は `git@github.com:...` で clone する**（2026-09-05 実測）。`gh` の認証は https なので効かず、`Permission denied (publickey)` で止まる。`ssh -T git@github.com` が名前を返すことを先に確認する |
| **2FA** | 🔴 **認証アプリかパスキー。**hicard-inc は「セキュアな2FA必須」で **SMS は不可** | Org のリポジトリ操作が **403** になる（2026-09-05 実測）。**管理者側では直せない。**本人が GitHub の設定で切り替える |
| **collaborator** | `claude-plugins` への read 権限 | `Repository not found` |
| **Node.js / npm** | `/slides` を使うときだけ | `node: command not found`。`/setup` には要らない |

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

🔴 **本人のアカウントとして入る。**サービスアカウント鍵・Notion Integration トークンは
**この配布物に一切含まれない**（理由は [plugins/hicard/skills/setup/access_model.md](plugins/hicard/skills/setup/access_model.md)）。
見える範囲は本人の権限そのままなので、**この plugin を入れても新しい権限は増えない。**

### 🔴 Google ドライブ・スプレッドシートは配れない（0.1.7 で外した）

0.1.6 まで `gdrive`（`drivemcp.googleapis.com`）と `gsheets`（`sheetsmcp.googleapis.com`）を
同梱していたが、**誰の環境でも一度も繋がっていなかった。**
2026-09-05 に2台（zono・ishikawa）で `claude mcp list` が同じものを返す：

```
plugin:hicard:gdrive:  ✘ Failed to connect — Incompatible auth server: does not support dynamic client registration
plugin:hicard:gsheets: ✘ Failed to connect — Incompatible auth server: does not support dynamic client registration
```

Google の MCP は**事前登録された OAuth クライアント**を要求し、動的登録（DCR）を受け付けない。

**claude.ai の「コネクタ」なら通る**（Anthropic が登録済みのクライアントを使う）。
🔴 **ただしその経路は plugin から配れない。**`.mcp.json` に書ける `type` は
`stdio` / `sse` / `http`（`streamable-http`）の**3種だけ**で、コネクタが使う内部の種類は書けない
（Claude Code 2.1.260 で実測）。

→ **ドライブは各自が claude.ai 側でコネクタを有効にする。**`/setup` は
検索ツールが在るかを見て、無ければ**本人の権限の問題ではないと明示して管理者へ回す。**

事前登録クライアントを書く道は残っている（`.mcp.json` の `oauth` は
`clientId` / `clientSecret` / `clientSecretHelper` / `authorizationUrl` / `tokenUrl` / `scope` 等を取る）。
**ただし Google が第三者にこの用途のクライアント登録を開放しているかは未確認**で、
`clientSecret` を配布物に入れることになるため採らなかった。

## 構成

```
RULES.md                            ← 運用ルール。/setup が ~/.claude/rules/ へ symlink する
.claude-plugin/marketplace.json     ← marketplace の定義
plugins/hicard/
  .claude-plugin/plugin.json        ← plugin の定義
  .mcp.json                         ← 配る MCP サーバー（notion のみ）
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
