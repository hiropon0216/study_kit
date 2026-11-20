"""教材JSONと、その部分のファイル（章ごと・総合演習）を同じ形で読み書きする。

章ごとのパイプライン（生成 → レビュー → 書き直し）では、教材をまとめる前の章ごとのファイルを直接直す。
差分・抜き出し・書き戻しのスクリプトがどの形のファイルも扱えるように、読むときに教材JSONの形に包み、
書くときに元の形に戻す。

  教材JSON        {"meta": …, "chapters": […], "finalExam": […], …}
  章ごとのファイル  {"chapter": {…}, "confusables": […], "extraFacts": […]}   work/chN.json
  総合演習のファイル {"questions": […]}                                        work/final_*.json
"""

import json
from pathlib import Path


def wrap(data):
    """どの形のデータも教材JSONの形にして返す。中の章・問題・事実は元のデータと同じオブジェクトを指す。"""
    if "chapters" in data:
        return data
    if "chapter" in data:
        return {
            "meta": {},
            "chapters": [data["chapter"]],
            "finalExam": [],
            "confusables": data.setdefault("confusables", []),
            "factsheet": data.setdefault("extraFacts", []),
        }
    if "questions" in data:
        return {"meta": {}, "chapters": [], "finalExam": data["questions"], "confusables": [], "factsheet": []}
    raise SystemExit("教材JSON・章ごとのファイル・総合演習のファイルのどれでもありません")


def load(path):
    """(元のデータ, 教材JSONの形に包んだもの) を返す。包んだほうを直すと、元のデータも直る。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data, wrap(data)


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
