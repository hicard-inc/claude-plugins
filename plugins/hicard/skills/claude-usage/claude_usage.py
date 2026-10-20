#!/usr/bin/env python3
"""Claude Code の週次使用量を1人×1週の1行に集計して JSON で出す（Notion [TMP] ClaudeUsage 用）。

入力:
  - ~/.claude/projects/**/*.jsonl            … トークン・モデル・セッション・稼働日（(message.id, requestId) で重複除去）
  - ~/.claude/usage-log/rate_limits.jsonl    … statusline_logger.py が記録した上限使用率（install_statusline.py で差し込んだ人だけ）
週は月曜 00:00 〜 日曜 24:00（JST）。--week-start 省略時は直近の完了週。
出力にはパス・プロンプト・セッションIDを含めない（集計値だけ）。

使い方:
  python3 claude_usage.py [--week-start 2026-10-12] [--plan "Max 20x"]
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os

VERSION = "0.1.1"
JST = dt.timezone(dt.timedelta(hours=9))
# Team は Notion の Pro換算の数式に倍率が無く 0 になる（Team は判定に使わない）
PLANS = {"Pro": 1, "Max 5x": 5, "Max 20x": 20, "Team": 0}

# API 標準単価（USD / 100万トークン）。2026-10-19 に claude-api Skill（2026-10-06 時点のキャッシュ）で確認。
# (入力, 出力, キャッシュ読み込み)。キャッシュ書き込みは 5分=入力×1.25・1時間=入力×2。
# haiku-5-5 / opus-5 / sonnet-5 / 4系のキャッシュ読み込みは「入力×0.1」の一般則から算出（個別の公表値は未確認）。
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-fable-5-1": (10.00, 50.00, 0.25),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-opus-5": (5.00, 25.00, 0.50),
    "claude-sonnet-5": (2.00, 10.00, 0.20),
    "claude-opus-4-8": (5.00, 25.00, 0.50),
    "claude-opus-4-7": (5.00, 25.00, 0.50),
    "claude-sonnet-4-6": (3.00, 15.00, 0.30),
    "claude-haiku-4-5": (1.00, 5.00, 0.10),
}
FAMILIES = [("fable", "Fable"), ("mythos", "Fable"), ("opus", "Opus"), ("sonnet", "Sonnet"), ("haiku", "Haiku")]


def price_for(model):
    for key in sorted(PRICES, key=len, reverse=True):
        if model == key or model.startswith(key + "-"):
            return PRICES[key]
    return None


def family(model):
    for needle, name in FAMILIES:
        if needle in model:
            return name
    return None


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def default_week_start(now):
    today = now.astimezone(JST).date()
    this_monday = today - dt.timedelta(days=today.weekday())
    return this_monday - dt.timedelta(days=7)


def aggregate_transcripts(root, start, end):
    seen = set()
    by_model = collections.defaultdict(lambda: collections.Counter())
    sessions, days = set(), set()
    oldest = None
    for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
        with open(path, errors="ignore") as f:
            for line in f:
                if '"usage"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = d.get("message")
                ts = d.get("timestamp")
                if not isinstance(m, dict) or not m.get("usage") or not ts:
                    continue
                model = m.get("model") or ""
                if model.startswith("<"):  # <synthetic> 等の擬似応答は除外
                    continue
                t = parse_ts(ts)
                oldest = t if oldest is None or t < oldest else oldest
                if not (start <= t < end):
                    continue
                key = (m.get("id"), d.get("requestId"))
                if key in seen:
                    continue
                seen.add(key)
                u = m["usage"]
                cc = u.get("cache_creation") or {}
                w5 = cc.get("ephemeral_5m_input_tokens")
                w1h = cc.get("ephemeral_1h_input_tokens")
                if w5 is None and w1h is None:  # 内訳が無い行は 5分扱い
                    w5, w1h = u.get("cache_creation_input_tokens", 0), 0
                c = by_model[(model, u.get("speed") == "fast")]
                c["input"] += u.get("input_tokens", 0) or 0
                c["output"] += u.get("output_tokens", 0) or 0
                c["cache_w5m"] += w5 or 0
                c["cache_w1h"] += w1h or 0
                c["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
                c["messages"] += 1
                if d.get("sessionId"):
                    sessions.add(d["sessionId"])
                days.add(t.astimezone(JST).date())
    return by_model, sessions, days, oldest


def aggregate_rate_limits(path, start, end):
    recs = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    t = parse_ts(r["ts"])
                except (ValueError, KeyError):
                    continue
                if start <= t < end:
                    recs.append((t, r))
    if not recs:
        return None
    sd_cycles = collections.defaultdict(float)
    fh_cycles = collections.defaultdict(float)
    for _, r in recs:
        if r.get("sd") is not None:
            sd_cycles[r.get("sd_reset")] = max(sd_cycles[r.get("sd_reset")], float(r["sd"]))
        if r.get("fh") is not None:
            fh_cycles[r.get("fh_reset")] = max(fh_cycles[r.get("fh_reset")], float(r["fh"]))
    return {
        "weekly_max": round(max(sd_cycles.values()), 1) if sd_cycles else None,
        "weekly_cycles": len(sd_cycles),
        "fh_hit": sum(1 for v in fh_cycles.values() if v >= 100),
        "fh_80": sum(1 for v in fh_cycles.values() if v >= 80),
        "obs_days": len({t.astimezone(JST).date() for t, _ in recs}),
        "records": len(recs),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week-start", help="週開始日（月曜・JST）YYYY-MM-DD。省略時は直近の完了週")
    ap.add_argument("--plan", choices=list(PLANS), help="現在のプラン")
    ap.add_argument("--projects", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--rate-log", default=os.path.expanduser("~/.claude/usage-log/rate_limits.jsonl"))
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    ws = dt.date.fromisoformat(args.week_start) if args.week_start else default_week_start(now)
    if ws.weekday() != 0:
        raise SystemExit(f"--week-start は月曜日を指定する（{ws} は月曜ではない）")
    start = dt.datetime.combine(ws, dt.time(), JST)
    end = start + dt.timedelta(days=7)

    by_model, sessions, days, oldest = aggregate_transcripts(args.projects, start, end)
    rl = aggregate_rate_limits(args.rate_log, start, end)

    tot = collections.Counter()
    cost, unknown = 0.0, set()
    out_by_family = collections.Counter()
    for (model, fast), c in by_model.items():
        tot.update(c)
        fam = family(model)
        if fam:
            out_by_family[fam] += c["output"]
        p = price_for(model)
        if p is None:
            unknown.add(model)
            continue
        pin, pout, pread = p
        mult = 2.0 if fast else 1.0
        cost += mult * (c["input"] * pin + c["cache_w5m"] * pin * 1.25 + c["cache_w1h"] * pin * 2.0
                        + c["cache_read"] * pread + c["output"] * pout) / 1e6

    notes = []
    if end > now:
        notes.append("集計対象の週が終わっていない（途中経過）")
    if oldest is None or oldest > start:
        notes.append("会話ログの保持期間より前の週を含む可能性（トークン系の値が過少）")
    if rl is None:
        notes.append("statusline の使用率記録が無い週（使用率・5時間枠の列は空欄）")
    elif rl["obs_days"] < 3:
        notes.append("観測日数が3日未満（判定から外す週）")
    if args.plan == "Team":
        notes.append("Team プランの行は判定に使わない（Pro換算は0になる）")
    if unknown:
        notes.append("単価未登録のモデルあり（API換算額に含めていない）: " + ", ".join(sorted(unknown)))

    info = f"集計 {now.astimezone(JST):%Y-%m-%d %H:%M} JST / claude_usage v{VERSION}"  # 「.py」を付けると Notion が usage.py をリンクに変える
    if rl:
        info += f" / 週次サイクル数 {rl['weekly_cycles']}・使用率記録 {rl['records']}件"
    if notes:
        info += " / " + " / ".join(notes)

    props = {
        "週開始日": ws.isoformat(),
        "プラン": args.plan,
        "週次上限の使用率": rl["weekly_max"] if rl else None,
        "5時間枠の上限到達回数": rl["fh_hit"] if rl else None,
        "5時間枠80%以上の回数": rl["fh_80"] if rl else None,
        "稼働日数": len(days),
        "セッション数": len(sessions),
        "出力トークン": tot["output"],
        "入力トークン": tot["input"] + tot["cache_w5m"] + tot["cache_w1h"] + tot["cache_read"],
        "主なモデル": out_by_family.most_common(1)[0][0] if out_by_family else None,
        "API換算額": round(cost, 2),
        "観測日数": rl["obs_days"] if rl else 0,
        "集計情報": info,
    }
    pro = None
    if args.plan and props["週次上限の使用率"] is not None:
        pro = round(PLANS[args.plan] * props["週次上限の使用率"] / 100, 2)
    breakdown = {
        f"{m}{' (fast)' if fast else ''}": dict(c) for (m, fast), c in sorted(by_model.items(), key=lambda x: -x[1]["output"])
    }
    print(json.dumps({
        "week": {"start": ws.isoformat(), "end": (ws + dt.timedelta(days=6)).isoformat()},
        "name_prefix": f"{ws.isoformat()}週",
        "properties": props,
        "expected_pro_equivalent": pro,
        "notes": notes,
        "model_breakdown": breakdown,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
