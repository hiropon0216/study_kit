"""教科書の地の文と解説文だけを抜き出し、yomiyasu とリントに渡す Markdown を作る。

抜き出す対象:
  - 節の body の中の <p>（属性なし）の段落
  - 問題の explanation（各節の問題と総合演習）
抜き出さないもの:
  - 表・コード・リスト・用語定義（<p> 以外）、問題文、選択肢
  - <code> <strong> <a> 以外のタグを含む段落（書き戻しで壊さないため。件数を標準エラーに出す）

出力は段落ごとに `<!-- prose: {ID} -->` の目印を付けた Markdown。
インラインのタグは Markdown に置き換える（<code>→`x`、<strong>→**x**、<a href>→[x](url)）。
書き戻しは apply_prose.py で行う。

使い方:
  python extract_prose.py content.json -o prose.md
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

PARAGRAPH_PATTERN = re.compile(r"<p>(.*?)</p>", re.DOTALL)
CODE_PATTERN = re.compile(r"<code>(.*?)</code>", re.DOTALL)
STRONG_PATTERN = re.compile(r"<strong>(.*?)</strong>", re.DOTALL)
LINK_PATTERN = re.compile(r'<a href="([^"]*)">(.*?)</a>', re.DOTALL)
TAG_NAME_PATTERN = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)")
MARKER_PATTERN = re.compile(r"<!-- prose: (\S+) -->")
CONVERTIBLE_TAGS = {"code", "strong", "a"}

MD_CODE_PATTERN = re.compile(r"(`[^`]+`)")
MD_STRONG_PATTERN = re.compile(r"\*\*(.+?)\*\*")
MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def marker(prose_id):
    return f"<!-- prose: {prose_id} -->"


def body_paragraph_id(section_id, index):
    return f"{section_id}#p{index}"


def explanation_id(question_id):
    return f"{question_id}#explanation"


def can_convert(fragment):
    return set(TAG_NAME_PATTERN.findall(fragment)) <= CONVERTIBLE_TAGS


def inline_html_to_markdown(fragment):
    """<code>/<strong>/<a> だけを含む HTML 断片を Markdown の1行にする。"""
    pieces = CODE_PATTERN.split(fragment)
    converted = []
    for index, piece in enumerate(pieces):
        is_code = index % 2 == 1
        if is_code:
            converted.append("`" + html.unescape(piece) + "`")
            continue
        piece = STRONG_PATTERN.sub(r"**\1**", piece)
        piece = LINK_PATTERN.sub(lambda m: f"[{m.group(2)}]({html.unescape(m.group(1))})", piece)
        converted.append(html.unescape(piece))
    return re.sub(r"\s*\n\s*", " ", "".join(converted)).strip()


def markdown_to_inline_html(text):
    """inline_html_to_markdown の逆変換。"""
    converted = []
    for index, piece in enumerate(MD_CODE_PATTERN.split(text)):
        is_code = index % 2 == 1
        if is_code:
            converted.append("<code>" + html.escape(piece[1:-1], quote=False) + "</code>")
            continue
        piece = html.escape(piece, quote=False)
        piece = MD_STRONG_PATTERN.sub(r"<strong>\1</strong>", piece)
        piece = MD_LINK_PATTERN.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', piece)
        converted.append(piece)
    return "".join(converted)


def iter_questions(content):
    for chapter in content["chapters"]:
        for section in chapter["sections"]:
            yield from section["questions"]
    yield from content.get("finalExam", [])


def extract_blocks(content):
    """(prose_id, markdown) の一覧と、変換できずに飛ばした ID の一覧を返す。"""
    blocks = []
    skipped = []
    for chapter in content["chapters"]:
        for section in chapter["sections"]:
            for index, match in enumerate(PARAGRAPH_PATTERN.finditer(section["body"]), start=1):
                prose_id = body_paragraph_id(section["id"], index)
                if can_convert(match.group(1)):
                    blocks.append((prose_id, inline_html_to_markdown(match.group(1))))
                else:
                    skipped.append(prose_id)
    for question in iter_questions(content):
        prose_id = explanation_id(question["id"])
        if can_convert(question["explanation"]):
            blocks.append((prose_id, inline_html_to_markdown(question["explanation"])))
        else:
            skipped.append(prose_id)
    return blocks, skipped


def render_blocks(blocks):
    return "\n\n".join(f"{marker(prose_id)}\n{text}" for prose_id, text in blocks) + "\n"


def parse_blocks(markdown):
    """render_blocks の出力（を書き直したもの）を {prose_id: 本文} に戻す。"""
    parts = MARKER_PATTERN.split(markdown)
    # parts = [先頭の余り, id1, 本文1, id2, 本文2, ...]
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def main():
    parser = argparse.ArgumentParser(description="教科書の地の文と解説文を Markdown に抜き出す")
    parser.add_argument("content", type=Path, help="教材JSONのパス")
    parser.add_argument("-o", "--output", type=Path, required=True, help="出力する Markdown のパス")
    args = parser.parse_args()

    content = json.loads(args.content.read_text(encoding="utf-8"))
    blocks, skipped = extract_blocks(content)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_blocks(blocks), encoding="utf-8")
    print(f"{len(blocks)}件の段落を抜き出しました: {args.output}")
    if skipped:
        print(f"変換できないタグを含むため {len(skipped)}件を対象外にしました: {', '.join(skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
