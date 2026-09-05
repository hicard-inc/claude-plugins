# このリポジトリに足す・直すときの基準

**足す前にここを読む。**読まずに足すと、以前の状態に戻る
（＝手順・判断・実データ・個人の状態が同じファイルに混ざり、**共有すべきものが埋もれる**）。

---

## 0. まず：ここに入れてはいけないもの

plugin のインストールは **`git clone`**。**この中身はインストールした全員のマシンに落ちる。**
private だからといって以下は入れない。**一度コミットすると履歴から消せない。**

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
claude plugin details hicard    # 常時コストと、スキルごとの呼び出し時コストが出る
```

現状の実測（**0.1.6**・2026-09-05）。**常時 ~314 トークン**、呼び出し時は
**setup ~5.3k** / slides ~4.3k / research ~2.9k / tasks ~2.2k ＝合計 ~14.7k。
全体の上限 25,000 は超えていない。

🔴 **setup が 1 Skill の上限 5,000 を超えていた**（表の2行目）。
0.1.1 の時点では 4.4k で、そこから追記を重ねるうちに越えた。**測るまで誰も気づいていない。**
[#6](https://github.com/hicard-inc/claude-plugins/pull/6) で参照資料（`google_drive.md`）を
切り出して戻した。**この数字は 0.1.6 のものなので、#6 のマージ後に測り直すこと。**

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
| 更新手順「`/plugin marketplace update` を実行」 | **`/plugin` は引数を取らない。**一覧が開くだけで、**Enter を押すと選択中の plugin がその場で入る**（zono のマシンに `superpowers` が意図せず入った） | [#4](https://github.com/hicard-inc/claude-plugins/pull/4) [#5](https://github.com/hicard-inc/claude-plugins/pull/5) |
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
claude plugin marketplace update hicard-plugins # 取り直す
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

## 7. このリポジトリへの書き込み権限（2026-09-04 追加）

**plugin のインストールは `git clone` で、更新は再 clone。**
つまり **ここに push できる人は、全メンバーの Claude に任意の Skill と MCP 設定を配れる。**
リポジトリの write 権限は、そのまま**全員の Claude を動かす権限**になる。

| | 決めごと |
|---|---|
| **write（push）** | **Org Owner のみ。**現在4名（実測 2026-09-04・全員2FA済み） |
| **配布先のメンバー** | **Outside collaborator の `pull`（read）だけ渡す。**push は付けない |
| **Org Member にしない** | Member は Org の**全リポジトリが見える**。クライアントワークが含まれるため |
| **clone したら1回** | `git config core.hooksPath hooks`。**忘れるとこのリポジトリのガードは全部無効になる**（GitHub Free ではサーバー側の branch protection が使えないので、hook が唯一の担保） |

read 権限を渡すコマンド（zono が実行する）：

```bash
# 現在の権限を見る
gh api repos/hicard-inc/claude-plugins/collaborators --jq '.[] | "\(.login)\t\(.role_name)"'

# read だけ渡す（招待が飛ぶ。本人が承諾するまで有効にならない）
gh api -X PUT repos/hicard-inc/claude-plugins/collaborators/<username> -f permission=pull

# 承諾待ちの招待を見る
gh api repos/hicard-inc/claude-plugins/invitations --jq '.[] | "\(.invitee.login)\t\(.permissions)"'
```

> **`permission=pull` を省くと既定は `push` になる。**必ず明示する。
