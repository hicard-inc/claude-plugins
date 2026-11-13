#!/usr/bin/env python3
"""fork から Skill を足す・変える PR の本文に、配布前レビューの結果があるかを確かめる。

blocklist.yml（pull_request_target・必須チェック「blocklist」）から main 側のこのスクリプトだけを動かす。
PR 側は読むだけ: 本文はイベントの JSON から、ファイルは pr/ に checkout したものを読む（実行しない）。

- 本文の形の正本: plugins/hicard/skills/skill-submit/pr_body.md（main 側を読む）
- 観点の名前の正本: plugins/hicard/skills/skill-review/checklist.md の「7つの観点」の表（main 側を読む）
- 対象: fork から来て plugins/hicard/skills/ を変える PR だけ。Owner の PR（本体のブランチから）と、
  Skill を変えない PR は対象外
- 機械の点検（scan.py）を PR の Skill に当て、結果をジョブの Summary に出す（確認者が読む材料。合否には使わない）

🔴 本文・ファイルの中身はログと Summary に書き写さない（足りない見出しの名前など、こちらの正本の文字だけを出す）。

終了コード: 0=対象外か合格 / 1=本文が足りない / 2=イベントや API が読めない（通さない）
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
TEMPLATE = os.path.join(BASE, "plugins", "hicard", "skills", "skill-submit", "pr_body.md")
CHECKLIST = os.path.join(BASE, "plugins", "hicard", "skills", "skill-review", "checklist.md")
SCAN = os.path.join(BASE, "plugins", "hicard", "skills", "skill-review", "scan.py")
SKILLS_PREFIX = "plugins/hicard/skills/"
REVIEW = "配布前レビュー"
CATEGORIES = ("落とす", "直して通す", "前提を書いて通す", "問題なし")
GUIDE = ("手元で `/hicard:skill-review <Skill のパス>` を回し、結果を PR 本文の「## 配布前レビュー」の表に書いてください。"
         "本文の形は plugins/hicard/skills/skill-submit/pr_body.md です（`/hicard:skill-submit` で出すと、この形で本文が入ります）。"
         "本文を直して保存すると、このチェックは自動でやり直されます。")


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def sections(md):
    """「## 見出し」→ 本文（コメントを除く）。コードブロックの中の ## は見出しとみなさない。"""
    out, cur, fence = {}, None, False
    for line in strip_comments(md).replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
            continue
        if cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def cells(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    parts = [c.strip().strip("*").strip() for c in s.strip("|").split("|")]
    if all(re.fullmatch(r":?-{2,}:?", c) for c in parts if c) and any(parts):
        return None  # 区切り行
    return parts


def blank_rows(section_text):
    """テンプレートの表で、空欄を持つ行 → (見出しのセル, 列数)。見出しのセルは最後の空でないセル。"""
    rows = []
    for line in section_text.split("\n"):
        c = cells(line)
        if c and "" in c:
            filled = [x for x in c if x]
            if filled:
                rows.append((filled[-1], len(c)))
    return rows


def viewpoints(checklist_md):
    return re.findall(r"^\|\s*\d\s*\|\s*\*\*(.+?)\*\*\s*\|", checklist_md, flags=re.M)


def check_body(body, template_md, checklist_md):
    """足りないところの一覧を返す（空なら合格）。返す文字はこちらの正本のものだけ。"""
    tpl = sections(template_md)
    got = sections(body or "")
    names = viewpoints(checklist_md)
    problems = []
    if len(names) != 7:
        problems.append(f"checklist.md から観点を7つ読めなかった（{len(names)} 個）。管理者が直す")
    for head, tbody in tpl.items():
        if head not in got:
            problems.append(f"見出し「## {head}」が無い")
            continue
        text = got[head]
        if not tbody and not text:
            problems.append(f"「## {head}」が空")
        body_rows = [c for c in (cells(l) for l in text.split("\n")) if c]
        for label, ncol in blank_rows(tbody):
            hit = [c for c in body_rows if label in c]
            if not hit:
                problems.append(f"「## {head}」の表に「{label}」の行が無い")
            elif not any(sum(1 for x in c if x) >= ncol for c in hit):
                problems.append(f"「## {head}」の「{label}」の行に空欄がある")
    review = got.get(REVIEW)
    if review is not None:
        rows = [c for c in (cells(l) for l in review.split("\n")) if c]
        for name in names:
            hit = [c for c in rows if name in c]
            if not hit or any(name in p for p in problems):
                continue  # 行が無い・空欄があることは上で出している
            cats = [x for c in hit for x in c if x in CATEGORIES]
            if not cats:
                problems.append(f"観点「{name}」の区分が {'／'.join(CATEGORIES)} のどれでもない")
            elif "落とす" in cats:
                problems.append(f"観点「{name}」が「落とす」のまま（直さない限り配れない）")
    return problems


def pr_files(repo, number, token):
    files = []
    for page in range(1, 31):  # API の上限は 3,000 件
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/pulls/{number}/files?per_page=100&page={page}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                     "User-Agent": "hicard-plugins-check"})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        for f in batch:
            files.append(f["filename"])
            if f.get("previous_filename"):
                files.append(f["previous_filename"])
        if len(batch) < 100:
            break
    return files


