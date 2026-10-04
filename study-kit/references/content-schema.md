# 教材データ（JSON）のスキーマ

`validate.py` がこの定義に沿って検査する。完全な例（お手本）は `examples/k8s-practical/content.json` にある。トピックが変わっても、この構造と部品の使い方を踏襲する。お手本の事実は未検証のサンプルなので、内容は流用しない。

## トップレベル

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `meta` | object | ○ | 教材の情報 |
| `chapters` | array | ○ | 章の配列（並び順＝学習順） |
| `finalExam` | array | ○ | 総合演習の問題の配列 |
| `factsheet` | array | ○ | ファクトシートの事実の配列 |
| `factCheckLog` | array | | 事実チェックの記録（`references/factsheet.md`） |

## meta

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | 教材ID。英小文字・数字・ハイフン。例 `k8s-practical-20261005`。保存キー `study-kit:{id}` に使うので、作り直しても変えない |
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
| `title` | string | ○ | 章のタイトル（例「1章 Kubernetes の基本オブジェクト」） |
| `sections` | array | ○ | 節の配列 |

## sections[]

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | `ch1-s1` のように章IDを前に付ける |
| `title` | string | ○ | 節のタイトル（例「1.1 Pod」） |
| `body` | string | ○ | 教科書本文（HTML 断片。下の「本文の書き方」） |
| `sources` | string[] | ○ | 根拠にした事実ID。教科書の「参考出典」に出る |
| `questions` | array | ○ | この節の問題（6〜10問） |

### 本文（body）の書き方

- 図や囲みは `references/textbook-components.md` の部品（`sk-` で始まるクラス）で書く
- 使ってよいタグ：`<p>` `<h3>` `<h4>` `<ul>` `<ol>` `<li>` `<table>` 一式 `<pre><code>` `<code>` `<strong>` `<a href="…">` `<dl>` `<dt>` `<dd>` `<br>` `<div>` `<span>` `<figure>` `<figcaption>` と、`sk-figure` の中のインライン `<svg>`
- `<script>` `<style>` `<iframe>`、`on〜` 属性、外部URLの画像は使えない（`validate.py` がエラーにする）
- 地の文は属性なしの `<p>` に書く。`extract_prose.py` は `<p>` だけを表現の改修の対象として抜き出す
- `<p>` の中で使うインラインのタグは `<code>` `<strong>` `<a href="…">` だけにする。ほかのタグが入った段落は改修の対象外になる
- 表のセル・リスト・用語定義（`<dl>`）の中には `<p>` を使わない
- `<`、`>`、`&` を文字として出すときは `&lt;` `&gt;` `&amp;` と書く
- 見出しは節タイトルが `h2` で出るので、本文の中は `h3` から使う
- 外部の画像・スクリプト・スタイルは読み込まない

## 問題（questions[] と finalExam[] 共通）

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | 節の問題は `q-ch1-s1-01`、総合演習は `q-final-01` |
| `type` | string | ○ | `choice`／`fill`／`order`／`predict` |
| `prompt` | string | ○ | 問題文（HTML 断片。インラインのタグだけ） |
| `code` | string\|null | | 問題文の下に整形済みで出すコード・コマンド・出力（プレーンテキスト）。`predict` では必須 |
| `options` | string[] | 形式による | 選択肢・並べ替え項目（プレーンテキスト。タグは使えない） |
| `answer` | 形式による | ○ | 下の表 |
| `explanation` | string | ○ | 解説（HTML 断片。インラインのタグ `<code>` `<strong>` `<a>` だけ。段落に分けない） |
| `refs` | string[] | ○ | 教科書の該当節ID。誤答時のリンクに使う。総合演習では関係する章の節を2章分以上入れる |

### 形式ごとの options と answer

| type | options | answer |
|---|---|---|
| `choice` | 選択肢（2つ以上、重複なし） | 正解の選択肢のインデックス（0始まり） |
| `predict` | 出力の候補（2つ以上、重複なし） | 正解の候補のインデックス（0始まり） |
| `fill` | 使わない（`[]`） | 許容表記の配列。判定時に全角半角・大文字小文字・空白の違いを無視する |
| `order` | 項目（3つ以上、重複なし）。この順で初回に表示するので、正解と同じ順にしない | `options` と同じ項目を正しい順に並べた配列 |

- 2回目以降の出題では、選択肢と並べ替え項目の順番を学習エンジンがシャッフルする。「上のすべて」「AとB」のように位置に依存する選択肢は作らない
- 「不明」ボタンは学習エンジンが自動で付ける。選択肢に「分からない」は入れない

## factsheet[]

| キー | 型 | 必須 | 内容 |
|---|---|---|---|
| `id` | string | ○ | `F-001` … |
| `claim` | string | ○ | 主張（1行） |
| `url` | string | ○ | 出典URL |
| `rank` | string | ○ | `S`／`A`／`B` |
| `backedBy` | string[] | B のとき○ | 裏付けにした rank S の事実ID |
