"""学習者が「この問題はもう出さない」にした問題を、教材から削除する。

学習者が ⚙ 設定から書き出した学習履歴（JSON）を読み、出さない問題を教材JSONから消す。

  - 章末演習・総合演習の問題：配列から削除する
  - すぐ確認の問題：項目の check を削除する（項目の説明は残し、問題のないページになる）
  - 削除した問題は、教材JSONの retired に記録する。作り直しで同じ問題を復活させないため

使い方:
  python retire_questions.py content.json 学習履歴.json -o content.json
  python retire_questions.py content.json 学習履歴.json            # 何を削除するかを表示するだけ
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

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
    """教材JSONから問題を削除し、削除した問題の一覧を返す。"""
    targets = set(ids)
    retired = content.setdefault("retired", [])
    removed = []

    def record(question, kind, where, item_ref=None):
        entry = {"id": question["id"], "kind": kind, "where": where, "prompt": plain(question.get("prompt")), "retiredOn": today}
        if item_ref:
            entry["item"] = item_ref
        retired.append(entry)
        removed.append(entry)

    for chapter_no, chapter in enumerate(content.get("chapters") or [], start=1):
        for section_no, section in enumerate(chapter.get("sections") or [], start=1):
            for item in section.get("items") or []:
                check = item.get("check")
                if isinstance(check, dict) and check.get("id") in targets:
                    record(check, "check", f"{chapter_no}-{section_no} {section.get('title')} ›「{plain(item.get('title'))}」", f"{section.get('id')}#{item.get('id')}")
                    del item["check"]
        kept = []
        for question in chapter.get("exercise") or []:
            if question.get("id") in targets:
                record(question, "exercise", f"第{chapter_no}章 章末演習")
            else:
                kept.append(question)
        chapter["exercise"] = kept

    kept = []
    for question in content.get("finalExam") or []:
        if question.get("id") in targets:
            record(question, "final", "総合演習")
        else:
            kept.append(question)
    content["finalExam"] = kept
    return removed


def main():
    parser = argparse.ArgumentParser(description="出さない問題を教材から削除する")
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
    removed = retire(content, ids, datetime.date.today().isoformat())
    if not removed:
        print("削除する問題はありません（出さない問題がないか、すでに削除済みです）。")
        return 0
    print(f"削除する問題 {len(removed)}問")
    for entry in removed:
        print(f"  {entry['id']}（{entry['where']}）{entry['prompt']}")

    if args.output:
        args.output.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"教材JSONを出力しました: {args.output}")
    else:
        print("（-o を付けると教材JSONを書き換えます）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
