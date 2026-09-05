# 困ったとき（症状別）

`setup` skill の補助資料。**症状から引く。**表に無い症状は、推測で答えず管理者に回す。

**見える範囲は、あなたの Notion / Google アカウントの権限そのままです。**
共有されていないものが見えないのは不具合ではありません。

## Claude Code が起動しない・コマンドが無い

| 症状 | 原因 | 対処 |
|---|---|---|
| `claude: command not found` | インストーラが `~/.local/bin` に置いたが、そこが PATH に無い | `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` → ターミナルを**閉じて開き直す** |
| 何度やっても `command not found` のまま | **zsh 以外のシェルを使っている**（設定を書く先が違う） | `echo $SHELL` を実行して、出た文字を管理者に伝える |
| インストールのあとも `command not found` | インストールが途中で失敗している | もう一度インストールする。それでも駄目なら管理者に連絡 |
| ログインで弾かれる | 無料プラン、または API キーを選んだ | **Pro / Max** が要る。選び直しは `/login` |
| 開発ツールのインストールが失敗した | 回線・空き容量 | 空き容量を確認してやり直す。30分以上進まないなら管理者に連絡 |
| `xcode-select --install` で何も起きない | 前回の途中経過が残っている | 管理者に連絡（手で消すのは危険） |

## プラグイン（skill が古い・存在しない）

| 症状 | 原因 | 対処 |
|---|---|---|
| **Claude が `/setup` を知らない** | プラグインが未導入 | ターミナルで `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 claude plugin marketplace add hicard-inc/claude-plugins` → `claude plugin install hicard@hicard-plugins` → **`claude` で立ち上げ直す** |
| **Claude の言うことが手順書と違う** | プラグインが古い | ターミナルで `claude plugin update hicard@hicard-plugins` → **`claude` で立ち上げ直す** |
| 更新したのに変わらない | **動いているセッションは古いままで走り続ける** | `/exit` → `claude`。**更新と再起動までが一組**。`/reload-plugins` でも差し替わる |
| **`/plugin update ...` と打ったら一覧が開いただけ** | 🔴 **`/plugin` は引数を取らない**（2.1.260 実測）。VSCode 拡張では `/plugin` 自体が使えない | **ターミナルで `claude plugin update hicard@hicard-plugins`。開いた一覧はそのまま閉じる**（下の🔴を読む） |
| **知らない Skill が増えている・常時トークンが増えた** | 🔴 **`/plugin` の一覧で Enter を押してインストールしてしまった**（2026-09-04 実測） | `claude plugin list` で確認し、`claude plugin uninstall <plugin>@<marketplace>` で外す |
| **Claude が秘密鍵（`.env` / `google_credentials.json`）を要求してくる** | 鍵を全員に配っていた頃のルールで動いている | プラグインを更新して再起動する。**鍵は要らない**（→ `access_model.md`） |
| **`marketplace add` が `Permission denied (publickey)`** | 🔴 **先頭の `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` を付けずに打った。**既定は SSH clone（`git@github.com:...`・2026-09-05 実測）。**`gh auth login` は https なので関係ない** | `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 claude plugin marketplace add hicard-inc/claude-plugins` で打ち直す。**SSH 鍵は作らせない**（public なので鍵もアカウントも要らない） |
| **`gh` は通っているのに 403 が出る**（`gh repo view` 等） | 🔴 **hicard-inc は「セキュアな2FA必須」で SMS は不可。**SMS だけの人は Org のリポジトリに一切触れない（2026-09-05 実測） | **本人が GitHub の2段階認証を認証アプリかパスキーに変える。**設定 → Password and authentication。**管理者側では直せない** |
| `Repository not found` | **つづりの間違い**（このリポジトリは public なので、権限が無くて出ることはない） | `hicard-inc/claude-plugins` を打ち直す |
| **`~/.claude/settings.json` を触られたくない** | 既定は user スコープ | **local スコープでよい。**そのプロジェクトの `.claude/settings.local.json` に入るだけで、機能は同じ（2026-09-05 実測） |

🔴 **更新だけでは直らない。閉じて開き直すまでが一組。**
古いまま使うと、Claude は古いルールで動く。**本人にも Claude にも「古い」と気づく手立てが無い**（画面には何も出ない）。
**更新は自動で届く**（`/setup` 1-3 で貼る設定に `autoUpdate` が入っている・反映は次の起動）。`check_setup.sh` の「自動更新」が ❌ の人だけ、
月に1回ターミナルで `claude plugin marketplace update hicard-plugins` → `claude plugin update hicard@hicard-plugins`。

### 🔴 `/plugin` を開かせない（2026-09-04 実測）