def changed_skills(files):
    out = set()
    for f in files:
        if f.startswith(SKILLS_PREFIX):
            rest = f[len(SKILLS_PREFIX):]
            if "/" in rest:
                out.add(rest.split("/")[0])
    return sorted(out)


def scan(pr_dir, name):
    path = os.path.join(pr_dir, *SKILLS_PREFIX.strip("/").split("/"), name)
    if not os.path.isdir(path):
        return f"`{name}`: PR の中にフォルダが無い（削除か改名）"
    with tempfile.TemporaryDirectory() as tmp:  # 手元の .claude を拾わないよう、空のフォルダで動かす
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "LANG": "C.UTF-8"}  # トークン・禁止語を渡さない
        r = subprocess.run([sys.executable, "-I", SCAN, path], cwd=tmp, env=env,
                           capture_output=True, text=True, timeout=120)
    return f"### `{name}`（scan.py の終了コード {r.returncode}）\n\n{r.stdout.strip()}\n{r.stderr.strip()}".strip()


def summary(text):
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def main():
    try:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
            ev = json.load(f)
    except (KeyError, OSError, ValueError) as e:
        print(f"✗ イベントを読めない: {type(e).__name__}")
        return 2
    pr = ev.get("pull_request")
    if not pr:
        print("PR ではないので対象外")
        return 0
    base_repo = ev["repository"]["full_name"]
    head_repo = ((pr.get("head") or {}).get("repo") or {}).get("full_name")
    if head_repo == base_repo:
        print("本体のブランチからの PR（Owner）なので対象外")
        return 0
    try:
        files = pr_files(base_repo, pr["number"], os.environ.get("GITHUB_TOKEN", ""))
    except Exception as e:  # 読めないときは通さない
        print(f"✗ PR の変更ファイルを取れない: {type(e).__name__}")
        return 2
    skills = changed_skills(files)
    if not skills:
        print("Skill（plugins/hicard/skills/）を変えていないので対象外")
        return 0

    with open(TEMPLATE, encoding="utf-8") as f:
        template_md = f.read()
    with open(CHECKLIST, encoding="utf-8") as f:
        checklist_md = f.read()
    problems = check_body(pr.get("body") or "", template_md, checklist_md)

    pr_dir = os.environ.get("PR_DIR", "")
    scans = [scan(pr_dir, n) for n in skills] if pr_dir else ["（PR の中身が無いので scan.py は回していない）"]

    lines = ["## 配布前レビュー（PR 本文）", ""]
    lines.append("対象の Skill: " + "、".join(f"`{n}`" for n in skills))
    lines.append("")
    if problems:
        lines += ["**✗ PR 本文に配布前レビューの結果が足りません。**", "", GUIDE, "", "足りないところ:", ""]
        lines += [f"- {p}" for p in problems]
    else:
        lines.append("✓ PR 本文に必要な見出しと、7観点の区分がそろっています（中身の正しさは確認者が読んで決める）")
    lines += ["", "## 機械の点検（scan.py・確認者が読む材料。合否には使わない）", "",
              "既存の Skill を変える PR では「配布中の Skill と同名」が出るが、それは想定どおり。", ""]
    lines += scans
    summary("\n".join(lines))

    if problems:
        print("::error title=配布前レビューが PR 本文にありません::" + GUIDE + " 足りないところ: " + " / ".join(problems))
        for p in problems:
            print(f"✗ {p}")
        return 1
    print("✓ 配布前レビューの結果が PR 本文にある（" + "、".join(skills) + "）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
