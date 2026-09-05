#!/usr/bin/env python3
"""hicard の運用ルールを ~/.claude/rules/hicard.md に置く（setup Skill の 1-2 から呼ばれる）。

配布元リポジトリ直下の RULES.md へ symlink を張る。
symlink 先は marketplace の clone（版番号を含まない安定したパス）なので、
`claude plugin marketplace update hicard-plugins` だけでルールも最新になる。

plugin の cache（.../cache/<marketplace>/<plugin>/<版>/）は版ごとに別のフォルダになるため、
そちらへ張ると更新のたびにリンクが切れる。だから marketplace 側を指す。
"""
import json
import pathlib
import sys

HOME = pathlib.Path.home()
MARKETPLACE = "hicard-plugins"


def find_rules() -> pathlib.Path | None:
    registry = HOME / ".claude/plugins/known_marketplaces.json"
    try:
        location = json.loads(registry.read_text(encoding="utf-8"))[MARKETPLACE]["installLocation"]
        candidate = pathlib.Path(location) / "RULES.md"
        if candidate.exists():
            return candidate
    except (OSError, ValueError, KeyError):
        pass
    # 登録簿が読めない・形が変わったときの保険
    hits = sorted((HOME / ".claude/plugins/marketplaces").glob("*/RULES.md"))
    return hits[0] if hits else None


def main() -> int:
    dst = HOME / ".claude/rules/hicard.md"
    src = find_rules()
    if src is None:
        # 前回の symlink が残っていると、リンク切れのまま毎回読み込まれる。先に片付ける
        if dst.is_symlink() and not dst.exists():
            dst.unlink()
            print("   （リンク切れになっていた古いルールを外した）")
        print("NG  RULES.md が見つからない。")
        print("    先にターミナルで  claude plugin marketplace update hicard-plugins  を実行してからやり直す。")
        return 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        dst.unlink()

    try:
        dst.symlink_to(src)
        print(f"OK  symlink  {dst} -> {src}")
    except OSError as e:
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"OK  コピー  {dst} （symlink が張れなかった: {e}）")
        print("    このやり方だと自動では更新されない。更新のたびに /setup を打ち直す。")

    print("    次回の起動から読み込まれる。確かめ方は2つ:")
    print(f"      1) ls -l {dst} && head -1 {dst}")
    print("         -> リンク先のパスと '# hicard で Claude を使うときのルール' が返れば合格")
    print("      2) 再起動後の自分の指示にルール本文が入っていること（1行引用して見せる）")
    print("    /context は Claude 自身では実行できない（スラッシュコマンド）。1) 2) で判定する。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
