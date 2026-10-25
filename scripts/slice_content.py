"""教材JSONから、レビュー担当に渡す部分だけを切り出す。

教材JSON全体は大きい（数百KB）。レビュー担当に全体を読ませると、読むだけで多くのトークンを使う。
そこで、レビューの範囲に必要なものだけを小さなファイルに切り出して渡す。

  chN      第N章の本文・問題すべてと、その章の節が sources に挙げた事実、その章に関わる confusables、
           それより前の章で前提を説明済みの固有名詞の一覧
  final    総合演習の問題すべてと、問題の refs が指す節の要約・事実
  outline  教材全体の骨組み（節・項目の見出し、要点、固有名詞の初出、問題の問題文と正解）。本文は入れない

使い方:
  python slice_content.py content.json --scope ch3 -o work/slices/ch3.json
  python slice_content.py content.json --all -d work/slices     # すべての章・final・outline を書く
"""

import argparse
import json
import re
import sys
from pathlib import Path

PREMISE = re.compile(r'<div class="sk-premise"(?: data-term="([^"]*)")?')
TAG = re.compile(r"<[^>]+>")
META_KEYS = ("id", "title", "purpose", "level", "goals", "targetVersion")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def meta_of(content):
    return {key: content["meta"][key] for key in META_KEYS if key in content["meta"]}


def facts_by_id(content):
    return {fact["id"]: fact for fact in content.get("factsheet", [])}


def premise_terms(text):
    return [(match.group(1) or "").strip() for match in PREMISE.finditer(text or "") if match.group(1)]


def chapter_questions(chapter):
    for section in chapter["sections"]:
        for item in section["items"]:
            yield from item.get("checks", [])
    yield from chapter.get("exercise", [])


def explained_terms(chapters):
    """渡された章の中で sk-premise を置いた語と、置いた場所。"""
    terms = []
    for chapter in chapters:
        for section in chapter["sections"]:
            for item in section["items"]:
                for term in premise_terms(item.get("title", "") + item.get("body", "")):
                    terms.append({"term": term, "where": f"{section['id']}#{item['id']}"})
    return terms


def confusables_for(content, section_ids):
    picked = []
    for pair in content.get("confusables", []):
        if any(ref.split("#")[0] in section_ids for ref in pair["items"]):
            picked.append(pair)
    return picked


def slice_chapter(content, chapter_id):
    chapters = content["chapters"]
    index = next((i for i, chapter in enumerate(chapters) if chapter["id"] == chapter_id), None)
    if index is None:
        raise SystemExit(f"章 {chapter_id} がありません")
    chapter = chapters[index]
    section_ids = {section["id"] for section in chapter["sections"]}
    by_id = facts_by_id(content)
    source_ids = []
    for section in chapter["sections"]:
        for fact_id in section.get("sources", []):
            if fact_id not in source_ids:
                source_ids.append(fact_id)
    return {
        "scope": chapter_id,
        "meta": meta_of(content),
        "explainedBefore": explained_terms(chapters[:index]),
        "chapter": chapter,
        "confusables": confusables_for(content, section_ids),
        "facts": [by_id[fact_id] for fact_id in source_ids if fact_id in by_id],
        "missingFacts": [fact_id for fact_id in source_ids if fact_id not in by_id],
    }


def answer_text(question):
    answer = question.get("answer")
    kind = question.get("type")
    options = question.get("options", [])
    if kind in ("choice", "predict") and isinstance(answer, int) and 0 <= answer < len(options):
        return options[answer]
    if kind == "truefalse":
        return "○" if answer else "×"
    if kind == "fill" and isinstance(answer, list):
        return " / ".join(answer)
    if kind == "order" and isinstance(answer, list):
        return " → ".join(answer)
    return answer


def question_outline(question):
    entry = {
        "id": question["id"],
        "type": question.get("type"),
        "prompt": TAG.sub("", question.get("prompt", "")),
        "answer": answer_text(question),
    }
    if question.get("refs"):
        entry["refs"] = question["refs"]
    return entry


def section_outline(section):
    return {
        "id": section["id"],
        "title": section["title"],
        "importance": section.get("importance"),
        "prerequisites": section.get("prerequisites", []),
        "keyPoints": section.get("keyPoints", []),
        "items": [
            {
                "id": item["id"],
                "type": item.get("type", "text"),
                "title": TAG.sub("", item.get("title", "")),
                "premises": premise_terms(item.get("title", "") + item.get("body", "")),
                "checks": [question_outline(q) for q in item.get("checks", [])],
            }
            for item in section["items"]
        ],
    }


def slice_outline(content):
    return {
        "scope": "outline",
        "meta": meta_of(content),
        "chapters": [
            {
                "id": chapter["id"],
                "title": chapter["title"],
                "sections": [section_outline(section) for section in chapter["sections"]],
                "exercise": [question_outline(q) for q in chapter.get("exercise", [])],
            }
            for chapter in content["chapters"]
        ],
        "finalExam": [question_outline(q) for q in content.get("finalExam", [])],
        "confusables": content.get("confusables", []),
    }


def slice_final(content):
    sections = {section["id"]: section for chapter in content["chapters"] for section in chapter["sections"]}
    referred = []
    for question in content.get("finalExam", []):
        for ref in question.get("refs", []):
            section_id = ref.split("#")[0]
            if section_id in sections and section_id not in referred:
                referred.append(section_id)
    by_id = facts_by_id(content)
    fact_ids = []
    for section_id in referred:
        for fact_id in sections[section_id].get("sources", []):
            if fact_id not in fact_ids:
                fact_ids.append(fact_id)
    return {
        "scope": "final",
        "meta": meta_of(content),
        "referredSections": [
            {"id": sid, "title": sections[sid]["title"], "keyPoints": sections[sid].get("keyPoints", [])}
            for sid in referred
        ],
        "finalExam": content.get("finalExam", []),
        "facts": [by_id[fact_id] for fact_id in fact_ids if fact_id in by_id],
    }


def make_slice(content, scope):
    if scope == "outline":
        return slice_outline(content)
    if scope == "final":
        return slice_final(content)
    return slice_chapter(content, scope)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{path}（{path.stat().st_size // 1024}KB）")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="教材JSONから、レビューの範囲に必要な部分だけを切り出す")
    parser.add_argument("content", type=Path, help="教材JSONのパス")
    parser.add_argument("--scope", help="ch1 などの章ID、final、outline")
    parser.add_argument("-o", "--output", type=Path, help="--scope の出力先")
    parser.add_argument("--all", action="store_true", help="すべての章と final・outline を書く")
    parser.add_argument("-d", "--dir", type=Path, help="--all の出力先フォルダ")
    args = parser.parse_args()

    content = load_json(args.content)
    if args.all:
        if not args.dir:
            parser.error("--all には -d が必要です")
        scopes = [chapter["id"] for chapter in content["chapters"]] + ["outline"]
        if content.get("finalExam"):
            scopes.append("final")
        for scope in scopes:
            write(args.dir / f"{scope}.json", make_slice(content, scope))
        return 0
    if not args.scope or not args.output:
        parser.error("--scope と -o を指定するか、--all と -d を指定してください")
    write(args.output, make_slice(content, args.scope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