**一覧で Enter を押すと、選択中の plugin がその場で入る。**
2026-09-04 に管理者のマシンで `superpowers`（Skill 14本・**~690 tok/セッション**）と
`code-review` が意図せず入った。どちらも `/plugin update ...` と打って一覧が開き、
**そのまま Enter を押した結果**。`hicard` 自体が ~314 tok なので、その2倍が乗っていた。

**画面には「意図せず入った」と出ない。**気づく手立ては `claude plugin list` を見ることだけ。

| | |
|---|---|
| **本人に言うこと** | **`/plugin` は打たない。**導入も更新もターミナルの `claude plugin ...` でやる |
| **開いてしまったら** | **何も選ばずに閉じる**（`Esc`）。Enter を押さない |
| **入ってしまったら** | `claude plugin list` で見て `claude plugin uninstall <plugin>@<marketplace>` |
| **なぜ気にするか** | 常時コストが増えるだけでなく、**入れた plugin の Skill が hicard のルールと競合しうる**（同じ場面で別の手順を主張する） |

## 🔴 接続の状態は4種類ある（`claude mcp list` の読み方・2026-09-05 実測）

**`✘` を全部同じ「壊れている」で扱わない。**本人が直せるものと、どうやっても直せないものが混ざっている。

| 表示 | 何が起きているか | 本人が直せるか | やること |
|---|---|---|---|
| `✔ Connected` | 接続だけは成立した | — | 🔴 **これを合格の理由にしない。**中身が読めたかで判定する（`SKILL.md` の 4） |
| `! Needs authentication` | **まだ一度も認可していないだけ。初回は全員これ** | ✅ 直せる | `/mcp` を開いて認可する |
| `✘ Failed to connect — Incompatible auth server: does not support dynamic client registration` | 相手が**事前登録された OAuth クライアント**を要求している | ❌ **直せない** | 下の「なぜドライブは配れないのか」 |
| `✘ Failed to connect — CONNECTION_CLOSED` | **`stdio` のサーバーが起動に失敗した**（ログがどこにも残らない。**起動直後だけの一過性もある**） | ✅ 直せることが多い | **まず `claude mcp list` を打ち直す。**2回続けて落ちたら下の「`CONNECTION_CLOSED` のとき」 |

🔴 **`! Needs authentication` を「繋がらない」と報告しない。**認可すれば通る状態で、`✘` とは別物。

**認可すると `✔ Connected` に変わる**（2026-09-05 実測。`plugin:hicard:notion` と
`plugin:figma:figma` の2本で確認）。**`/mcp` で認可するだけで、再起動も設定の変更も要らない。**

### 🔴 `claude mcp list` は、打った場所で結果が変わる

**同じマシンの同じ時刻に、別の結果が出る**（2026-09-05 実測）。

```
# ホーム（cd ~）で実行
plugin:hicard:notion: https://mcp.notion.com/mcp (HTTP) - ! Needs authentication

# .mcp.json を持つリポジトリの中で実行
notion: https://mcp.notion.com/mcp (HTTP) - ✔ Connected      ← リポジトリ側の設定。plugin のものではない
```

**リポジトリの `.mcp.json` に同じ名前のサーバーがあると、plugin 側がその名前ごと隠れる。**
別名の plugin サーバー（`plugin:figma:figma`）は両方に出るので、
**「プロジェクトの中では plugin の MCP が無効になる」わけではない。名前がぶつかっているだけ。**

→ 🔴 **plugin の状態を見るときは、`cd ~` してから `claude mcp list` を打つ。**
リポジトリの中で見た `✔ Connected` を、plugin が繋がった証拠にしない。

**中身が同じなら、リポジトリ側の重複定義を消して plugin 側に一本化する。**
上の例は `.mcp.json` の `notion` が plugin と**同じ URL・同じ `type`** だったので、リポジトリ側を消した。
消したあとは**どのディレクトリで打っても同じ結果**になる（2026-09-05 実測）：

```
plugin:hicard:notion: https://mcp.notion.com/mcp (HTTP) - ✔ Connected
```

⚠️ **消す前に、そのサーバーのツール名を名指ししている設定が無いか探す。**
plugin 経由は `mcp__plugin_<plugin>_<server>__<tool>`、プロジェクト経由は `mcp__<server>__<tool>` で、
**名前が変わる。**`allowed-tools` などに書いてあると**そのツールだけ黙って使えなくなる。**

### `CONNECTION_CLOSED` のとき（`stdio` の起動失敗を目で見る）

🔴 **最初にやることは、診断ではなく `claude mcp list` を打ち直すこと。**
**起動直後だけ落ちて、その後は何もせず繋がる場合がある**（2026-09-05 実測）。
セッション開始時に `google-sheets (CONNECTION_CLOSED)` と出た同じマシンで、
**1分後に打ち直したら `✔ Connected` だった。設定も鍵も何も変えていない。**

