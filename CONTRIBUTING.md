# このリポジトリに足す・直すときの基準

**足す前にここを読む。**読まずに足すと、以前の状態に戻る
（＝手順・判断・実データ・個人の状態が同じファイルに混ざり、**共有すべきものが埋もれる**）。

---

## 0. まず：ここに入れてはいけないもの

plugin のインストールは **`git clone`**。**この中身はインストールした全員のマシンに落ちる。**
**public リポジトリ**（2026-09-05 から）なので、インストールしなくても誰でも読める。以下は入れない。**一度コミットすると履歴から消せない。**

| 入れない | 例 |
|---|---|
| **個人名と、その人の状態** | 「◯◯が担当」「◯◯の判断待ち」「◯◯のマシンにしかない」 |
| **報酬・評価・人事** | 按分％・報酬額・パフォーマンス評価・人事判断の記録 |
| **契約・取引先の実データ** | 契約先一覧・外注先・クライアント企業名の一覧 |
| **財務の実データ** | 予実・P/L・売上の数値、それらのシート ID |
| **シークレット** | トークン・秘密鍵・サービスアカウント JSON・その中身 |
| **クライアント案件の固有名詞** | 案件コード・案件名・ブランチ名に入った案件名 |

**判断に迷ったら入れない。**必要なら、その事実を**一般化した言い方**に書き換えてから入れる
（例：「Leo が最も嫌う」→「読み手の判断を誤らせる」）。

---

### RULES.md に書いてよいこと（2026-09-04 追加）

`RULES.md` は**メンバー全員の Claude が毎セッション読む**（`~/.claude/rules/hicard.md` 経由）。
**上の「入れてはいけないもの」より1段きつい基準を当てる。**

| 書く | 書かない |
|---|---|
| 守るべき振る舞い（何を確認し、何をやらないか） | **クライアント名・個人名・DB名・シート名・具体的なファイルパス・金額** |
| 一般的なサービス名（Notion / Google ドライブ / スプレッドシート） | 「誰が承認者か」の実名（「管理者」と書く） |

🔴 **ルール文書は「守るべきもの」を書くので、裏返すと「価値のあるものの地図」になる。**
固有名詞を入れた瞬間、**全員のマシンに機密の所在が平文で落ちる。**

**常時ロードされるので長さがそのままコストになる。**80行・5.5KB を上限の目安にする。

## 1. 粒度の基準：4層に分ける

**同じファイルに2つの層を混ぜない。**混ざったファイルは、必ずどちらの用にも使えなくなる。

| 層 | 何を書くか | どこに置くか | frontmatter |
|---|---|---|---|
| **判断・知識** | 「どう考えるか」。手順ではなく基準 | `skills/<名前>/SKILL.md` | 既定のまま（人も Claude も呼べる） |
| **実行** | 「何を順に叩くか」。副作用がある | `skills/<名前>/SKILL.md` | **`disable-model-invocation: true`** |
| **参照資料** | 理由・実例・症状別の対処表・作例 | `skills/<名前>/` 配下の別ファイル | なし（Markdown のみ） |
| **状態** | いま誰が何をしているか・現在の一覧・進捗 | **ここには置かない** | — |

🔴 **「Skill と Command は別の仕組み」ではない。**公式に統合済みで、
`commands/deploy.md` と `skills/deploy/SKILL.md` はどちらも `/deploy` になる。
**分けるのは置き場所ではなく frontmatter。**副作用のあるものに `disable-model-invocation: true` を付ける。

### 参照資料は「読まれるまでタダ」

`SKILL.md` は**一度読み込まれるとセッション中ずっとコンテキストに残る**。1行が毎ターンの費用になる。
一方、**同じフォルダの別ファイルは、実際に読まれるまで0トークン**。

→ **`SKILL.md` には「次に何をするか」だけを書き、理由・実例・対処表は別ファイルに出す。**
`skills/research/method.md`（40KB）や `skills/setup/troubleshooting.md` がその形。

