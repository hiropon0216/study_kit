"""直す前と直した後の教材JSONを比べ、変わった項目・問題・要点・事実だけを Markdown に書き出す。

再レビューの担当には、教材JSONを2つ丸ごと読ませず、この差分だけを渡す。
変わった単位ごとに、直す前と直した後の全文を並べる（その単位の中で読み比べられるように）。

比べる単位:
  - 項目（見出し・本文）          節ID#項目ID
  - 問題（すぐ確認・章末演習・総合演習。言い換え問題を含む）  問題ID
  - 節の要点（keyPoints）・出典（sources）・前提（prerequisites）
  - まぎらわしい項目の組（confusables）
  - ファクトシートの事実

使い方:
  python diff_content.py work/content_before_validity_r1.json content.json -o work/reviews/validity-ch1-r2-diff.md
  python diff_content.py before.json after.json --scope ch1 -o diff.md    # 第1章（と、その章の事実）だけ
"""

import argparse
import json
import sys
from pathlib import Path


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=1)


def units(content, scope=None):
    """比べる単位を {キー: (種類, 値)} で返す。scope を渡すと、その章（ch1 など）か final だけにする。"""
    found = {}
    for chapter in content.get("chapters", []):
        if scope and scope != chapter["id"]:
            continue
        for section in chapter["sections"]:
            sid = section["id"]
            for key in ("keyPoints", "sources", "prerequisites"):
                found[f"{sid} {key}"] = ("節", section.get(key))
            for item in section["items"]:
                found[f"{sid}#{item['id']}"] = ("項目", {"title": item.get("title"), "type": item.get("type", "text"), "body": item.get("body")})
                for question in item.get("checks", []):
                    found[question["id"]] = ("すぐ確認", question)
        for question in chapter.get("exercise", []):
            found[question["id"]] = ("章末演習", question)
    if not scope or scope == "final":
        for question in content.get("finalExam", []):
            found[question["id"]] = ("総合演習", question)
    if not scope:
        for index, pair in enumerate(content.get("confusables", [])):
            found["confusables " + " / ".join(pair["items"])] = ("見分け", pair)
    for fact in content.get("factsheet", []):
        found[fact["id"]] = ("事実", fact)
    return found


def render(before, after):
    lines = []
    changed = added = removed = 0
    keys = list(before.keys()) + [key for key in after.keys() if key not in before]
    for key in keys:
        old = before.get(key)
        new = after.get(key)
        if old and new and old[1] == new[1]:
            continue
        kind = (new or old)[0]
        if old and new:
            changed += 1
            lines += [f"## {key}（{kind}・変更）", "", "直す前：", "```json", dump(old[1]), "```", "", "直した後：", "```json", dump(new[1]), "```", ""]
        elif new:
            added += 1
            lines += [f"## {key}（{kind}・追加）", "", "```json", dump(new[1]), "```", ""]
        else:
            removed += 1
            lines += [f"## {key}（{kind}・削除）", "", "```json", dump(old[1]), "```", ""]
    header = [f"# 教材の差分：変更 {changed}件・追加 {added}件・削除 {removed}件", ""]
    return "\n".join(header + lines) + "\n", changed + added + removed


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="直す前と直した後の教材JSONの差分を、変わった単位だけ書き出す")
    parser.add_argument("before", type=Path, help="直す前の教材JSON")
    parser.add_argument("after", type=Path, help="直した後の教材JSON")
    parser.add_argument("--scope", help="ch1 などの章ID、final（省略するとすべて）")
    parser.add_argument("-o", "--output", type=Path, required=True, help="差分の出力先（Markdown）")
    args = parser.parse_args()

    before = units(load_json(args.before), args.scope)
    after = units(load_json(args.after), args.scope)
    text, count = render(before, after)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"{count}件の違いを書き出しました: {args.output}（{args.output.stat().st_size // 1024}KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
