"""章ごとに書いた JSON を1つの教材JSON（content.json）にまとめる。章1つだけを包んで検査することもできる。

フェーズ3で、章ごとに別のサブエージェントが書いたファイルをまとめるのに使う。

  <出力先>/work/meta.json     meta と、章をまたぐ前提の節（prerequisites）
  <出力先>/work/ch1.json …    章ごとのファイル（{"chapter": …, "confusables": […], "extraFacts": […]}）
  <出力先>/work/final_*.json  総合演習（{"questions": […]}。いくつかに分けてよい）
  <出力先>/factsheet.md       ファクトシート（references/factsheet.md の書式）

使い方:
  python assemble.py <出力先>              # すべてをまとめて <出力先>/content.json に書く
  python assemble.py <出力先> --force      # content.json がすでにあっても書き直す
  python assemble.py <出力先> --check 3    # 第3章だけを包んだ仮の教材を validate.py で検査する

meta.json の形:
  {"meta": {"id": …, "title": …, "purpose": …, "goals": […], …},
   "prerequisites": {"ch2-s1": ["ch1-s3"], …}}

章ごとのファイルの prerequisites は、章だけの検査ではほかの章の節を指せないため、meta.json にまとめて書き、
すべてをまとめるときに入れる。

content.json を作ったあとは、content.json が正になる。レビューの修正は content.json を直し、
章ごとのファイルからまとめ直さない（まとめ直すと修正が消える。そのため --force がないと上書きしない）。
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
FACT_ROW = re.compile(r"^\|\s*(F-\d+)\s*\|\s*(.+?)\s*\|\s*(\S+)\s*\|\s*([SAB])\s*\|(.*)$")
FACT_ID = re.compile(r"F-\d+")
CHAPTER_FILE = re.compile(r"^ch(\d+)\.json$")
# 章だけを包んだ検査では、教材全体を前提にした警告が必ず出るので表示しない
CHECK_NOISE = ("finalExam", "総合演習", "どの節の sources からも参照されていません")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_factsheet(path):
    """ファクトシートの表の行を読む。信頼度 B の行は、使用箇所より後ろの列にある事実IDを backedBy にする。"""
    facts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = FACT_ROW.match(line)
        if not match:
            continue
        fact = {"id": match.group(1), "claim": match.group(2), "url": match.group(3), "rank": match.group(4)}
        if fact["rank"] == "B":
            rest = match.group(5).split("|")[1:]  # 使用箇所の列より後ろ
            backed = FACT_ID.findall("|".join(rest))
            if backed:
                fact["backedBy"] = backed
        facts.append(fact)
    return facts


def chapter_files(work):
    files = []
    for path in work.iterdir():
        match = CHAPTER_FILE.match(path.name)
        if match:
            files.append((int(match.group(1)), path))
    return [path for _, path in sorted(files)]


def build(out_dir, only=None):
    work = out_dir / "work"
    meta_file = load_json(work / "meta.json")
    facts = load_factsheet(out_dir / "factsheet.md")
    known = {fact["id"] for fact in facts}

    files = chapter_files(work)
    if only is not None:
        files = [path for path in files if path.name == f"ch{only}.json"]
        if not files:
            raise SystemExit(f"{work / f'ch{only}.json'} がありません")

    chapters, confusables = [], []
    for path in files:
        data = load_json(path)
        chapters.append(data["chapter"])
        confusables.extend(data.get("confusables", []))
        for fact in data.get("extraFacts", []):
            if fact["id"] in known:
                continue
            facts.append({key: fact[key] for key in ("id", "claim", "url", "rank", "backedBy") if key in fact})
            known.add(fact["id"])

    final_exam = []
    if only is None:
        prerequisites = meta_file.get("prerequisites", {})
        for chapter in chapters:
            for section in chapter["sections"]:
                if section["id"] in prerequisites:
                    section["prerequisites"] = prerequisites[section["id"]]
        for path in sorted(work.glob("final_*.json")):
            final_exam.extend(load_json(path)["questions"])

    return {
        "meta": meta_file["meta"],
        "chapters": chapters,
        "finalExam": final_exam,
        "confusables": confusables,
        "factsheet": facts,
    }


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def check_chapter(out_dir, number):
    content = build(out_dir, only=number)
    tmp = out_dir / "work" / f"_check_ch{number}.json"
    write_json(tmp, content)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate.py"), str(tmp)],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    errors = warnings = 0
    for line in (result.stdout + result.stderr).splitlines():
        if line.startswith("エラー ") and "件 / 警告" in line:
            continue
        if any(noise in line for noise in CHECK_NOISE):
            continue
        if line.startswith("[ERROR]"):
            errors += 1
        elif line.startswith("[WARN]"):
            warnings += 1
        print(line)
    print(f"第{number}章：エラー {errors}件 / 警告 {warnings}件（教材全体を前提にした警告は除いた）")
    tmp.unlink()
    return 1 if errors else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="章ごとの JSON を1つの教材JSONにまとめる")
    parser.add_argument("out_dir", type=Path, help="教材の出力先フォルダ")
    parser.add_argument("--check", type=int, metavar="N", help="第N章だけを包んで validate.py で検査する")
    parser.add_argument("--force", action="store_true", help="content.json がすでにあっても書き直す")
    args = parser.parse_args()

    if args.check is not None:
        return check_chapter(args.out_dir, args.check)

    target = args.out_dir / "content.json"
    content = build(args.out_dir)
    if target.exists():
        if not args.force:
            print(f"{target} はすでにあります。レビューの修正が消えるため上書きしません（書き直すなら --force）")
            return 1
        old = load_json(target)
        for key in ("factCheckLog", "retired"):
            if old.get(key):
                content[key] = old[key]
    write_json(target, content)
    print(f"{target} に書きました：{len(content['chapters'])}章、総合演習 {len(content['finalExam'])}問、事実 {len(content['factsheet'])}件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
