"""yomiyasu で書き直した Markdown（extract_prose.py の出力形式）を教材JSONに書き戻す。

目印 `<!-- prose: {ID} -->` で段落を対応づける。目印が欠けている・増えているときはエラーにして書き戻さない。
地の文の段落が空行で複数に分かれていたら、<p> を複数に分けて書き戻す。
解説文が複数段落になっていたら1段落に連結し、警告を出す。

使い方:
  python apply_prose.py content.json prose_revised.md -o content_revised.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

from extract_prose import (
    PARAGRAPH_PATTERN,
    body_paragraph_id,
    explanation_id,
    extract_blocks,
    iter_questions,
    markdown_to_inline_html,
    parse_blocks,
)


def split_paragraphs(text):
    return [re.sub(r"\s*\n\s*", " ", part).strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def apply_revisions(content, revised_by_id):
    warnings = []
    for chapter in content["chapters"]:
        for section in chapter["sections"]:
            counter = {"index": 0}

            def replace_paragraph(match, section_id=section["id"], counter=counter):
                counter["index"] += 1
                prose_id = body_paragraph_id(section_id, counter["index"])
                if prose_id not in revised_by_id:
                    return match.group(0)  # 抜き出し対象外だった段落はそのまま
                paragraphs = split_paragraphs(revised_by_id[prose_id])
                return "".join(f"<p>{markdown_to_inline_html(p)}</p>" for p in paragraphs)

            section["body"] = PARAGRAPH_PATTERN.sub(replace_paragraph, section["body"])

    for question in iter_questions(content):
        prose_id = explanation_id(question["id"])
        if prose_id not in revised_by_id:
            continue
        paragraphs = split_paragraphs(revised_by_id[prose_id])
        if len(paragraphs) > 1:
            warnings.append(f"{prose_id}: 解説が{len(paragraphs)}段落に分かれていたため1段落に連結しました")
        question["explanation"] = markdown_to_inline_html("".join(paragraphs))
    return warnings


def main():
    parser = argparse.ArgumentParser(description="書き直した地の文・解説文を教材JSONに書き戻す")
    parser.add_argument("content", type=Path, help="書き戻し先の教材JSON（抜き出しに使ったもの）")
    parser.add_argument("revised", type=Path, help="書き直した Markdown")
    parser.add_argument("-o", "--output", type=Path, required=True, help="書き戻した教材JSONの出力先")
    args = parser.parse_args()

    content = json.loads(args.content.read_text(encoding="utf-8"))
    revised_by_id = parse_blocks(args.revised.read_text(encoding="utf-8"))

    expected_ids = {prose_id for prose_id, _ in extract_blocks(content)[0]}
    missing = sorted(expected_ids - revised_by_id.keys())
    unexpected = sorted(revised_by_id.keys() - expected_ids)
    if missing or unexpected:
        if missing:
            print(f"[ERROR] 目印が見つからない段落: {', '.join(missing)}")
        if unexpected:
            print(f"[ERROR] 元の教材にない目印: {', '.join(unexpected)}")
        print("書き戻しを中止しました。目印 <!-- prose: ID --> を元のまま残して書き直してください。")
        return 1
    empty = sorted(prose_id for prose_id, text in revised_by_id.items() if not text)
    if empty:
        print(f"[ERROR] 本文が空の段落: {', '.join(empty)}")
        return 1

    for warning in apply_revisions(content, revised_by_id):
        print(f"[WARN]  {warning}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"書き戻した教材JSONを出力しました: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
