# 教材データ（JSON）のスキーマ

`validate.py` がこの定義に沿って検査する。完全な例（お手本）は `examples/k8s-practical/content.json` にある。トピックが変わっても、この構造と部品の使い方を踏襲する。お手本の事実は未検証のサンプルなので、内容は流用しない。

## 全体の形

```
meta
chapters[]                 章（並び順＝学習順）
  sections[]               節
    items[]                項目：説明（インプット）とすぐ確認1問（アウトプット）の組
      check                すぐ確認の問題
    keyPoints[]            この節の要点
  exercise[]               章末演習の問題（10問以上）
finalExam[]                総合演習の問題
factsheet[]                ファクトシートの事実
```

節のページは見開きで、1項目が1見開きになる。左ページに項目の説明、右ページにその項目のすぐ確認1問を出す（読む前に問題文だけを見せる予告問題）。項目1 → 項目2 → … とページをめくって進む。

## トップレベル

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `meta` | object | ○ | 教材の情報 |
| `chapters` | array | ○ | 章の配列（並び順＝学習順） |
| `finalExam` | array | ○ | 総合演習の問題の配列（作らない場合は `[]`） |
| `factsheet` | array | ○ | ファクトシートの事実の配列 |
| `factCheckLog` | array | | 事実チェックの記録（`references/factsheet.md`） |

## meta

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | 教材ID。英小文字・数字・ハイフン。例 `k8s-practical-20261005`。保存キー `study-kit:{id}` に使うので、作り直しても変えない |
| `series` | string | | 上部バーで教材名の上に小さく出す文字（シリーズ名など） |
| `title` | string | ○ | 教材名 |
| `purpose` | string | ○ | `資格`／`実務`／`教養` |
| `goals` | string[] | ○ | 「〜できる」形式のゴール |
| `level` | string | | ヒアリングした現在の知識レベル |
| `targetVersion` | string | | 対象バージョン |
| `createdAt` | string | | 作成日 `YYYY-MM-DD` |
| `exam` | object\|null | | 資格トピックのときだけ。`questionCount`（整数）、`minutes`（整数）、`passingRate`（1〜100、任意） |

## chapters[]

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | `ch1`、`ch2` … |
| `title` | string | ○ | 章のタイトル。**番号は書かない**（「第1章」は学習エンジンが付ける）。例「Kubernetes の基本オブジェクト」 |
| `sections` | array | ○ | 節の配列 |
| `exercise` | array | ○ | 章末演習の問題（10問以上。下の「問題」） |

## sections[]

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | `ch1-s1` のように章IDを前に付ける |
| `title` | string | ○ | 節のタイトル。**番号は書かない**（「1-2」は学習エンジンが付ける）。例「Deployment と ReplicaSet」 |
| `items` | array | ○ | 項目の配列（3〜6個）。下の「items[]」 |
| `keyPoints` | string[] | ○ | この節の要点（2〜6個）。節のページの「まとめ」のページに出る。インラインのタグ（`<code>` など）だけ使える |
| `sources` | string[] | ○ | 根拠にした事実ID。節のページの「参考出典」に出る |
| `prerequisites` | string[] | | 前提になる節のID。節の見出しの下に「前提：1-1 Pod」と出る |
| `minutes` | integer | | 読了目安（分）。省略すると本文の文字数から見積もる |

## items[]（項目）

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | 節の中で一意。`i1`、`i2` … |
| `type` | string | | `text`（説明。省略時）／`example`（例題） |
| `title` | string | ○ | `text`：項目の見出し（「1. 」の番号は学習エンジンが付ける）。`example`：例題の問題文 |
| `body` | string | ○ | `text`：説明の本文。`example`：例題の解き方（`sk-steps` で書く）。HTML 断片（下の「本文の書き方」） |
| `check` | object | ○ | すぐ確認の問題（下の「問題」）。`refs` は不要（置かれた項目が教科書の該当箇所になる） |

- 1節は `text` の項目2〜5個と、必要なら最後に `example` を1個。例題の後ろのすぐ確認は「類題」として出る
- 1つの項目で説明するのは1つの事柄にする。すぐ確認が「その項目を読めば解ける1問」になるように区切る
- 項目の見出し・本文で、初めて出てくる固有名詞には `sk-premise` を先に置く（`references/proper-nouns.md`）。見出しは本文より先に表示されるので、見出しに初出の固有名詞を入れない

### 本文（body）の書き方