---

## 2. サイズの基準（公式の制限）

| 基準 | 数字 | 破ると何が起きるか |
|---|---|---|
| `SKILL.md` の長さ | **500行以内** | 公式の推奨上限 |
| 再読み込み時の1 Skill あたり | **5,000トークン** | 要約後に**先頭5,000トークンだけ**が復元される。超えた分は落ちる |
| 再読み込みされる Skill 全体 | **25,000トークン** | 配っている Skill の合計がこれを超えると、どれかが落ちる |
| 参照資料 | **制限なし** | 読まれるまで0トークンなので大きくてよい |

**新しい Skill を足したら、測り直す。**目安で済ませない：

```bash
claude plugin details hicard    # 常時コストと、スキルごとの呼び出し時コストが出る（frontmatter からの見積もり）
claude -p "/skill-doctor" --output-format text   # 2.1.252 以降。system prompt に実際に載っている行のトークンと、直近7日の呼び出し回数
```

**2つは違うものを測っている。**`plugin details` は定義から見積もる。`/skill-doctor` は**今のセッションの
system prompt に載っている一覧行**を測るので、人が呼ぶだけの Skill（`disable-model-invocation: true` の
setup・slides）は一覧に載らず `-`（0）と出る（2026-09-05 実測: research ~20・tasks ~20・setup と slides は `-`）。
**常時コストの実測は `/skill-doctor`、呼び出し時コストは `plugin details`。**`/skill-doctor` は対話中に打つと
`/plugin` の Stats タブが開くので、🔴 **Enter を押さない**（一覧で Enter を押すと plugin が入る・7 章）。上の `-p` 版なら開かない。

現状の実測（**0.1.15**・2026-09-05）。**常時 ~322 トークン**、呼び出し時は
**setup ~4.6k** / slides ~4.6k / research ~2.9k / tasks ~2.1k ＝合計 ~14.2k。
全体の上限 25,000 は超えていない。