`uvx` / `npx` のように**起動のたびにパッケージを取りに行く**書き方だと、
初回の解決が Claude 側の待ち時間に間に合わないことがある（**推定**。待ち時間の値は未確認）。

→ **打ち直して繋がったら、そこで終わり。**下の手順に進むのは**2回続けて落ちたとき**だけ。
🔴 **1回の失敗で `.mcp.json` を書き換えない。**直っていないものを直したと記録することになる。

**2回続けて落ちたとき:**

**`stdio` のサーバーは、プロセスが起動に失敗してもログがどこにも残らない。**Claude 側には接続断としか見えない。
**`.mcp.json` に書いてある `command` と `args` をそのまま手で実行して stderr を読む**のが、原因を見る唯一の方法。

```bash
# .mcp.json のあるディレクトリで。<サーバー名> は claude mcp list に出ている名前
python3 - '<サーバー名>' <<'EOF' > /tmp/run_mcp.sh
import json, shlex, sys
d = json.load(open(".mcp.json"))["mcpServers"][sys.argv[1]]
env = " ".join("%s=%s" % (k, shlex.quote(v)) for k, v in d.get("env", {}).items())
print("#!/bin/sh")
print("exec env %s %s %s" % (env, shlex.quote(d["command"]),
                             " ".join(shlex.quote(a) for a in d["args"])))
EOF
sh /tmp/run_mcp.sh < /dev/null      # ← ここに出る stderr が原因
```

🔴 **打ち直さず、ファイルから組み立てる。**手で打ち直すと、`.mcp.json` の中身ではなく
**自分が正しいと思っている中身**を試すことになる。

**実際に出た例**（2026-09-05・hicard の別リポジトリの Google Sheets サーバー）:

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

**原因は上流の破壊的変更だった。**パッケージを `@latest` で指していたので**起動のたびに依存が解決し直され**、
作者が想定していない新しい版を引いていた。**版を固定して直った。**

🔴 **`CONNECTION_CLOSED` を見て「権限が無い」「相手のサーバーの障害」と決めつけない。**
このときも会社側の制限を疑ったが、**同じ鍵で API 自体は通っていた。**起動していなかっただけ。

→ **`.mcp.json` に外部パッケージを書くときは版を固定する**（`@latest` を使わない）。

## Notion

| 症状 | 原因 | 対処 |
|---|---|---|
| Notion は繋がったのに hicard が見えない | 許可のとき**個人のワークスペース**を選んだ | Claude に「Notion を繋ぎ直したい」と言う。認可をやり直し、**「hicard」を選ぶ** |
| 一部のページだけ見えない | **まだ共有されていない**（正常） | 管理者に共有を依頼。**設定では直らない** |
| Notion のツールがそもそも出てこない | プラグイン未導入・未再起動 | 上の「プラグイン」の表へ |
| `claude mcp list` に `plugin:hicard:notion: ! Needs authentication` と出る | **まだ認可していないだけ**（初回は全員これ） | `/mcp` を開いて認可する。**`✘` ではないので「繋がらない」と報告しない**。上の「接続の状態は4種類ある」 |

## Google ドライブ

### 🔴 なぜドライブは配れないのか（2026-09-05 実測・0.1.7 で外した）

0.1.6 まで `.mcp.json` に `gdrive` / `gsheets` を同梱していたが、**誰の環境でも一度も繋がっていなかった。**
Owner 2名のマシンで `claude mcp list` が同じものを返す：

```
plugin:hicard:gdrive:  ✘ Failed to connect — Incompatible auth server: does not support dynamic client registration
plugin:hicard:gsheets: ✘ Failed to connect — Incompatible auth server: does not support dynamic client registration
```

Google の MCP は**事前登録された OAuth クライアント**を要求し、動的登録（DCR）を受け付けない。
claude.ai の「コネクタ」は Anthropic が登録済みのクライアントを使うので通るが、
**その経路は plugin から配れない**（`.mcp.json` に書ける `type` は `stdio` / `sse` / `http` の3種だけで、
コネクタが使う内部の種類は書けない。Claude Code 2.1.260 で実測）。

→ **ドライブは claude.ai のコネクタで各自が有効にする。**この手順書からは配らない。
⚠️ **claude.ai 側の画面の順番は未実測。**思い出しで案内せず、管理者に回す。

