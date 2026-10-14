"""学習者が「この問題はもう出さない」にした問題を、教材から廃止する。

学習者が ⚙ 設定から書き出した学習履歴（JSON）を読み、出さない問題を教材JSONから外す。

  - 章末演習・総合演習の問題：教材JSONから削除する
  - すぐ確認の問題：項目に1問ずつ必要なので削除しない。新しいIDの問題に差し替えるよう一覧に出す
    （差し替えるまで validate.py がエラーにする）
  - 廃止した問題は、教材JSONの retired に記録する。作り直しで同じ問題を復活させないため

使い方:
  python retire_questions.py content.json 学習履歴.json -o content.json
  python retire_questions.py content.json 学習履歴.json            # 何を廃止するかを表示するだけ
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

MIN_EXERCISE_PER_CHAPTER = 10
FINAL_EXAM_QUESTIONS_PER_SECTION = 10
TAG_PATTERN = re.compile(r"<[^>]+>")


def plain(html):
    return TAG_PATTERN.sub("", str(html or "")).strip()


def excluded_ids(history):
    """書き出した学習履歴から、出さない問題のIDを集める。"""
    ids = []
    for entry in history.get("excludedQuestions") or []:
        if isinstance(entry, dict) and entry.get("id"):
            ids.append(entry["id"])
    for qid, record in (history.get("questions") or {}).items():
        if isinstance(record, dict) and record.get("status") == "excluded" and qid not in ids:
            ids.append(qid)
    return ids


def retire(content, ids, today):
    """教材JSONを書き換え、廃止の結果を返す。"""
    targets = set(ids)
    retired = content.setdefault("retired", [])
    already = {entry.get("id") for entry in retired if isinstance(entry, dict)}
    result = {"removed": [], "replace": [], "unknown": [], "already": []}
    found = set()

    def record(question, kind, where):
        found.add(question["id"])
        if question["id"] in already:
            result["already"].append(question["id"])
            return
        retired.append({"id": question["id"], "kind": kind, "where": where, "prompt": plain(question.get("prompt")), "retiredOn": today})
        already.add(question["id"])

    section_count = 0
    for chapter_no, chapter in enumerate(content.get("chapters") or [], start=1):
        for section_no, section in enumerate(chapter.get("sections") or [], start=1):
            section_count += 1
            for item in section.get("items") or []:
                check = item.get("check") or {}
                if check.get("id") in targets:
                    where = f"{chapter_no}-{section_no} {section.get('title')} ›「{plain(item.get('title'))}」のすぐ確認"
                    record(check, "check", where)
                    result["replace"].append({"id": check["id"], "where": where, "prompt": plain(check.get("prompt"))})
        kept = []
        for question in chapter.get("exercise") or []:
            if question.get("id") in targets:
                where = f"第{chapter_no}章 章末演習"
                record(question, "exercise", where)
                result["removed"].append({"id": question["id"], "where": where, "prompt": plain(question.get("prompt"))})
            else:
                kept.append(question)
        chapter["exercise"] = kept
        if len(kept) < MIN_EXERCISE_PER_CHAPTER:
            result.setdefault("short", []).append(f"第{chapter_no}章 章末演習が {len(kept)}問です（あと {MIN_EXERCISE_PER_CHAPTER - len(kept)}問足します）")

    kept = []
    for question in content.get("finalExam") or []:
        if question.get("id") in targets:
            record(question, "final", "総合演習")
            result["removed"].append({"id": question["id"], "where": "総合演習", "prompt": plain(question.get("prompt"))})
        else:
            kept.append(question)
    content["finalExam"] = kept
    expected = section_count * FINAL_EXAM_QUESTIONS_PER_SECTION
    if len(kept) < expected:
        result.setdefault("short", []).append(f"総合演習が {len(kept)}問です（あと {expected - len(kept)}問足します）")

    # 前に廃止して、もう教材にない問題は「記録済み」。廃止の記録にもない問題は、作り直しで消えた問題
    for qid in ids:
        if qid in found:
            continue
        if qid in already:
            result["already"].append(qid)
        else:
            result["unknown"].append(qid)
    return result


def main():
    parser = argparse.ArgumentParser(description="出さない問題を教材から廃止する")
    parser.add_argument("content", type=Path, help="教材JSONのパス")
    parser.add_argument("history", type=Path, help="⚙ 設定から書き出した学習履歴（JSON）")
    parser.add_argument("-o", "--output", type=Path, help="書き換えた教材JSONの出力先（省略すると表示だけ）")
    args = parser.parse_args()

    try:
        content = json.loads(args.content.read_text(encoding="utf-8"))
        history = json.loads(args.history.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"[ERROR] 読み込めません: {error}")
        return 1
    content_id = (content.get("meta") or {}).get("id")
    if history.get("contentId") != content_id:
        print(f"[ERROR] 別の教材の学習履歴です（履歴: {history.get('contentId')} / 教材: {content_id}）")
        return 1

    ids = excluded_ids(history)
    if not ids:
        print("出さない問題はありません。")
        return 0
    result = retire(content, ids, datetime.date.today().isoformat())

    print(f"出さない問題 {len(ids)}問")
    for entry in result["removed"]:
        print(f"  削除   {entry['id']}（{entry['where']}）{entry['prompt']}")
    for entry in result["replace"]:
        print(f"  差し替え {entry['id']}（{entry['where']}）{entry['prompt']}")
    for qid in result["already"]:
        print(f"  記録済み {qid}（前に廃止済み）")
    for qid in result["unknown"]:
        print(f"  [WARN] {qid} は教材にありません（作り直しで消えた問題）")
    for line in result.get("short", []):
        print(f"  [補充] {line}")
    if result["replace"]:
        print("すぐ確認は新しいIDの問題に差し替えてください（差し替えるまで validate.py がエラーにします）。")

    if args.output:
        args.output.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"教材JSONを出力しました: {args.output}")
    else:
        print("（-o を付けると教材JSONを書き換えます）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
