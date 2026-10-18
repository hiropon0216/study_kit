"""教材JSONを検査する。

検査内容:
  - スキーマ違反（必須項目・型・問題形式）
  - ID の重複
  - リンク切れ（refs が存在しない節・項目を指す、sources が存在しない事実IDを指す）
  - 正解の整合性（正解が選択肢にない、並べ替えの正解が項目の並べ替えになっていない）
  - 分量の目安（1節の項目3〜6個（重要度 A は8個まで）、重要度に応じたすぐ確認の数、章末演習10問以上、総合演習は節の数×10問以上）
  - 図解の使い忘れ（説明の項目ごとに図や表の部品を1つ以上）
  - 固有名詞の前提の説明（sk-premise）が、その語の初出より後ろに置かれていないか
  - 廃止した問題（retired）が教材に残っていないか、同じ問題文で作り直していないか
  - 言い換え問題（variants）・穴あき例題（faded）・まぎらわしい項目の組（confusables）の形

使い方:
  python validate.py content.json
終了コード: エラーがあれば 1、警告だけなら 0
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

QUESTION_TYPES = {"choice", "fill", "order", "predict", "truefalse"}
ITEM_TYPES = {"text", "example", "faded"}
BLANK_STEP_PATTERN = re.compile(r'<li class="sk-blank"')
MAX_VARIANTS = 2
FACT_RANKS = {"S", "A", "B"}
PURPOSES = {"資格", "実務", "教養"}
CONTENT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ITEM_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FORBIDDEN_HTML_PATTERNS = [
    (re.compile(r"<\s*(script|style|iframe|object|embed)\b", re.IGNORECASE), "<script> <style> <iframe> などのタグ"),
    (re.compile(r"\son[a-z]+\s*=", re.IGNORECASE), "on〜 のイベント属性"),
    (re.compile(r"\b(src|href)\s*=\s*\"\s*javascript:", re.IGNORECASE), "javascript: のURL"),
    (re.compile(r"\bsrc\s*=\s*\"https?://", re.IGNORECASE), "外部URLの画像・メディア（オフラインで表示できない）"),
]
STYLE_ATTRIBUTE_PATTERN = re.compile(r"\sstyle\s*=", re.IGNORECASE)
VISUAL_COMPONENT_PATTERN = re.compile(
    r'class="[^"]*\b(sk-nest|sk-flow|sk-compare|sk-figure|sk-badge-list|sk-terms|sk-cells|sk-steps)\b|<table\b'
)
PREMISE_PATTERN = re.compile(r'<div class="sk-premise"(?: data-term="([^"]*)")?')
TAG_PATTERN = re.compile(r"<[^>]+>")
CHAPTER_NUMBER_PATTERN = re.compile(r"^\s*(第\s*)?[0-9０-９]+\s*章")
SECTION_NUMBER_PATTERN = re.compile(r"^\s*[0-9０-９]+\s*[.．\-－]\s*[0-9０-９]+")
MIN_ITEMS_PER_SECTION = 3
MAX_ITEMS_PER_SECTION = 6
MAX_ITEMS_PER_SECTION_A = 8  # 重要度 A の盛りだくさんな節
MIN_KEY_POINTS = 2
MAX_KEY_POINTS = 6
MIN_EXERCISE_PER_CHAPTER = 10
FINAL_EXAM_QUESTIONS_PER_SECTION = 10
MAX_CHECKS_PER_ITEM = 4
# 節の重要度ごとの、1項目あたりのすぐ確認の数の下限（A：ゴールに直結する中心の節、B：標準、C：前提・補助）
IMPORTANCE_QUESTIONS_PER_ITEM = {"A": 2, "B": 1.5, "C": 1}


def item_checks(item):
    """項目のすぐ確認の配列を返す。checks（配列）と、1問だけの旧形式 check の両方を読む。形が違えば None。"""
    if "checks" in item:
        return item["checks"] if isinstance(item["checks"], list) else None
    check = item.get("check")
    if check is None:
        return []
    return [check]


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
    if meta.get("series") is not None and not isinstance(meta.get("series"), str):
        report.error("meta.series", "文字列にしてください")
    goals = meta.get("goals")
    if not isinstance(goals, list) or not goals or not all(_is_non_empty_string(g) for g in goals):
        report.error("meta.goals", "「〜できる」形式のゴールを1つ以上並べてください")

    exam = meta.get("exam")
    if meta.get("purpose") == "資格" and exam is None:
        report.warn("meta.exam", "資格トピックなのに exam がありません（模擬試験が出ません）")
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
    if STYLE_ATTRIBUTE_PATTERN.search(fragment):
        report.warn(where, "style 属性で見た目を上書きしています（見た目は template.html の部品に任せ、どの教材でも同じ見た目にします）")


def _mask_tags(fragment):
    """タグを同じ長さの空白にして、文字の位置を保ったまま本文の文字だけを残す。"""
    return TAG_PATTERN.sub(lambda m: " " * len(m.group()), fragment)


def _term_pattern(term):
    """英数字で始まる・終わる語は、別の単語の一部に一致しないようにする（Go と Google など）。"""
    pattern = re.escape(term)
    if re.match(r"[A-Za-z0-9]", term):
        pattern = r"(?<![A-Za-z0-9])" + pattern
    if re.search(r"[A-Za-z0-9]$", term):
        pattern += r"(?![A-Za-z0-9])"
    return re.compile(pattern)


def _question_text(question):
    """問題の文字列（言い換え問題 variants も含める）。"""
    if not isinstance(question, dict):
        return ""
    parts = []
    for form in _with_variants(question):
        parts += [form.get("prompt"), form.get("code"), form.get("explanation"), form.get("hint"), *(form.get("options") or [])]
    return _mask_tags(" ".join(str(part) for part in parts if isinstance(part, str)))


def _with_variants(question):
    """問題と、その言い換え問題（variants）を返す。"""
    variants = question.get("variants") if isinstance(question, dict) else None
    return [question] + [v for v in variants if isinstance(v, dict)] if isinstance(variants, list) else [question]


def _iter_items(chapters):
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        for section in chapter.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            for item in section.get("items", []) or []:
                if isinstance(item, dict):
                    yield chapter, section, item


def _check_premises(chapters, final_exam, report):
    """固有名詞の前提の説明（references/proper-nouns.md）が、その語の初出までに置かれているかを調べる。

    教材を学習順に並べた文字列（項目の本文 → その項目のすぐ確認 → … → 章末演習 → … → 総合演習）の中で、
    sk-premise の位置よりも前にその語が出てきていたら警告する。
    """
    texts = []  # (場所, 文字列)
    premises = []  # (語, 場所, texts の番号, 文字位置)
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        for section in chapter.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            for item in section.get("items", []) or []:
                if not isinstance(item, dict):
                    continue
                where = f"節 {section.get('id')} 項目 {item.get('id')}"
                title = item.get("title") if isinstance(item.get("title"), str) else ""
                body = item.get("body") if isinstance(item.get("body"), str) else ""
                text = title + "\n" + body
                for match in PREMISE_PATTERN.finditer(text):
                    term = (match.group(1) or "").strip()
                    if not term:
                        report.warn(where, "sk-premise に data-term（説明する固有名詞）がありません")
                        continue
                    premises.append((term, where, len(texts), match.start()))
                texts.append((where, _mask_tags(text)))
                for check in item_checks(item) or []:
                    texts.append((f"{where} のすぐ確認", _question_text(check)))
        for question in chapter.get("exercise", []) or []:
            texts.append((f"章 {chapter.get('id')} の章末演習", _question_text(question)))
    for question in final_exam:
        texts.append(("総合演習", _question_text(question)))

    first_premise = {}
    for term, where, text_index, position in premises:
        if term in first_premise:
            report.warn(where, f"「{term}」の sk-premise が {first_premise[term][0]} と重複しています（2回目以降は繰り返しません）")
            continue
        first_premise[term] = (where, text_index, position)

    for term, (where, text_index, position) in first_premise.items():
        pattern = _term_pattern(term)
        for index in range(text_index + 1):
            text_where, text = texts[index]
            match = pattern.search(text)
            if match and (index < text_index or match.start() < position):
                report.warn(where, f"「{term}」は {text_where} で先に出てきます。前提の説明（sk-premise）は初出の項目の、初出の文より前に置いてください")
                break


def _check_variants(question, where, ref_targets, report, register_id, is_check):
    """言い換え問題（variants）：同じ知識を別の問いで問う版。日を変えて出すたびに版を替える。"""
    variants = question.get("variants") if isinstance(question, dict) else None
    if variants is None:
        return
    if not isinstance(variants, list) or not variants:
        report.error(where, "variants は言い換え問題の配列にしてください（ないときは書きません）")
        return
    if len(variants) > MAX_VARIANTS:
        report.warn(where, f"variants が {len(variants)}個です（{MAX_VARIANTS}個までにします）")
    base_prompt = _normalize_prompt(TAG_PATTERN.sub("", str(question.get("prompt", ""))))
    for index, variant in enumerate(variants):
        variant_where = f"{where} の variants[{index}]"
        if not isinstance(variant, dict):
            report.error(variant_where, "オブジェクトが必要です")
            continue
        if _is_non_empty_string(variant.get("id")):
            if not variant["id"].startswith(f"{question.get('id')}-v"):
                report.warn(variant_where, f"ID は元の問題のIDに -v1, -v2 を付けます（例 {question.get('id')}-v1）")
            register_id(variant["id"], variant_where)
        if "variants" in variant:
            report.error(variant_where, "言い換え問題の中に variants は書けません")
        # refs を省くと元の問題の refs を使う
        _check_question(variant, variant_where, ref_targets, report, is_check=is_check or "refs" not in variant)
        if _normalize_prompt(TAG_PATTERN.sub("", str(variant.get("prompt", "")))) == base_prompt:
            report.error(variant_where, "元の問題と同じ問題文です（問い方を変えます）")
    if all(isinstance(v, dict) and v.get("type") == question.get("type") for v in variants):
        report.warn(where, "言い換え問題がすべて元の問題と同じ形式です（形式を変えると、問題の見た目でなく知識で答える練習になります）")


def _check_question(question, where, ref_targets, report, is_check=False):
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
        elif len(options) > 8:
            report.error(where, "options は8つまでにしてください")
        if not isinstance(answer, int) or isinstance(answer, bool) or not isinstance(options, list) or not 0 <= answer < len(options):
            report.error(where, "answer は options の範囲内のインデックス（0始まり）が必要です（正解が選択肢にありません）")
        if question_type == "predict" and not _is_non_empty_string(question.get("code")):
            report.error(where, "出力予測（predict）は code に読ませるコードやコマンドが必要です")

    elif question_type == "truefalse":
        if not isinstance(answer, bool):
            report.error(where, "truefalse の answer は true（○）か false（×）が必要です")
        if options not in (None, []):
            report.warn(where, "truefalse では options を使いません")
        if isinstance(question.get("prompt"), str) and re.search(r"正しければ|誤りなら|[○×]", question["prompt"]):
            report.warn(where, "truefalse の prompt には判定させる文だけを書きます（「正しければ○、誤りなら×」は学習エンジンが付けます）")

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

    if question.get("unit") is not None and (question_type != "fill" or not _is_non_empty_string(question.get("unit"))):
        report.warn(where, "unit（入力欄の後ろの単位）は fill の問題で、空でない文字列のときだけ使います")
    if question.get("hint") is not None and not _is_non_empty_string(question.get("hint")):
        report.error(where, "hint は空でない文字列にしてください")
    notes = question.get("optionNotes")
    if notes is not None:
        if question_type not in ("choice", "predict"):
            report.warn(where, "optionNotes は choice・predict の問題でだけ使います")
        elif not isinstance(notes, list) or not isinstance(options, list) or len(notes) != len(options) \
                or not all(n is None or _is_non_empty_string(n) for n in notes):
            report.error(where, "optionNotes は options と同じ長さの配列にし、各要素は解説の文字列か null にしてください")
    if question_type == "fill" and isinstance(answer, list) and answer \
            and not any(isinstance(a, str) and re.fullmatch(r"[\x20-\x7e]+", a) for a in answer):
        report.warn(where, "fill の answer に半角の英数字で打てる表記がありません（日本語でしか答えられない語は選択式にします）")

    refs = question.get("refs")
    if is_check:
        return  # すぐ確認は、置かれた項目が教科書の該当箇所になる
    if not isinstance(refs, list) or not refs:
        report.error(where, "refs に教科書の該当箇所（節ID か 節ID#項目ID）を1つ以上入れてください")
    else:
        for ref in refs:
            if ref not in ref_targets:
                report.error(where, f"refs のリンク切れ: '{ref}' という節・項目はありません")


def _iter_questions(chapters, final_exam):
    """教材のすべての問題を (問題, 場所) で返す。"""
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        for section in chapter.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            for item in section.get("items", []) or []:
                if not isinstance(item, dict):
                    continue
                for check in item_checks(item) or []:
                    if isinstance(check, dict):
                        yield check, f"すぐ確認 {check.get('id')}（{section.get('id')} {item.get('id')}）"
        for question in chapter.get("exercise", []) or []:
            if isinstance(question, dict):
                yield question, f"章末演習 {question.get('id')}"
    for question in final_exam:
        if isinstance(question, dict):
            yield question, f"総合演習 {question.get('id')}"


def _check_retired(retired, chapters, final_exam, report):
    """廃止した問題（retire_questions.py が記録する）が教材に残っていないか、同じ問題を作り直していないか。"""
    if retired is None:
        return
    if not isinstance(retired, list):
        report.error("retired", "廃止した問題の配列が必要です")
        return
    retired_ids = {}
    retired_prompts = {}
    for index, entry in enumerate(retired):
        where = f"retired[{index}]"
        if not isinstance(entry, dict):
            report.error(where, "オブジェクトが必要です")
            continue
        _check_required_strings(entry, ["id", "prompt"], where, report)
        retired_ids[entry.get("id")] = entry
        if _is_non_empty_string(entry.get("prompt")):
            retired_prompts[_normalize_prompt(entry["prompt"])] = entry
    for parent, parent_where in _iter_questions(chapters, final_exam):
        for question in _with_variants(parent):
            where = parent_where if question is parent else f"{parent_where} の言い換え {question.get('id')}"
            if question.get("id") in retired_ids:
                report.error(where, "削除した問題（retired）が残っています。教材から削除してください")
                continue
            prompt = _normalize_prompt(TAG_PATTERN.sub("", str(question.get("prompt", ""))))
            if prompt and prompt in retired_prompts:
                report.warn(where, f"削除した問題 {retired_prompts[prompt].get('id')} と同じ問題文です（学習者が不要とした問題を作り直していないか確認します）")


def _check_confusables(confusables, ref_targets, report):
    """まぎらわしい項目の組：今日の想起で並べて出し、教科書で見比べるよう促す。"""
    if confusables is None:
        return
    if not isinstance(confusables, list):
        report.error("confusables", "まぎらわしい項目の組の配列が必要です")
        return
    for index, group in enumerate(confusables):
        where = f"confusables[{index}]"
        if not isinstance(group, dict):
            report.error(where, "オブジェクトが必要です")
            continue
        items = group.get("items")
        if not isinstance(items, list) or len(items) < 2 or len(set(items)) != len(items):
            report.error(where, "items に、見比べる項目（節ID#項目ID）を重複なく2つ以上並べてください")
            items = []
        for key in items:
            if "#" not in str(key) or key not in ref_targets:
                report.error(where, f"items のリンク切れ: '{key}'（節ID#項目ID で、ある項目を指します）")
        if not _is_non_empty_string(group.get("note")):
            report.error(where, "note に見分けるポイントを1〜2文で書いてください")
        _check_html(group.get("note"), f"{where}.note", report)


def _normalize_prompt(text):
    return re.sub(r"\s+", "", text)


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

    # refs に書ける行き先：節ID と 節ID#項目ID
    section_ids = set()
    ref_targets = set()
    chapter_by_section = {}
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        for section in chapter.get("sections", []) or []:
            if not isinstance(section, dict):
                continue
            section_ids.add(section.get("id"))
            ref_targets.add(section.get("id"))
            chapter_by_section[section.get("id")] = chapter.get("id")
            for item in section.get("items", []) or []:
                if isinstance(item, dict):
                    ref_targets.add(f"{section.get('id')}#{item.get('id')}")

    def ref_chapter(ref):
        return chapter_by_section.get(str(ref).split("#")[0])

    seen_ids = {}
    # 問題を削除した項目（retired の item に記録がある）は check がなくてよい
    retired_items = {entry.get("item") for entry in content.get("retired") or [] if isinstance(entry, dict) and entry.get("item")}

    def register_id(identifier, where):
        if identifier in seen_ids:
            report.error(where, f"ID '{identifier}' が {seen_ids[identifier]} と重複しています")
        else:
            seen_ids[identifier] = where

    section_count = 0
    for chapter_index, chapter in enumerate(chapters):
        chapter_where = f"chapters[{chapter_index}]"
        if not isinstance(chapter, dict):
            report.error(chapter_where, "オブジェクトが必要です")
            continue
        _check_required_strings(chapter, ["id", "title"], chapter_where, report)
        chapter_where = f"章 {chapter.get('id')}"
        register_id(chapter.get("id"), chapter_where)
        if isinstance(chapter.get("title"), str) and CHAPTER_NUMBER_PATTERN.match(chapter["title"]):
            report.warn(chapter_where, "title に章番号を書かないでください（「第1章」は学習エンジンが付けます）")
        sections = chapter.get("sections")
        if not isinstance(sections, list) or not sections:
            report.error(chapter_where, "節の配列が必要です")
            sections = []
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict):
                report.error(f"{chapter_where}.sections[{section_index}]", "オブジェクトが必要です")
                continue
            section_count += 1
            section_where = f"節 {section.get('id')}"
            _check_required_strings(section, ["id", "title"], section_where, report)
            register_id(section.get("id"), section_where)
            if isinstance(section.get("title"), str) and SECTION_NUMBER_PATTERN.match(section["title"]):
                report.warn(section_where, "title に節番号を書かないでください（「1-2」は学習エンジンが付けます）")
            minutes = section.get("minutes")
            if minutes is not None and (not isinstance(minutes, int) or isinstance(minutes, bool) or minutes <= 0):
                report.error(section_where, "minutes（読了目安）は正の整数にしてください")
            for prerequisite in section.get("prerequisites") or []:
                if prerequisite not in section_ids:
                    report.error(section_where, f"prerequisites のリンク切れ: '{prerequisite}' という節はありません")

            sources = section.get("sources")
            if not isinstance(sources, list) or not sources:
                report.error(section_where, "sources にファクトシートの事実IDを1つ以上入れてください")
            else:
                for fact_id in sources:
                    if fact_id not in fact_ids:
                        report.error(section_where, f"sources のリンク切れ: '{fact_id}' はファクトシートにありません")

            key_points = section.get("keyPoints")
            if not isinstance(key_points, list) or not key_points or not all(_is_non_empty_string(p) for p in key_points):
                report.error(section_where, "keyPoints（この節の要点）に文字列を並べてください")
            elif not MIN_KEY_POINTS <= len(key_points) <= MAX_KEY_POINTS:
                report.warn(section_where, f"keyPoints が {len(key_points)}個です（目安は{MIN_KEY_POINTS}〜{MAX_KEY_POINTS}個）")

            items = section.get("items")
            if not isinstance(items, list) or not items:
                report.error(section_where, "items（本文の項目とすぐ確認）の配列が必要です")
                continue
            max_items = MAX_ITEMS_PER_SECTION_A if section.get("importance") == "A" else MAX_ITEMS_PER_SECTION
            if not MIN_ITEMS_PER_SECTION <= len(items) <= max_items:
                report.warn(section_where, f"項目が {len(items)}個です（目安は{MIN_ITEMS_PER_SECTION}〜{max_items}個。重要度 A の節は{MAX_ITEMS_PER_SECTION_A}個まで）")
            item_ids = set()
            text_items = 0
            section_questions = 0
            for item_index, item in enumerate(items):
                item_where = f"{section_where} items[{item_index}]"
                if not isinstance(item, dict):
                    report.error(item_where, "オブジェクトが必要です")
                    continue
                item_where = f"{section_where} 項目 {item.get('id')}"
                _check_required_strings(item, ["id", "title", "body"], item_where, report)
                if _is_non_empty_string(item.get("id")):
                    if not ITEM_ID_PATTERN.match(item["id"]):
                        report.error(item_where, "項目IDは英小文字・数字・ハイフンで書いてください（例 i1）")
                    if item["id"] in item_ids:
                        report.error(item_where, f"項目ID '{item['id']}' がこの節の中で重複しています")
                    item_ids.add(item["id"])
                item_type = item.get("type", "text")
                if item_type not in ITEM_TYPES:
                    report.error(item_where, f"type は {sorted(ITEM_TYPES)} のいずれかにしてください（省略すると text）")
                _check_html(item.get("title"), f"{item_where}.title", report)
                _check_html(item.get("body"), f"{item_where}.body", report)
                if item_type == "text":
                    text_items += 1
                    if isinstance(item.get("body"), str) and not VISUAL_COMPONENT_PATTERN.search(item["body"]):
                        report.warn(item_where, "図や表の部品（sk-figure / sk-nest / sk-flow / sk-compare / sk-cells など）が1つもありません。説明の項目には図解を1つ以上入れます")
                elif isinstance(item.get("body"), str) and "sk-steps" not in item["body"]:
                    report.warn(item_where, "例題・穴あき例題の解き方は sk-steps（手順）で書きます")
                if isinstance(item.get("body"), str):
                    has_blank = bool(BLANK_STEP_PATTERN.search(item["body"]))
                    if item_type == "faded" and not has_blank:
                        report.error(item_where, '穴あき例題（faded）は、伏せる段を <li class="sk-blank"> にします（1つ以上）')
                    if item_type != "faded" and has_blank:
                        report.warn(item_where, "sk-blank（伏せる段）は穴あき例題（type: faded）でだけ伏せられます")
                previous_type = items[item_index - 1].get("type", "text") if item_index > 0 and isinstance(items[item_index - 1], dict) else None
                if item_type == "faded" and previous_type != "example":
                    report.warn(item_where, "穴あき例題（faded）は、同じ考え方の例題（example）の直後に置きます")
                if "check" in item and "checks" in item:
                    report.error(item_where, "check と checks の両方があります（checks にまとめます）")
                checks = item_checks(item)
                if checks is None:
                    report.error(item_where, "checks はすぐ確認の問題の配列にしてください")
                    continue
                if not checks:
                    if f"{section.get('id')}#{item.get('id')}" not in retired_items:
                        report.error(item_where, "checks（すぐ確認の問題。1問以上）が必要です")
                    continue  # 学習者が不要とした問題をすべて削除した項目は、説明だけのページ
                if len(checks) > MAX_CHECKS_PER_ITEM:
                    report.warn(item_where, f"すぐ確認が {len(checks)}問です（1項目{MAX_CHECKS_PER_ITEM}問まで。多いときは項目を分けます）")
                section_questions += len(checks)
                for check in checks:
                    check_where = f"すぐ確認 {check.get('id') if isinstance(check, dict) else '?'}（{section.get('id')} {item.get('id')}）"
                    if not isinstance(check, dict):
                        report.error(check_where, "オブジェクトが必要です")
                        continue
                    register_id(check.get("id"), check_where)
                    _check_question(check, check_where, ref_targets, report, is_check=True)
                    _check_variants(check, check_where, ref_targets, report, register_id, True)
            if text_items == 0:
                report.error(section_where, "説明の項目（type が text）が1つもありません")
            # 重要度に応じた問題数（目的に近い節ほど問題を増やす）
            importance = section.get("importance")
            if importance is None:
                report.warn(section_where, "importance（重要度 A／B／C）がありません。章立てで決めた重要度を入れます")
            elif importance not in IMPORTANCE_QUESTIONS_PER_ITEM:
                report.error(section_where, f"importance は {sorted(IMPORTANCE_QUESTIONS_PER_ITEM)} のいずれかにしてください")
            else:
                expected_questions = math.ceil(len(items) * IMPORTANCE_QUESTIONS_PER_ITEM[importance])
                retired_here = sum(1 for entry in content.get("retired") or [] if isinstance(entry, dict) and str(entry.get("item", "")).startswith(f"{section.get('id')}#"))
                if section_questions + retired_here < expected_questions:
                    report.warn(section_where, f"重要度 {importance} の節なのに、すぐ確認が {section_questions}問です（項目 {len(items)}個 × {IMPORTANCE_QUESTIONS_PER_ITEM[importance]} = {expected_questions}問以上にします）")

        exercise = chapter.get("exercise")
        if not isinstance(exercise, list):
            report.error(chapter_where, "exercise（章末演習）の問題配列が必要です")
            exercise = []
        if len(exercise) < MIN_EXERCISE_PER_CHAPTER:
            report.warn(chapter_where, f"章末演習が {len(exercise)}問です（{MIN_EXERCISE_PER_CHAPTER}問以上にします）")
        for question in exercise:
            where = f"章末演習 {question.get('id') if isinstance(question, dict) else '?'}"
            if isinstance(question, dict):
                register_id(question.get("id"), where)
            _check_question(question, where, ref_targets, report)
            _check_variants(question, where, ref_targets, report, register_id, False)
            if isinstance(question, dict) and isinstance(question.get("refs"), list):
                if question["refs"] and all(ref_chapter(ref) != chapter.get("id") for ref in question["refs"]):
                    report.warn(where, "refs がこの章の節を1つも指していません（章末演習はその章の内容から出します）")

    final_exam = content.get("finalExam")
    if not isinstance(final_exam, list):
        report.error("finalExam", "総合演習の問題配列が必要です（ない場合は []）")
        final_exam = []
    for question in final_exam:
        where = f"総合演習 {question.get('id') if isinstance(question, dict) else '?'}"
        if isinstance(question, dict):
            register_id(question.get("id"), where)
        _check_question(question, where, ref_targets, report)
        _check_variants(question, where, ref_targets, report, register_id, False)
        if isinstance(question, dict) and isinstance(question.get("refs"), list):
            chapters_used = {ref_chapter(ref) for ref in question["refs"]} - {None}
            if len(chapters_used) < 2:
                report.warn(where, "refs が1つの章にしか及んでいません（総合演習は複数の章の知識を組み合わせる問題にします）")
    expected = section_count * FINAL_EXAM_QUESTIONS_PER_SECTION
    if chapters and len(final_exam) < expected:
        report.warn("finalExam", f"総合演習が {len(final_exam)}問です（節の数×{FINAL_EXAM_QUESTIONS_PER_SECTION} = {expected}問以上にします）")

    _check_premises(chapters, final_exam, report)
    _check_retired(content.get("retired"), chapters, final_exam, report)
    _check_confusables(content.get("confusables"), ref_targets, report)

    used_fact_ids = {
        fact_id
        for chapter in chapters if isinstance(chapter, dict)
        for section in chapter.get("sections", []) or [] if isinstance(section, dict)
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
