# claude-usage の参照資料（列の定義・症状別の対処）

SKILL.md から必要なときだけ読む。

## 列の定義（`claude_usage.py` が出す値）

| 列 | 定義 |
|---|---|
| 週開始日 | 月曜。週は月曜 00:00〜日曜 24:00（JST）。省略時は直近の完了週 |
| プラン | 本人に聞いた値（Pro / Max 5x / Max 20x / Team）。判定は Pro / Max を軸にし、Team の行は使わない |
| 週次上限の使用率 | その週に記録された `seven_day.used_percentage` の最大値（%）。statusline は Claude Code 起動中しか動かないので**下限値** |
| 5時間枠の上限到達回数 | `five_hour.resets_at` ごとの最大値が 100% 以上だった枠の数 |
| 5時間枠80%以上の回数 | 同じく 80% 以上だった枠の数 |
| 観測日数 | 使用率の記録がある日数（JST）。**3日未満の週は判定から外す** |
| 稼働日数・セッション数 | `~/.claude/projects/**/*.jsonl` で応答があった日数・セッション数 |
| 出力トークン | 出力トークンの合計 |
| 入力トークン | 入力 + キャッシュ書き込み（5分・1時間）+ キャッシュ読み込み |
| 主なモデル | 出力トークンが最多の系列（Opus / Sonnet / Haiku / Fable） |
| API換算額 | API 標準単価で計算した参考額（USD）。単価表は `claude_usage.py` の冒頭 |
| Pro換算 | Notion 側の数式。プラン倍率（Pro=1・Max 5x=5・Max 20x=20・それ以外=0）× 週次上限の使用率 ÷ 100。Notion のツールでは値が読めないので画面で見る |

- 会話ログは同じ応答が複数行に入るので `(message.id, requestId)` で重複を除く。`<synthetic>` は除外
- 会話ログの保持は既定30日。それより前の週はトークン系が過少になる（`notes` に出る）
- `rate_limits` は claude.ai の Pro / Max 契約で、各セッションの最初の応答の後にだけ statusline に届く

## 記録の差し込み（`install_statusline.py`）が変えるもの

| 変えるもの | 中身 |
|---|---|
| `~/.claude/settings.json` の `statusLine` | 元が無い: `python3 ~/.claude/usage-log/statusline_logger.py`（記録だけ・表示なし）／元がある: `... --then '<元のコマンド>'`（記録してから元の表示を出す） |
| `~/.claude/usage-log/statusline_logger.py` | 配布版のコピー。配布元の更新では変わらない（install をもう一度実行すると置き換わる） |
| `~/.claude/usage-log/statusline_original.json` | 差し込む前の `statusLine`（uninstall で戻す元） |
| `~/.claude/usage-log/settings.json.bak-<日時>` | 書き換える直前の settings.json 全体 |
| `~/.claude/usage-log/rate_limits.jsonl` | 記録本体。1行 = 時刻・5時間枠と週次の使用率・リセット時刻。前回と同じ値で同じ日なら書かない |

## 症状別の対処

| 症状 | 原因と対処 |
|---|---|
| 使用率の列が空（`notes` に「記録が無い週」） | 記録を差し込んでいない、または差し込む前の週。`状態` で確かめ、なしなら `記録を始める` |
| `状態` で「記録ファイル: まだ無い」が続く | 差し込み後に Claude が一度も応答していない、または Pro / Max 以外の契約（API キー利用など）。数回やり取りしてから再確認 |
| statusline の表示が消えた・変わった | `記録を止める` で元に戻す。戻らなければ `~/.claude/usage-log/settings.json.bak-*` の最新を管理者と確認 |
| `NG  statusLine が command 形式ではない` | 自動では差し込めない形。管理者に相談 |
| Notion で書き込み権限が無い | DB の編集権限が無い。管理者に頼む |
| 既存行が2件以上 | 同じ週の行が重複している。書かずに止まるので、管理者に重複の整理を頼む |