| 症状 | 原因 | 対処 |
|---|---|---|
| **ドライブの検索ツールが1つも出てこない** | claude.ai のコネクタが有効になっていない | 本人に `/mcp` を打ってもらい `claude.ai Google Drive` の行があるか見せてもらう。無ければ `google_drive.md` の「コネクタが無い人」へ（**A: まだ有効にしていない／B: 組織側で禁止**の2通りある） |
| **他社のドメインの Google アカウントで、コネクタを有効にできない** | 🔴 **その会社の Workspace 管理者が third-party 連携を止めている**（2026-09-05 実測） | ❌ **本人にも hicard にも直せない。**「有効にしてください」と言わない。`Drive:利用不可（アカウントの組織側で禁止）` として閉じる |
| **`plugin:hicard:gdrive` が ✘ と出ている** | **0.1.6 以前の古い版**。0.1.7 で外した | `claude plugin marketplace update hicard-plugins` → `claude plugin update hicard@hicard-plugins` → 再起動 |
| **繋がっているのにツールが無い** | 🔴 **セッションによって出る／出ないが実際にある**（2026-09-05 実測） | `/exit` → `claude` で入り直してもう一度見る。**1回で「未接続」と決めない** |
| ドライブは繋がったのに hicard が見えない | **個人アカウントで許可してしまった。**許可の画面は、ブラウザにログイン中のアカウントを既定で使う | 下の「Google アカウントの繋ぎ直し」 |
| **個人の Google アカウントも一緒に使いたい** | **できない。**Claude に繋げる Google アカウントは**1つだけ** | **Claude のログインは個人のままで構わない**（別物・**追加の課金もない**）。仕事で個人ドライブのファイルが要るときは、**フォルダを右クリック →「共有」→ 会社アドレスを編集者で追加**する。**フォルダごと共有すれば中身は全部読める**（あとから追加したものも） |
| **切り替えたら個人ドライブが読めなくなった** | 正常。上と同じ理由 | **繋ぎ直す必要はない。**要るフォルダを上のやり方で共有する |
| 一部のファイルだけ見えない | まだ共有されていない（正常） | 管理者に共有を依頼 |
| Google のログインで会社の認証画面が出た | SSO | 普段のやり方でログイン。分からなければ管理者に連絡 |
| Google の招待メールが来ない | **グループ追加はメールが来ないことがある** | 管理者に「`all@hicard.studio` に入れましたか」と聞く |

### Google アカウントの繋ぎ直し

🔴 **頼む「前」に、失うものを自分から言う。**聞かれてから答えると、
**本人は「黙って不便にされた」と受け取る。**多くの人が同じところで引っかかる。

> **切り替えると、いま繋がっている個人アカウントのドライブは Claude から読めなくなります。**
> **Claude に繋げる Google アカウントは1つだけ**で、両方は繋げません（Claude の仕様です）。
> **個人のドライブ自体は普段どおり使えます。**Claude のログインも今のままで、追加の課金もありません。
> **仕事で使っているファイルが個人のドライブにあるなら、先に共有しておいてください。**

手順（アドレスは実物で埋めて渡す）：

> Google Drive の接続を**いったん「切断」** → もう一度「接続」→
> **「別のアカウントを使用」から `<会社のアドレス>` を選ぶ**

🔴 **切断を飛ばさない。**繋がったまま「接続」を押しても、**アカウントを選ぶ画面が出ずに同じアカウントで通る。**

共有のやり方（本人に渡す）：

> Google ドライブでフォルダを右クリック →「共有」→ `<会社のアドレス>` を入れて「編集者」→ 送信。
> **フォルダごと共有すれば、中のファイルは全部読めます。**あとから追加したものも読めます。

**「あとで気づいた」も普通に起きる。**そのときは同じ手順で共有すればよい（**繋ぎ直しは要らない**）。

## スライド（`/slides`）が動かない

| 症状 | 原因 | 対処 |
|---|---|---|
| `node: command not found` | 🔴 **`/slides` は Node.js が必須**（`check_setup.sh` では【任意】と出るが、それは `/setup` に要らないという意味） | Node.js を入れる（`brew install node`、または https://nodejs.org の LTS）。**`node --version` と `npm --version` の両方が返るまで確認する** |
| `Cannot find module 'playwright-core'` | 依存が未インストール | `npm install --prefix "${CLAUDE_PLUGIN_ROOT}/skills/slides/scripts"` |
| `Chromium が見つかりません` | 描画用ブラウザ本体が未インストール | `npx playwright install chromium`（初回だけ・約15秒・約560MB） |

## 会話中の操作

| 症状 | 原因 | 対処 |
|---|---|---|
| Claude が「実行してよいですか」と聞いてきた | 正常 | 矢印キーで **Yes** を選んで Enter。セットアップ中に出るものは全部実行して大丈夫 |
| 日本語が途中で送信されてしまった | 変換の Enter で送信された | **コピペする。**打つなら、文字の下線が消えてから Enter |
