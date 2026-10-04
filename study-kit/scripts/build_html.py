"""教材JSONを template.html に埋め込み、1ファイルのHTMLとファクトシート（md）を出力する。

template.html はどのトピックでも共通。トピックごとに変わるのは教材JSONだけ。

使い方:
  # 教材JSONから作る
  python build_html.py content.json -o out/k8s-practical.html --factsheet out/k8s-practical_factsheet.md

  # 作成済みの教材HTMLを、最新の template.html で作り直す（教材JSONが手元になくてもよい）
  python build_html.py --from-html out/k8s-practical.html -o out/k8s-practical.html

validate.py の検査でエラーが出たときは出力しない。
"""

import argparse
import json
import re
import sys
from pathlib import Path

from validate import validate

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "template.html"
DATA_PLACEHOLDER = "__STUDY_DATA__"
EMBEDDED_DATA_PATTERN = re.compile(
    r'<script id="study-data" type="application/json">(.*?)</script>', re.DOTALL
)


def embed_content(template_html, content):
    if template_html.count(DATA_PLACEHOLDER) != 1:
        raise ValueError(f"テンプレートに {DATA_PLACEHOLDER} がちょうど1つ必要です")
    # <script> の中に置くため、"</" で script タグが閉じないようにエスケープする
    data_json = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
    return template_html.replace(DATA_PLACEHOLDER, data_json)


def extract_content(built_html):
    """作成済みの教材HTMLから、埋め込まれた教材JSONを取り出す（embed_content の逆）。"""
    match = EMBEDDED_DATA_PATTERN.search(built_html)
    if not match or match.group(1).strip() == DATA_PLACEHOLDER:
        raise ValueError("教材データが埋め込まれた study-kit の教材HTMLではありません")
    return json.loads(match.group(1).replace("<\\/", "</"))


def render_factsheet_markdown(content):
    """教材JSONの factsheet から、使用箇所つきのファクトシートを作る。"""
    usage_by_fact_id = {}
    for chapter in content["chapters"]:
        for section in chapter["sections"]:
            for fact_id in section.get("sources", []):
                usage_by_fact_id.setdefault(fact_id, []).append(f"{chapter['title']} ／ {section['title']}")

    meta = content["meta"]
    lines = [f"# ファクトシート：{meta['title']}", ""]
    lines.append(f"- 教材ID：`{meta['id']}`")
    if meta.get("targetVersion"):
        lines.append(f"- 対象バージョン：{meta['targetVersion']}")
    if meta.get("createdAt"):
        lines.append(f"- 作成日：{meta['createdAt']}")
    lines += ["", "| ID | 主張（1行） | 出典URL | 信頼度 | 使用箇所 |", "|---|---|---|---|---|"]
    for fact in content["factsheet"]:
        claim = fact["claim"].replace("|", "\\|")
        if fact.get("backedBy"):
            claim += f"（裏付け：{', '.join(fact['backedBy'])}）"
        usage = "<br>".join(usage_by_fact_id.get(fact["id"], ["（未使用）"]))
        lines.append(f"| {fact['id']} | {claim} | {fact['url']} | {fact['rank']} | {usage} |")

    fact_check_log = content.get("factCheckLog") or []
    if fact_check_log:
        lines += ["", "## 事実チェックの記録", "", "| 日付 | 対象 | 対応 | 根拠 |", "|---|---|---|---|"]
        for entry in fact_check_log:
            cells = [str(entry.get(key, "")).replace("|", "\\|") or "―" for key in ("date", "target", "action", "evidence")]
            lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="教材JSONを埋め込んだ1ファイルのHTMLを出力する")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("content", type=Path, nargs="?", help="教材JSONのパス")
    source.add_argument("--from-html", type=Path, help="作成済みの教材HTML（埋め込まれた教材JSONを使って作り直す）")
    parser.add_argument("-o", "--output", type=Path, required=True, help="出力するHTMLのパス")
    parser.add_argument("--factsheet", type=Path, help="ファクトシート（md）の出力先")
    parser.add_argument("--save-json", type=Path, help="使った教材JSONの保存先（--from-html で取り出したJSONを残すとき）")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="HTMLテンプレートのパス")
    args = parser.parse_args()

    if args.from_html:
        content = extract_content(args.from_html.read_text(encoding="utf-8"))
    else:
        content = json.loads(args.content.read_text(encoding="utf-8"))

    report = validate(content)
    for line in report.errors + report.warnings:
        print(line)
    if report.errors:
        print(f"エラーが {len(report.errors)}件あるため出力しません。")
        return 1

    html = embed_content(args.template.read_text(encoding="utf-8"), content)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"HTML を出力しました: {args.output}")

    if args.factsheet:
        args.factsheet.parent.mkdir(parents=True, exist_ok=True)
        args.factsheet.write_text(render_factsheet_markdown(content), encoding="utf-8")
        print(f"ファクトシートを出力しました: {args.factsheet}")
    if args.save_json:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"教材JSONを保存しました: {args.save_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
