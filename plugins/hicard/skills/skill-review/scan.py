#!/usr/bin/env python3
"""配布前レビューの機械点検（読むだけ。ファイルは変えない）。

使い方:
  python3 -I scan.py <Skill のフォルダ または コマンドの .md>

出力: 観点・区分・場所・内容の表。最後に件数。
終了コード: 0=落とす候補なし / 1=落とす候補あり / 2=使い方の誤り
区分の意味:
  落とす候補 … 直さない限り配れない可能性が高い（最終判断は読んでから）
  要確認     … 読んで判断する。問題なしのことも多い
観点の番号は checklist.md の 1〜7。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(HERE))  # skills/skill-review/ の2つ上
HOME = os.path.expanduser("~")
MAX_CHARS = 6700  # これを超えると 5,000 トークンを超える（CONTRIBUTING 2章）
MAX_LINES = 500

findings = []  # (観点, 区分, 場所, 内容)
seen = set()


def add(view, level, where, text, key=None):
    k = key or (view, level, where, text)
    if k in seen:
        return
    seen.add(k)
    text = text.replace("|", "\\|").replace("\n", " ")
    if len(text) > 80:
        text = text[:77] + "…"
    findings.append((view, level, where, text))


def mask(s):
    return s[:4] + "…（伏せ字）"


# ---- このマシンの利用者を表す文字列（属人性の手がかり） ----
def identity_words():
    words = set()
    for v in (os.environ.get("USER"), os.path.basename(HOME)):
        if v and len(v) >= 3:
            words.add(v)
    for key in ("user.name", "user.email"):
        try:
            out = subprocess.run(["git", "config", "--global", key], capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            out = ""
        if key == "user.email" and "@" in out:
            out = out.split("@")[0]
        if out and len(out) >= 3:
            words.add(out)
    return words


# ---- このマシンにだけある Skill・コマンド・エージェントの名前 ----
def local_names(exclude):
    names = set()
    bases = [os.path.join(HOME, ".claude"), os.path.join(os.getcwd(), ".claude")]
    for b in bases:
        sk = os.path.join(b, "skills")
        if os.path.isdir(sk):
            names.update(d for d in os.listdir(sk) if os.path.isdir(os.path.join(sk, d)))
        for sub in ("commands", "agents"):
            d = os.path.join(b, sub)
            for root, _, files in os.walk(d) if os.path.isdir(d) else []:
                names.update(f[:-3] for f in files if f.endswith(".md"))
    names -= exclude
    # 短い一般語は誤検出が多いので外す（ハイフンなしで6文字未満）
    return {n for n in names if "-" in n or len(n) >= 6}


SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|ntn_[A-Za-z0-9]{20,}|secret_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AIza[0-9A-Za-z_-]{30,})")
ABS_HOME = re.compile(r"(/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|C:\\\\Users\\\\[A-Za-z0-9._-]+)")
TILDE = re.compile(r"(?:~|\$HOME|\$\{HOME\})/([^\s`\"')\]]*)")
# 書いた人が自分で作るもの（配布先には無い）
LOCAL_OWN = re.compile(r"^\.claude/(scripts|hooks|agents|handoffs|plans|memory)(/|$)|^\.claude/(skills|commands)/[^<*\s]")
# 誰の手元にもあるが、中身が人によって違うもの
LOCAL_COMMON = re.compile(r"^\.claude/(CLAUDE\.md|rules|projects|settings[^/]*\.json|keybindings\.json)")
PARENT = re.compile(r"(?:^|[\s`\"'(])\.\./")
IDS = [
    (re.compile(r"docs\.google\.com/(spreadsheets|document|presentation|forms)/d/[A-Za-z0-9_-]+"), "Google のファイル ID"),
    (re.compile(r"drive\.google\.com/[^\s)`]+"), "Google ドライブの URL"),
    (re.compile(r"notion\.so/[^\s)`]+"), "Notion の URL"),
    (re.compile(r"\b[0-9a-f]{32}\b|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"), "ID らしき英数字"),
    (re.compile(r"\b[CDG]0[A-Z0-9]{8,}\b"), "Slack のチャンネル ID らしき文字列"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "メールアドレス"),
]
SERVICES = re.compile(r"(freee|Google ?Sheets|スプレッドシート|Gmail|Google ?(ドライブ|Drive|Calendar|カレンダー)|Slack|Asana|Figma|Redash|BigQuery|Treasure ?Data|HubSpot|Salesforce|Dropbox|1Password|Box\b|Linear|Jira|Confluence|Canva)", re.I)
CLI = re.compile(r"(?:^|[\s;|&(`$])(gh|codex|gcloud|jq|node|npx|npm|pnpm|yarn|bun|deno|brew|docker|aws|uv|pip3?|ffmpeg|op|yt-dlp|ruby|java|terraform|kubectl)(?=\s|$)")
PIPE_SH = re.compile(r"(curl|wget)[^|\n]*\|\s*(ba|z)?sh\b|(ba|z)?sh\s+<\(\s*(curl|wget)")
DANGER = re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r|git\s+push\s+(-f\b|--force)|git\s+reset\s+--hard|--no-verify")
SIDE = re.compile(r"(git\s+push|gh\s+pr\s+create|gh\s+(issue|release)\s+create|curl\s+-X\s*(POST|PUT|PATCH|DELETE)|requests\.(post|put|patch|delete)|送信|投稿|書き込|上書き|削除|起票|create-pages|update-page|add_rows|update_cells)")
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
MCP = re.compile(r"mcp__[A-Za-z0-9_-]+")


def code_parts(lines, is_code_file):
    """各行のうち「コードとして書かれている部分」を返す（コマンド名の検出用）。"""
    out = []
    fence = False
    for ln in lines:
        if is_code_file:
            out.append(ln)
            continue
        if ln.lstrip().startswith("```"):
            fence = not fence
            out.append("")
            continue
        out.append(ln if fence else " ".join(re.findall(r"`([^`]+)`", ln)))
    return out


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    for ln in m.group(1).splitlines():
        if ":" in ln and not ln.startswith((" ", "\t")):
            k, v = ln.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, text[m.end():]


def scan_file(path, rel, ids, lnames, is_entry, distributed, inside_plugin):
    if os.path.islink(path):
        add(3, "落とす候補", rel, "シンボリックリンク（配布先では別の場所を指すか、リンク切れになる）")
        return
    size = os.path.getsize(path)
    if size > 1_000_000:
        add(7, "要確認", rel, f"1MB 超のファイル（{size:,} バイト）。配布に要るか")
    try:
        text = open(path, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return  # 画像などのバイナリは読まない
    lines = text.splitlines()
    is_code = path.endswith((".py", ".sh", ".js", ".ts", ".rb", ".zsh", ".bash"))
    code = code_parts(lines, is_code)

    if is_entry:
        fm, body = frontmatter(text)
        if path.endswith("SKILL.md"):
            if len(text) > MAX_CHARS:
                add(7, "落とす候補", rel, f"{len(text):,} 字（上限 {MAX_CHARS:,} 字）。理由・実例は別ファイルへ出す")
            if len(lines) > MAX_LINES:
                add(7, "落とす候補", rel, f"{len(lines)} 行（上限 {MAX_LINES} 行）")
        if fm is None:
            add(7, "要確認", rel, "frontmatter が無い（name・description を足す）")
            fm = {}
        if "name" not in fm and path.endswith("SKILL.md"):
            add(7, "要確認", rel, "frontmatter に name が無い")
        if not fm.get("description"):
            add(7, "要確認", rel, "description が無い（他の人が、いつ使うものか分からない）")
        for k in ("model", "effort"):
            if k in fm:
                add(4, "要確認", rel, f"frontmatter の {k}: は書いた人の環境・プランに依存する（CONTRIBUTING 5章）")
        if "mcp__" in fm.get("allowed-tools", ""):
            add(5, "落とす候補", rel, "allowed-tools に MCP ツール名（環境で名前が変わり、黙って使えなくなる）")
        name = fm.get("name") or os.path.basename(os.path.dirname(path)) if path.endswith("SKILL.md") else os.path.basename(path)[:-3]
        if name in distributed and not inside_plugin:
            add(7, "落とす候補", rel, f"配布中の Skill と同じ名前: {name}")
        dmi = fm.get("disable-model-invocation", "").lower() == "true"
        if not dmi:
            m = SIDE.search(body)
            if m:
                add(6, "要確認", rel, f"副作用らしき記述（{m.group(0)}）があるのに disable-model-invocation: true が無い。書く前に確認を取る手順があるか")

    date_hits = 0
    for i, ln in enumerate(lines, 1):
        where = f"{rel}:{i}"
        for m in SECRET.finditer(ln):
            add(1, "落とす候補", where, "鍵・トークンらしき文字列 " + mask(m.group(0)))
        for m in ABS_HOME.finditer(ln):
            add(3, "落とす候補", where, f"個人のホームの絶対パス {m.group(0)}")
        for m in TILDE.finditer(ln):
            p = m.group(1)
            if p.startswith(".claude/plugins"):
                continue
            if LOCAL_OWN.match(p):
                add(4, "落とす候補", where, f"書いた人が手元で作ったものを読む・使う ~/{p}（配布先には無い）")
            elif LOCAL_COMMON.match(p):
                add(4, "要確認", where, f"Claude の設定 ~/{p}（誰にでもあるが中身は人ごとに違う。書いた人の中身を前提にしていないか）")
            else:
                add(3, "要確認", where, f"ホーム配下のパス ~/{p}（配布先に同じものがあるか）")
        if PARENT.search(ln):
            add(3, "要確認", where, "../ で Skill フォルダの外を指していないか")
        for rx, label in IDS:
            for m in rx.finditer(ln):
                s = m.group(0)
                if label == "メールアドレス" and s.endswith(("@anthropic.com", "@example.com")):
                    continue
                add(1, "要確認", where, f"{label} {s}")
        for w in ids:
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])", ln, re.I):
                add(2, "要確認", where, f"このマシンの利用者を表す語 {w}")
        if "CLAUDE.md" in ln:
            add(4, "要確認", where, "CLAUDE.md への言及（書いた人の CLAUDE.md のルールが前提になっていないか）")
        for m in MCP.finditer(ln):
            add(5, "要確認", where, f"MCP ツール名 {m.group(0)}（環境で名前が変わる。ToolSearch で探す形に）")
        for m in SERVICES.finditer(ln):
            k = (5, rel, m.group(0).lower())
            add(5, "要確認", where, f"外部サービス {m.group(0)}（全員がつないでいるか。無い人に止まって案内するか）", key=k)
        for m in CLI.finditer(code[i - 1]):
            k = (5, rel, "cli", m.group(1))
            add(5, "要確認", where, f"追加の道具 {m.group(1)}（全員の前提ではない。無い人に止まって案内するか）", key=k)
        if PIPE_SH.search(ln):
            add(6, "落とす候補", where, "ネットから取ってきたものをそのまま実行している")
        m = DANGER.search(ln)
        if m:
            add(6, "要確認", where, f"取り消せない操作 {m.group(0)}")
        for n in lnames:
            if re.search(r"(?<![A-Za-z0-9_-])" + re.escape(n) + r"(?![A-Za-z0-9_-])", ln):
                add(4, "要確認", where, f"このマシンにだけある Skill・コマンド・エージェントの名前 {n}")
        if DATE.search(ln):
            date_hits += 1
            if date_hits == 1:
                add(7, "要確認", where, "日付つきの記述（その時点の状態・事実が書かれていないか。以降の行は省略）")

    if is_code and path.endswith(".py") and hasattr(sys, "stdlib_module_names"):
        local_mods = {f[:-3] for f in os.listdir(os.path.dirname(path)) if f.endswith(".py")}
        for i, ln in enumerate(lines, 1):
            m = re.match(r"\s*(?:from\s+([A-Za-z0-9_]+)|import\s+([A-Za-z0-9_]+))", ln)
            if m:
                mod = m.group(1) or m.group(2)
                if mod not in sys.stdlib_module_names and mod not in local_mods and mod != "__future__":
                    add(5, "要確認", f"{rel}:{i}", f"標準ライブラリにないモジュール {mod}（全員の環境に入っていない）")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    target = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if not os.path.exists(target):
        print(f"✗ 見つからない: {target}")
        return 2
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    distributed = {d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))} if os.path.isdir(skills_dir) else set()
    inside_plugin = os.path.realpath(target).startswith(os.path.realpath(skills_dir) + os.sep)
    own = os.path.basename(target.rstrip("/"))
    own = own[:-3] if own.endswith(".md") else own
    lnames = local_names(distributed | {own})
    ids = identity_words()

    files = []
    if os.path.isdir(target):
        if not os.path.isfile(os.path.join(target, "SKILL.md")):
            print(f"✗ SKILL.md が無い: {target}")
            return 2
        for root, dirs, fs in os.walk(target, followlinks=False):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
            for d in list(dirs):
                if os.path.islink(os.path.join(root, d)):
                    files.append(os.path.join(root, d))
                    dirs.remove(d)
            files += [os.path.join(root, f) for f in fs if f != ".DS_Store"]
        base = target
    elif target.endswith(".md"):
        files = [target]
        base = os.path.dirname(target)
    else:
        print("✗ Skill のフォルダか、コマンドの .md を渡す")
        return 2

    for f in sorted(files):
        rel = os.path.relpath(f, base)
        is_entry = rel == "SKILL.md" or os.path.isfile(target)
        scan_file(f, rel, ids, lnames, is_entry, distributed, inside_plugin)

    print(f"対象: {own}（{len(files)} ファイル）")
    print()
    print("| 観点 | 区分 | 場所 | 内容 |")
    print("|---|---|---|---|")
    order = {"落とす候補": 0, "要確認": 1}
    for v, lv, w, t in sorted(findings, key=lambda x: (order[x[1]], x[0], x[2])):
        print(f"| {v} | {lv} | {w} | {t} |")
    ng = sum(1 for f in findings if f[1] == "落とす候補")
    print()
    print(f"落とす候補 {ng} 件 / 要確認 {len(findings) - ng} 件")
    print("（機械で拾えるのはパス・名前・ID などの形だけ。属人的な書きぶりや権限の前提は、読んで判断する）")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
