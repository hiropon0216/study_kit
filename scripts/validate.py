"""教材JSONを検査する。

検査内容:
  - スキーマ違反（必須項目・型・問題形式）
  - ID の重複
  - リンク切れ（refs が存在しない節を指す、sources が存在しない事実IDを指す）
  - 正解の整合性（正解が選択肢にない、並べ替えの正解が項目の並べ替えになっていない）
  - 分量の目安（1節6〜10問、総合演習は章数×2問程度）

使い方:
  python validate.py content.json
終了コード: エラーがあれば 1、警告だけなら 0
"""

import argparse
import json
import re
import sys
from pathlib import Path

QUESTION_TYPES = {"choice", "fill", "order", "predict"}
FACT_RANKS = {"S", "A", "B"}
PURPOSES = {"資格", "実務", "教養"}
CONTENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FORBIDDEN_HTML_PATTERNS = [
    (re.compile(r"<\s*(script|style|iframe|object|embed)\b", re.IGNORECASE), "<script> <style> <iframe> などのタグ"),
    (re.compile(r"\son[a-z]+\s*=", re.IGNORECASE), "on〜 のイベント属性"),
    (re.compile(r"\b(src|href)\s*=\s*\"\s*javascript:", re.IGNORECASE), "javascript: のURL"),
    (re.compile(r"\bsrc\s*=\s*\"https?://", re.IGNORECASE), "外部URLの画像・メディア（オフラインで表示できない）"),
]
STYLE_ATTRIBUTE_PATTERN = re.compile(r"\sstyle\s*=", re.IGNORECASE)
VISUAL_COMPONENT_PATTERN =re.compile(r'class="[^"]*\b(sk-nest|sk-flow|sk-compare|sk-figure|sk-badge-list|sk-terms)\b|<table\b')
MIN_QUESTIONS_PER_SECTION = 6
MAX_QUESTIONS_PER_SECTION = 10
FINAL_EXAM_QUESTIONS_PER_CHAPTER = 2


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append(f"[ERROR] {where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"[WARN]  {where}: {message}")


def _is_non_empty_string(value):
    return isinstance(value, str) and value.strip() != ""


def _check_required_strings(obj, keys, where, report):
    for key in keys:
        if not _is_non_empty_string(obj.get(key)):
            report.error(where, f"'{key}' は空でない文字列が必要です")


def _check_meta(meta, report):
    if not isinstance(meta, dict):
        report.error("meta", "オブジェクトが必要です")
        return
    _check_required_strings(meta, ["id", "title", "purpose"], "meta", report)
    if _is_non_empty_string(meta.get("id")) and not CONTENT_ID_PATTERN.match(meta["id"]):
        report.error("meta.id", "英小文字・数字・ハイフンだけで書いてください（保存キー study-kit:{id} に使います）")
    if meta.get("purpose") not in PURPOSES:
        report.error("meta.purpose", f"{sorted(PURPOSES)} のいずれかにしてください")
    goals = meta.get("goals")
    if not isinstance(goals, list) or not goals or not all(_is_non_empty_string(g) for g in goals):
        report.error("meta.goals", "「〜できる」形式のゴールを1つ以上並べてください")

    exam = meta.get("exam")
    if meta.get("purpose") == "資格" and exam is None:
        report.warn("meta.exam", "資格トピックなのに exam がありません（模擬試験モードが出ません）")
    if exam is not None:
        if not isinstance(exam, dict):
            report.error("meta.exam", "null かオブジェクトにしてください")
            return
        for key in ["questionCount", "minutes"]:
            if not isinstance(exam.get(key), int) or exam[key] <= 0:
                report.error("meta.exam", f"'{key}' は正の整数が必要です")
        passing = exam.get("passingRate")
        if passing is not None and not (isinstance(passing, (int, float)) and 0 < passing <= 100):
            report.error("meta.exam.passingRate", "1〜100 の数値にしてください")


def _check_html(fragment, where, report):
    if not isinstance(fragment, str):
        return
    for pattern, label in FORBIDDEN_HTML_PATTERNS:
        if pattern.search(fragment):
            report.error(where, f"使えない HTML が含まれています: {label}")


def _check_body_components(body, where, report):
    """教科書の部品（references/textbook-components.md）の使い忘れを警告する。"""
    if not isinstance(body, str):
        return
    if 'class="sk-goals"' not in body:
        report.warn(where, "先頭に sk-goals（この節でわかること）がありません")
    if 'class="sk-summary"' not in body:
        report.warn(where, "最後に sk-summary（まとめ）がありません")
    if STYLE_ATTRIBUTE_PATTERN.search(body):
        report.warn(where, "style 属性で見た目を上書きしています（見た目は template.html の部品に任せ、どの教材でも同じ見た目にします）")
    if not VISUAL_COMPONENT_PATTERN.search(body):
        report.warn(where, "図や表の部品（sk-nest / sk-flow / sk-compare / sk-figure など）が1つもありません")


def _check_question(question, where, section_ids, report):
    if not isinstance(question, dict):
        report.error(where, "問題はオブジェクトが必要です")
        return
    _check_required_strings(question, ["id", "type", "prompt", "explanation"], where, report)
    _check_html(question.get("prompt"), f"{where}.prompt", report)
    _check_html(question.get("explanation"), f"{where}.explanation", report)
    question_type = question.get("type")
    if question_type not in QUESTION_TYPES:
        report.error(where, f"type は {sorted(QUESTION_TYPES)} のいずれかにしてください")
        return

    options = question.get("options")
    answer = question.get("answer")

    if question_type in ("choice", "predict"):
        if not isinstance(options, list) or len(options) < 2 or not all(_is_non_empty_string(o) for o in options):
            report.error(where, "options は2つ以上の文字列が必要です")
        elif len(set(options)) != len(options):
            report.error(where, "options に同じ選択肢が重複しています")
        if not isinstance(answer, int) or isinstance(answer, bool) or not isinstance(options, list) or not 0 <= answer < len(options):
            report.error(where, "answer は options の範囲内のインデックス（0始まり）が必要です（正解が選択肢にありません）")
        if question_type == "predict" and not _is_non_empty_string(question.get("code")):
            report.error(where, "出力予測（predict）は code に読ませるコードやコマンドが必要です")

    elif question_type == "fill":
        if not isinstance(answer, list) or not answer or not all(_is_non_empty_string(a) for a in answer):
            report.error(where, "fill の answer は許容表記の文字列配列が必要です")
        if options not in (None, []):
            report.warn(where, "fill では options を使いません")

    elif question_type == "order":
        if not isinstance(options, list) or len(options) < 3 or not all(_is_non_empty_string(o) for o in options):
            report.error(where, "order の options は3つ以上の文字列が必要です")
        elif len(set(options)) != len(options):
            report.error(where, "order の options に同じ項目が重複しています")
        elif not isinstance(answer, list) or sorted(answer) != sorted(options):
            report.error(where, "order の answer は options と同じ項目を正しい順に並べた配列が必要です")
        elif answer == options:
            report.error(where, "order の options（初回の表示順）が正解と同じ順になっています")

    refs = question.get("refs")
    if not isinstance(refs, list) or not refs:
        report.error(where, "refs に教科書の該当節IDを1つ以上入れてください")
    else:
        for ref in refs:
            if ref not in section_ids:
                report.error(where, f"refs のリンク切れ: '{ref}' という節はありません")


def validate(content):
    report = Report()
    if not isinstance(content, dict):
        report.error("root", "JSON のトップはオブジェクトが必要です")
        return report

    _check_meta(content.get("meta"), report)

    factsheet = content.get("factsheet")
    fact_ids = set()
    if not isinstance(factsheet, list) or not factsheet:
        report.error("factsheet", "事実の配列が必要です（教材はファクトシートの事実だけで作ります）")
        factsheet = []
    for index, fact in enumerate(factsheet):
        where = f"factsheet[{index}]"
        if not isinstance(fact, dict):
            report.error(where, "オブジェクトが必要です")
            continue
        _check_required_strings(fact, ["id", "claim", "url", "rank"], where, report)
        if fact.get("id") in fact_ids:
            report.error(where, f"事実ID '{fact.get('id')}' が重複しています")
        fact_ids.add(fact.get("id"))
        if not str(fact.get("url", "")).startswith(("http://", "https://")):
            report.error(where, "url は http(s) で始まる出典URLが必要です")
        if fact.get("rank") not in FACT_RANKS:
            report.error(where, f"rank は {sorted(FACT_RANKS)} のいずれかにしてください")
        if fact.get("rank") == "B" and not fact.get("backedBy"):
            report.error(where, "rank B の事実は backedBy に裏付けとなる rank S の事実IDが必要です")

    chapters = content.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        report.error("chapters", "章の配列が必要です")
        chapters = []

    section_ids = {
        section.get("id")
        for chapter in chapters if isinstance(chapter, dict)
        for section in chapter.get("sections", []) if isinstance(section, dict)
    }
    seen_ids = {}

    def register_id(identifier, where):
        if identifier in seen_ids:
            report.error(where, f"ID '{identifier}' が {seen_ids[identifier]} と重複しています")
        else:
            seen_ids[identifier] = where

    for chapter_index, chapter in enumerate(chapters):
        chapter_where = f"chapters[{chapter_index}]"
        if not isinstance(chapter, dict):
            report.error(chapter_where, "オブジェクトが必要です")
            continue
        _check_required_strings(chapter, ["id", "title"], chapter_where, report)
        register_id(chapter.get("id"), chapter_where)
        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            report.error(chapter_where, "節の配列が必要です")
            continue
        for section_index, section in enumerate(sections):
            section_where = f"{chapter_where}.sections[{section_index}]"
            if not isinstance(section, dict):
                report.error(section_where, "オブジェクトが必要です")
                continue
            section_where = f"節 {section.get('id')}"
            _check_required_strings(section, ["id", "title", "body"], section_where, report)
            register_id(section.get("id"), section_where)
            _check_html(section.get("body"), f"{section_where}.body", report)
            _check_body_components(section.get("body"), section_where, report)
            sources = section.get("sources")
            if not isinstance(sources, list) or not sources:
                report.error(section_where, "sources にファクトシートの事実IDを1つ以上入れてください")
            else:
                for fact_id in sources:
                    if fact_id not in fact_ids:
                        report.error(section_where, f"sources のリンク切れ: '{fact_id}' はファクトシートにありません")
            questions = section.get("questions")
            if not isinstance(questions, list):
                report.error(section_where, "questions の配列が必要です")
                continue
            if not MIN_QUESTIONS_PER_SECTION <= len(questions) <= MAX_QUESTIONS_PER_SECTION:
                report.warn(section_where, f"問題数が {len(questions)}問です（目安は{MIN_QUESTIONS_PER_SECTION}〜{MAX_QUESTIONS_PER_SECTION}問）")
            for question in questions:
                where = f"問題 {question.get('id') if isinstance(question, dict) else '?'}"
                if isinstance(question, dict):
                    register_id(question.get("id"), where)
                _check_question(question, where, section_ids, report)

    final_exam = content.get("finalExam")
    if not isinstance(final_exam, list):
        report.error("finalExam", "総合演習の問題配列が必要です")
        final_exam = []
    chapter_by_section = {
        section.get("id"): chapter.get("id")
        for chapter in chapters if isinstance(chapter, dict)
        for section in chapter.get("sections", []) if isinstance(section, dict)
    }
    for question in final_exam:
        where = f"総合演習 {question.get('id') if isinstance(question, dict) else '?'}"
        if isinstance(question, dict):
            register_id(question.get("id"), where)
        _check_question(question, where, section_ids, report)
        if isinstance(question, dict) and isinstance(question.get("refs"), list):
            chapters_used = {chapter_by_section.get(ref) for ref in question["refs"]} - {None}
            if len(chapters_used) < 2:
                report.warn(where, "refs が1つの章にしか及んでいません（総合演習は複数の章の知識を組み合わせる問題にします）")
    expected = len(chapters) * FINAL_EXAM_QUESTIONS_PER_CHAPTER
    if chapters and not expected * 0.5 <= len(final_exam) <= expected * 1.5:
        report.warn("finalExam", f"総合演習が {len(final_exam)}問です（目安は章数×2 = {expected}問程度）")

    used_fact_ids = {
        fact_id
        for chapter in chapters if isinstance(chapter, dict)
        for section in chapter.get("sections", []) if isinstance(section, dict)
        for fact_id in section.get("sources", []) or []
    }
    for fact_id in sorted(fact_ids - used_fact_ids - {None}):
        report.warn(f"factsheet {fact_id}", "どの節の sources からも参照されていません")

    return report


def main():
    parser = argparse.ArgumentParser(description="教材JSONのスキーマ・リンク切れ・正解の整合性を検査する")
    parser.add_argument("content", type=Path, help="教材JSONのパス")
    args = parser.parse_args()

    try:
        content = json.loads(args.content.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"[ERROR] {args.content}: 読み込めません: {error}")
        return 1

    report = validate(content)
    for line in report.errors + report.warnings:
        print(line)
    print(f"エラー {len(report.errors)}件 / 警告 {len(report.warnings)}件")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