🔴 **setup は 0.1.11〜0.1.14 で上限 5,000 に到達していた**（表示 ~5k・6,645 字）。
[#18](https://github.com/hicard-inc/claude-plugins/pull/18) でドライブの合否判定を `google_drive.md` へ出し、
重複していた手順を削って **6,179 字・~4.6k に戻した。**余裕は ~400 トークン（≒500 字）。**次に足すときも参照資料へ。**
0.1.17 で自動更新と https clone の文言を足して **6,264 字・表示 ~4.7k**（`plugin details` 実測。上限まで残り ~440 字）。
経緯: 0.1.1 で 4.4k → 追記を重ねて 0.1.6 で **5.3k と上限を超えていた**（測るまで誰も気づいていない）。
[#6](https://github.com/hicard-inc/claude-plugins/pull/6) で参照資料（`google_drive.md`）を
切り出して 4.9k に戻し、0.1.7〜0.1.10 は**参照資料側だけを増やして 4.9k を維持していた。**
0.1.11 で `SKILL.md` に **101 文字**（許可設定を入れる節）を足したところ、**表示が ~5k に上がった。**

🔴 **文字数からトークンを見積もれる。**git 履歴の文字数と実測値を突き合わせると
**1文字 ≒ 0.74 トークン**（0.1.1=5,912字/4.4k、0.1.6=7,119字/5.3k、0.1.7=6,635字/4.9k、
0.1.8〜0.1.10=6,544字/4.9k、0.1.11〜0.1.14=6,645字/~5k、0.1.15=6,179字/4.6k）。
**`SKILL.md` が 6,700 字を超えたら 5,000 トークンを超える。**測る前にこれで当たりをつける。

🔴 **表示は 0.1k 刻みで丸められる。**0.1.8 で `SKILL.md` を 91 文字削ったが表示は 4.9k のまま動かなかった。
**「削ったのに減らない」は正常。**上限に近いスキルの増減は、表示ではなく**文字数で管理する。**

→ **setup に何か足すときは、`SKILL.md` ではなく参照資料に書く**
（`troubleshooting.md` / `google_drive.md` / `access_model.md`）。
0.1.9〜0.1.11 の追記の大半はこの形で、**参照資料に書いた分は常時コストも呼び出しコストも1トークンも増えていない。**

**How to apply: Skill に1行足したら測る。**行数や体感で判断しない。
`SKILL.md` を膨らませずに内容を足す方法は1つで、**参照資料に出して本文からポインタで指す**（1章）。

🔴 **`claude plugin details` は接続を確かめない。**0.1.6 では

```
MCP servers (3)  notion, gdrive, gsheets  (tool schemas resolved at runtime; not counted)
```

と出ていたが、そのうち**繋がっていたのは `notion` の1本だけだった。**
この行は **`.mcp.json` に3本書いてある**という意味でしかない。
**繋がっているかは `claude mcp list` でしか分からない**（`✔ Connected` が出た本数だけが稼働している）。

🔴 **`plugin.json` の `version` を上げないと、この数字も配布物も更新されない。**
`claude plugin update` は**版番号を見て判断する**ので、中身を直しただけでは
`already at the latest version` と言って何もしない。
**内容を変えたら `plugin.json` と `marketplace.json` の両方の `version` を上げる**（片方だけだと食い違う）。

**版を上げなくてよいのは `plugins/` の外だけ**（この `CONTRIBUTING.md` と直下の `README.md`）。
配布物に入らないので、直しても各自の環境には影響しない。

---

## 3. 配布可否の4関門（全部通らないものは配らない）

| # | 関門 | 落ちる例 |
|---|---|---|
| **1** | **2人以上が使うか** | 1人の文体を写すもの／管理者しか実行しないもの／経理担当だけのもの |
| **2** | **固有名詞・状態が本文に無いか** | 「現在のページ一覧（10人）」「◯◯の判断待ち」「クライアント企業26社の略号表」 |
| **3** | **自己完結しているか** | 配れないファイルを「方法論の正本」として参照しているもの／別リポジトリの `docs/` を読むもの |
| **4** | 🔴 **書いた本人が1回実行して、出力を見たか** | `--help` に載っているから動くはずのコマンド／`.mcp.json` に書いただけの接続／思い出しで書いた画面の手順 |

**関門1を飛ばすのが最も多い失敗。**「移しやすいか」ではなく「**2人以上が使うか**」で決める。

### 関門4（2026-09-05 追加・落ちた実績が3件あるので足した）

**「配布物に載せるコマンド・接続・画面の手順は、書いた本人が1回実行して、その出力を貼る。」**

| 配ったもの | 何が起きたか | 直した PR |
|---|---|---|
| 更新手順「`/plugin marketplace update` を実行」 | **`/plugin` は引数を取らない。**一覧が開くだけで、**Enter を押すと選択中の plugin がその場で入る**（管理者のマシンに `superpowers` が意図せず入った） | [#4](https://github.com/hicard-inc/claude-plugins/pull/4) [#5](https://github.com/hicard-inc/claude-plugins/pull/5) |
| MCP 3本（`notion` / `gdrive` / `gsheets`） | **`gdrive` / `gsheets` は2台とも一度も繋がっていなかった**（`Incompatible auth server: does not support dynamic client registration`）。**`.mcp.json` に書いたことを稼働の証明に使っていた** | [#6](https://github.com/hicard-inc/claude-plugins/pull/6) |
| ルールの確認手順「`/context` で見る」 | **`/context` はスラッシュコマンドで Claude 自身は実行できない。**さらに表示は symlink 名ではなく解決先のパス（正常な人が全員 ✘ と判定するところだった） | [#3](https://github.com/hicard-inc/claude-plugins/pull/3) [#6](https://github.com/hicard-inc/claude-plugins/pull/6) |

**3件に共通するのは「定義が存在すること」を「動くこと」の証明に使った点。**
`--help` に載っている・`.mcp.json` に書いてある・仕様上そう表示されるはず、はどれも証明ではない。

**関門4の通し方**（PR 本文に貼る）:

| 配布物の種類 | 実行するもの | 貼るもの |
|---|---|---|
| コマンド | そのコマンドをそのまま | 出力の先頭数行と終了コード |
| MCP サーバー | `claude mcp list` | `✔ Connected` の行 |
| Skill の手順 | 手順を上から1回 | 判定に使う行が実際に出たこと |
| 画面（claude.ai 等） | 実際に1回通す | 画面の順番。**通せないなら手順を書かず「管理者へ回す」で止める** |

🔴 **通せなかったときに、思い出しで手順を書かない。**
[#6](https://github.com/hicard-inc/claude-plugins/pull/6) で入る `skills/setup/google_drive.md` が実例で、
claude.ai 側の画面順が未実測なので**手順を書かず、管理者へ回す文面だけを置いてある。**
**空白のまま置くほうが、間違った手順より安い。**

### 実際に落ちたもの（同じ判断を繰り返さないための記録）

| 落ちたもの | どの関門 | 理由 |
|---|---|---|
| `sync-now` | **3** | スクリプトが読む設定ファイルに、実名・クライアント26社・財務シート ID が入っている。かつ Google の鍵が必要で、鍵は配らない |
| `lp` | **3** | 本文が「方法論は別ファイルが正本」と宣言していて、その正本にクライアント案件名が18箇所ある |
| 管理者向けの招待手順 | **1** | 実行するのは管理者だけ |
| 1Password での鍵配布設計 | **1・2** | 経理担当だけが使う。特定マシンの状態と個人の TODO が本文にある |
| GitHub 運用ルールの解説 | **2** | admin 権限者の実名と、人事判断への言及がある |

---

## 4. パスの書き方

**リポジトリ相対のパスを書かない。**plugin はどこにインストールされるか分からない。

| 書くもの | 書き方 |
|---|---|
| この plugin の中のファイル | `${CLAUDE_PLUGIN_ROOT}/skills/<名前>/<ファイル>` |
| 作業中のリポジトリの中 | 相対パスのまま（`docs/slides/<なまえ>.md` 等） |
| ホームディレクトリ | 書かない（`~/hicard` を前提にしない） |

**シェルスクリプトも同じ。**`${CLAUDE_PLUGIN_ROOT}` が入っていない前提でも動くよう、
`$(dirname "$0")` からのフォールバックを持たせる（`skills/setup/check_setup.sh` がその形）。

🔴 **絶対パスをハードコードしない。**移行前の `drift.js` は
`/Users/<個人名>/hicard/scripts/preview/node_modules/...` を `require` していて、
**本人以外のマシンでは必ず落ちた。**

---

## 5. MCP ツール名を frontmatter に書かない

plugin が配る MCP サーバーのツール名は **`mcp__plugin_hicard_<サーバー名>__<ツール名>`** に修飾される。
一方、claude.ai のコネクタ経由なら `mcp__claude_ai_Notion__...` になる。**環境で変わる。**

→ **`allowed-tools` に MCP ツール名を列挙しない。**
書くと、名前が違う環境で**そのツールだけ黙って使えなくなり、原因が分からない失敗になる。**
本文で `ToolSearch` を使って読み込ませる：

```
ToolSearch  query: "+notion query data sources users"
```

同じ理由で、Skill の frontmatter に `model:` を書かない（Skill の正式なフィールドではない）。

---

## 6. 直したら確かめる

1. **JSON を機械で検証する**（`marketplace.json` / `plugin.json` / `.mcp.json`）。
   壊れていると**インストール自体ができない**
2. **シェル・JS は構文チェックを通す**（`bash -n` / `node --check`）
3. **`${CLAUDE_PLUGIN_ROOT}` を除いた参照が実在するか**を確認する
4. **禁止語をスキャンする**（人名・報酬・契約・案件名）
5. **`version` を上げる**（`plugin.json` と `marketplace.json` の両方）。
   🔴 **#3〜#7 は5回続けて `plugin.json` しか上げておらず、`marketplace.json` は 0.1.2 で止まっていた。**
   覚えておく方式は既に失敗しているので、**`python3 hooks/check_versions.py` で機械が見る**
   （`git config core.hooksPath hooks` を入れてあれば push のときに自動で走って止まる）
6. **自分の環境に入れ直して、実際に動かす**
7. 🔴 **関門4を通す**（3章）。**書いたコマンド・接続・手順を自分で1回実行し、出力を PR 本文に貼る**

```bash
claude plugin validate .                        # marketplace の検証
claude plugin validate plugins/hicard           # plugin 単体の検証
claude plugin marketplace update hicard-plugins # 取り直す（マージ後は最初の指示から 10 分以内に自動でも届く・2026-09-05 実測）
claude plugin update hicard@hicard-plugins      # 入れ直す（restart が要る）
claude plugin details hicard                    # 構成とトークンを見る
claude mcp list                                 # 🔴 接続を確かめる（details では分からない）
python3 hooks/check_versions.py                 # 版が2箇所で食い違っていないか
```

```bash
# 4 と 3 をまとめて。リポジトリ直下で実行する
python3 - <<'PY'
import json, re, glob, os, sys
ng = 0
for p in ['.claude-plugin/marketplace.json'] + glob.glob('plugins/*/.claude-plugin/plugin.json') + glob.glob('plugins/*/.mcp.json'):
    try: json.load(open(p))
    except Exception as e: print('JSON 壊れ', p, e); ng += 1
# ${CLAUDE_PLUGIN_ROOT}/... の参照先が実在するか
for f in glob.glob('plugins/*/skills/**/*.md', recursive=True):
    root = f.split('/skills/')[0]
    for m in re.finditer(r'\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)', open(f, encoding='utf-8').read()):
        if not os.path.exists(os.path.join(root, m.group(1))):
            print('参照切れ', f, '->', m.group(1)); ng += 1
print('OK' if not ng else f'{ng} 件の問題')
sys.exit(1 if ng else 0)
PY
```

**`main` に直接 push しない。**PR にする。hook を有効にしていれば自動で止まる：

```bash
git config core.hooksPath hooks
```

---

## 7. このリポジトリの権限（2026-09-04 追加・2026-09-05 public 化で改訂）

**plugin のインストールは `git clone` で、更新は再 clone。**
つまり **ここに push できる人は、全メンバーの Claude に任意の Skill と MCP 設定を配れる。**
リポジトリの write 権限は、そのまま**全員の Claude を動かす権限**になる。

| | 決めごと |
|---|---|
| **読む（clone・インストール）** | **public。**誰でも読める。**新メンバーに招待は要らない**（GitHub アカウントも SSH 鍵も要らない。ただし `marketplace add` の既定は SSH clone なので、先頭に `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` を付ける。README 参照） |
| **write（push）** | **Org Owner のみ。**現在4名（実測 2026-09-04・全員2FA済み）。**collaborator も Org Member も足さない** |
| **メンバーの投稿（2026-11-12 追加）** | **fork から PR を出す**（9章・`/hicard:skill-submit`）。write は渡さない。**マージできるのは Owner だけなので、取り込むかは Owner が PR を見て決める**（承認数の必須化は入れていない＝2026-11-12 管理者決定。Owner 自身の PR が止まるため） |
| **`main` の保護（GitHub 側）** | **PR 必須・直接 push 禁止・force push 禁止・削除禁止・管理者にも適用**（`enforce_admins`）。2026-09-05 に設定し、API の GET で確認済み。**Owner でも `main` へは PR を経ないと入らない** |
| **clone したら1回** | `git config core.hooksPath hooks`。push 前に手元で**版の食い違いと鍵の混入**を見る。**public では push した瞬間に世界に見える**ので、push 前に止められるのはこの hook と下の Push protection だけ。PR テンプレートに有効化のチェック欄がある |
| **Claude Code から commit / push するとき（2026-09-06 追加）** | このリポジトリの `.claude/settings.json` に **project hook** が入っている。Claude Code をこのフォルダで起動すると、**開いた時点で `core.hooksPath` を自動設定**し、Claude が `git commit` / `git push` を打つ**直前に版・鍵・禁止語を検査して、落ちたらコマンドを止め、理由を Claude に返す**（Claude が本人に伝える）。手順は 8 章 |
| **Push protection（GitHub 側・2026-09-05 ON）** | Secret scanning ＋ Push protection。**既知の約 200 社のトークン形式は push 時にサーバー側で拒否**される（Owner・admin にも効く。バイパスは可能だが Security タブに記録が残る） |
| **必須チェック `checks`（Actions・2026-09-05 ON）** | PR ごとに `hooks/check_versions.py`・`hooks/check_secrets.py --all`・`hooks/check_blocklist.py`・**`claude plugin validate --strict`**（公式・2026-09-06 追加。`npm install -g @anthropic-ai/claude-code` してから plugin と marketplace の両方を検査。ログイン不要・実測）が走り、**落ちると `main` にマージできない**（branch protection の required status check）。ローカル hook と同じスクリプトなので判定はずれない。🔴 **fork からの PR では禁止語のステップだけ飛ばす**（GitHub は fork の `pull_request` に secret を渡さないので、BLOCKLIST が空で必ず落ちるため） |
| **必須チェック `blocklist`（Actions・2026-11-12 追加）** | `.github/workflows/blocklist.yml`。**`pull_request_target` で動くので fork の PR でも BLOCKLIST を使える。**🔴 安全条件: 実行するのは **main 側の** `hooks/check_blocklist.py` だけで、PR 側の中身は別フォルダに取って**読むだけ**（PR のコードは一切実行しない・書き込み権限なし・このファイル自体の変更は main に入るまで効かない）。**この条件を崩す変更（PR 側のスクリプトを実行する・`permissions` を広げる）は入れない** |
| **禁止語一覧 `BLOCKLIST`** | クライアント名・人名など「パターンで書ける不要な情報」の正規表現（`\|` 区切り・大文字小文字を区別しない）。🔴 **public なので一覧はリポジトリに置かず、Actions の secret に入れる**（`gh secret set BLOCKLIST -R hicard-inc/claude-plugins`・Owner だけが更新できる）。**空だとチェックは失敗する**（守っていない状態で通さない）。ログには当たった場所しか出ない。**一覧に無い語は通る**ので、文脈で決まる情報（報酬額・評価）は人のレビューで見る |
| **public に切り替えた理由** | private では Org Free の制約で branch protection が使えず（403）、新メンバーごとに outside collaborator の招待が要り、**招待前は誰も clone できなかった**。中身は最初から「全員のマシンに落ちる前提」で書いているので、公開範囲が広がっても入れてよいものの基準（0章）は変わらない |

**なぜ private に戻さないか**: 戻すと保護と Push protection が外れて招待が復活する。**戻す判断は Owner 4名で**。

🔴 **鍵が public に出たら、履歴を消しても fork とキャッシュに残る。**唯一の対処は**鍵そのものの無効化（ローテーション）**。
だから止める層は push の**前**に置く（hook・Push protection）。Actions は「`main` に入るのを止める」層で、push 後。

保護の現状を見るコマンド（Owner が実行する）：

```bash
gh api repos/hicard-inc/claude-plugins --jq '"private=\(.private) delete_branch_on_merge=\(.delete_branch_on_merge)"'
gh api repos/hicard-inc/claude-plugins/branches/main/protection \
  --jq '"pr_required=\(.required_pull_request_reviews != null) enforce_admins=\(.enforce_admins.enabled) force_push=\(.allow_force_pushes.enabled) deletions=\(.allow_deletions.enabled) checks=\(.required_status_checks.contexts)"'
gh api repos/hicard-inc/claude-plugins --jq '.security_and_analysis | "secret_scanning=\(.secret_scanning.status) push_protection=\(.secret_scanning_push_protection.status)"'
gh secret list -R hicard-inc/claude-plugins   # BLOCKLIST が並ぶこと（中身は見えない）
```

期待値: `private=false delete_branch_on_merge=true` / `pr_required=true enforce_admins=true force_push=false deletions=false checks=["checks","blocklist"]` /
`secret_scanning=enabled push_protection=enabled` / `BLOCKLIST`。

**禁止語で PR が落ちたとき**: ログの `path:line` を手元で開いて直す。語そのものを確認したいときは Owner に聞く（一覧は secret の中）。
テスト用の偽データなど正当な例外は、`check_secrets.py` は `ci:allow-secret` の注記で通せるが、**禁止語には例外の仕組みを作っていない**（例外を作ると一覧の意味が無くなる）。

## 8. Owner のセットアップ（Claude Code で commit / push する人向け・2026-09-06 追加）

7 章の GitHub 側の層は **push された後**に効く。public なので、**push した瞬間に世界に見える**ものを
push の前に止めるには、手元の層が要る。手元は Claude Code から git を打つのが普通なので、
**Claude Code の hook**（`.claude/settings.json`・リポジトリに入っている）で止める。

| 層 | いつ | 何を見る | 落ちたとき |
|---|---|---|---|
| Claude Code の `PreToolUse`（`hooks/claude_guard.sh`） | Claude が `git commit` / `git push` を打つ**直前** | 版の食い違い・鍵・禁止語（`git config hicard.blocklist`）・`--no-verify`・force | コマンドが実行されず、理由が Claude に返る |
| git の `pre-push`（`hooks/pre-push`） | 手打ちの push でも | 版・`main` 直 push・差分内の鍵 | push が止まる |
| GitHub（Push protection・Actions `checks`・branch protection） | push 後 | 既知のトークン形式・版・鍵・禁止語（`BLOCKLIST`）・plugin 定義（`validate --strict`） | `main` に入らない |

`.claude/settings.json` の `SessionStart` が `git config core.hooksPath hooks` を自動で入れるので、2層目の打ち忘れも無くなる。

### 手順（clone したあと Claude Code に貼る）

禁止語一覧は public のリポジトリに書けないので、**`.git/config` に置く**（commit されない・clone ごとに1回）。
一覧の中身は Owner 同士で別経路（Slack の DM など）で渡す。**この文書にもチャットログにも書かない。**

Claude Code をこのリポジトリのフォルダで起動し（初回は「このフォルダの hook を信頼するか」の確認が出るので承諾する）、次を貼る：

```
このリポジトリ（hicard-inc/claude-plugins）で commit / push できるように準備して。
1. git config core.hooksPath が hooks になっているか見て、違えば git config core.hooksPath hooks を実行
2. 禁止語一覧を設定する。値はこれ（Owner から受け取った値をここに貼る。正規表現・| 区切り）:
   git config hicard.blocklist '<ここに一覧>'
   設定後、値そのものは会話に出さず、git config --get hicard.blocklist | wc -c で文字数だけ報告
3. bash hooks/claude_guard.sh --self-test を実行して「✓」と「pre-push hook 有効」が出ることを確かめる
4. 「わざと失敗させる」確認: git config hicard.blocklist を一時的に 'セットアップ状態' に変えて
   bash hooks/claude_guard.sh --self-test が exit 2 で止まることを見てから、2 の値に戻す
以後この repo では --no-verify と force push は使わない。検査で止まったら迂回せず理由を私に見せる。
```

期待する結果: 3 で `✓ claude_guard: 版・鍵・禁止語 すべて通過（pre-push hook 有効）`、4 で
`✗ 置いてはいけない語が N 箇所` と `path:line` が出て止まる。**止まるのを一度見ていない guard は動いている保証が無い**（RULES.md 5 章）。

### 分かっていること・限界

- **Claude Code を別のフォルダで起動して `git -C <このrepo> push` と打った場合、この hook は走らない**（project hook は起動したフォルダの設定）。その場合は 2 層目（`pre-push`）と 3 層目が残る
- `hicard.blocklist` が**未設定のまま commit / push すると止まる**（警告ではなく停止。守っていない状態で通さない）。一覧を持っていない人は Owner に聞く
- 一覧は `.git/config` にあるので、**clone をやり直したら消える**。もう一度 2 を実行する
- GitHub の **push ruleset（ファイルパスで push 自体を拒否）は public の Free では作れない**（2026-09-05 実測: API が 422 "Source public repos cannot have push rules"）。だから手元の層で止める
- メンバーの `marketplace add` で落ちる clone にもこの `.claude/settings.json` は入るが、**メンバーはそのフォルダで Claude を起動しないので影響しない**

## 9. メンバーが Skill を出す（fork → PR・2026-11-12 追加）

**メンバーは write を持たない（7章）。**自分の GitHub 上に写し（fork）を作り、そこから本体へ PR を出す。
**取り込むかは Owner が PR を見て決め、マージすると全メンバーに自動で届く**（`hicard` 本体に入る＝全員に配る。任意導入にはしない・2026-11-12 管理者決定）。

### メンバーがやること

GitHub アカウントと `gh`（`gh auth login` 済み）が要る。**持っていない人はこの経路を使えない**ので、Owner に Skill のフォルダを渡して代わりに出してもらう。

```
/hicard:skill-submit <Skill のフォルダのパス>
```

Skill が fork の用意 → 0〜5章と4関門の点検 → 版上げと検査 → **本人の確認** → push → PR まで進める。手で打つ場合の手順も同じで、作業場所は `~/work/claude-plugins-fork`（origin＝自分の fork、upstream＝本体）。

| 手元の検査 | fork の clone での動き |
|---|---|
| `pre-push`（版・`main` 直 push・鍵） | Owner と同じ。`git config core.hooksPath hooks` を入れる |
| `claude_guard.sh`（Claude Code をこのフォルダで起動したとき） | 版・鍵は同じ。**禁止語一覧は持たないので見ない**（origin が本体でなければ fork とみなす）。禁止語は PR の必須チェック `blocklist` が見る |

🔴 **fork は public。push した時点で誰でも読める。**禁止語の機械検査は push の後（PR）にしか走らないので、**0章の点検は push の前に本人と Claude が目でやる。**`/hicard:skill-submit` は push の前に必ず確認を取る。

### Owner がやること（メンバーの PR を受けたとき）

1. **初めての投稿者は Actions の実行承認が要る**（PR 画面の「Approve and run」）。押すまで `checks` は待ちのまま
2. `checks` と `blocklist` が両方緑であることを見る
3. **機械が見ないものを目で見る**: 0章（報酬・評価など文脈で決まる情報）／3章の関門1と関門4（PR 本文に実行出力があるか）／
   **振る舞いの危険**（全員の Claude が各自の権限で実行する。外部への送信・削除・広い Bash・Notion などへの書き込みを確認なしで行う手順が無いか）
4. 版が他の PR とぶつかったら（同時に複数の PR が同じ版を名乗る）、後にマージする方で版を上げ直してもらう
5. マージしたら、その場で `claude plugin marketplace update hicard-plugins` → `claude plugin update hicard@hicard-plugins`（6章）

**まずいものが入ったとき**: revert の PR を出して版を上げる。次に各自が Claude Code に最初の指示を出してから 0〜10 分で上書きされる（README「更新」）。