- **説明の項目には、図や表の部品を1つ以上入れる**（`validate.py` が警告する）。図解と丁寧な説明が基本。部品は `references/textbook-components.md`（`sk-` で始まるクラス）
- 使ってよいタグ：`<p>` `<h3>` `<h4>` `<ul>` `<ol>` `<li>` `<table>` 一式 `<pre><code>` `<code>` `<strong>` `<a href="…">` `<dl>` `<dt>` `<dd>` `<br>` `<div>` `<span>` `<figure>` `<figcaption>` と、`sk-figure` の中のインライン `<svg>`
- `<script>` `<style>` `<iframe>`、`on〜` 属性、外部URLの画像は使えない（`validate.py` がエラーにする）
- 地の文は属性なしの `<p>` に書く。`extract_prose.py` は `<p>` だけを表現の改修の対象として抜き出す
- `<p>` の中で使うインラインのタグは `<code>` `<strong>` `<a href="…">` だけにする。ほかのタグが入った段落は改修の対象外になる
- 本文の `<strong>` は蛍光ペンの線で表示される。その項目で覚えてほしい語だけに使う
- 表のセル・リスト・用語定義（`<dl>`）の中には `<p>` を使わない（`sk-steps` の手順の中は例外）
- `<`、`>`、`&` を文字として出すときは `&lt;` `&gt;` `&amp;` と書く
- 項目の見出しが `h2` で出るので、本文の中は `h3` から使う
- 外部の画像・スクリプト・スタイルは読み込まない

## 問題（check・exercise[]・finalExam[] 共通）

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | すぐ確認は `q-ch1-s1-01`、章末演習は `q-ch1-ex-01`、総合演習は `q-final-01` |
| `type` | string | ○ | `choice`／`truefalse`／`fill`／`order`／`predict` |
| `prompt` | string | ○ | 問題文（HTML 断片。インラインのタグだけ）。`truefalse` は判定させる文だけを書く（「正しければ○、誤りなら×」は学習エンジンが付ける） |
| `code` | string\|null | | 問題文の下に整形済みで出すコード・コマンド・出力（プレーンテキスト）。`predict` では必須 |
| `options` | string[] | 形式による | 選択肢・並べ替え項目（プレーンテキスト。タグは使えない） |
| `answer` | 形式による | ○ | 下の表 |
| `explanation` | string | ○ | 解説（HTML 断片。インラインのタグ `<code>` `<strong>` `<a>` だけ。段落に分けない） |
| `optionNotes` | (string|null)[] | | choice・predict だけ。`options` と同じ長さで、誤った選択肢ごとの解説（正解の位置は `null`）。その選択肢を選んで間違えたときに出る |
| `hint` | string | | 現在の学習エンジンでは表示しない。書かなくてよい |
| `unit` | string | | `fill` だけ。入力欄の後ろに出す単位（例「通り」「バイト」） |
| `refs` | string[] | 章末演習・総合演習で○ | 教科書の該当箇所。節ID（`ch1-s2`）か、項目まで指す `ch1-s2#i3`。演習の「教科書で確認する」に使う。項目まで指すほうがよい。総合演習では2章分以上を入れる |

### 形式ごとの options と answer

| type | options | answer |
|---|---|---|
| `choice` | 選択肢（2〜8つ、重複なし。基本は4つ） | 正解の選択肢のインデックス（0始まり） |
| `predict` | 出力の候補（2〜8つ、重複なし） | 正解の候補のインデックス（0始まり） |
| `truefalse` | 使わない（`[]`） | `true`（○）か `false`（×） |
| `fill` | 使わない（`[]`） | 許容表記の配列。判定時に全角半角・大文字小文字・空白の違いを無視する |
| `order` | 項目（3つ以上、重複なし）。この順で初回に表示するので、正解と同じ順にしない | `options` と同じ項目を正しい順に並べた配列 |

- 解き直し・2回目以降の出題では、選択肢と並べ替え項目の順番を学習エンジンがシャッフルする。「上のすべて」「AとB」のように位置に依存する選択肢は作らない
- 選択肢の記号（ア・イ・ウ・エ）は学習エンジンが付ける。選択肢の文に記号を書かない
- 選択式は、問題文だけを3秒見せてから選択肢を出す（`references/learning-engine.md`）。問題文だけで答えが1つに決まるように書く
- `fill` の `answer` には、半角の英数字で打てる表記を必ず1つ入れる（例：`["ReplicaSet", "レプリカセット"]`）。日本語でしか答えられない語は、選択式にする

## factsheet[]

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | `F-001` … |
| `claim` | string | ○ | 主張（1行） |
| `url` | string | ○ | 出典URL |
| `rank` | string | ○ | `S`／`A`／`B` |
| `backedBy` | string[] | B のとき○ | 裏付けにした rank S の事実ID |
