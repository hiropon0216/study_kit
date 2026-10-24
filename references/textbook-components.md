# 教科書の部品（項目の body で使うオブジェクト）

教科書は文章だけで書かない。**図解を多用し、説明は丁寧に** する。各項目で、内容に合う部品を選んで「見て分かる」形にする。
部品の見た目（色・アイコン。明るい地に太い黒枠の「アーケード」調）は template.html が持っているので、body には下の HTML とクラス名だけを書く。

## 1つの項目（items[]）の組み立て（目安）

節は「項目の説明 → すぐ確認」の繰り返しでできている（`references/content-schema.md`）。1つの説明の項目は次の順に組み立てる。

1. `sk-premise`：この項目で初めて出てくる固有名詞の前提の説明（`references/proper-nouns.md`。本文の先頭にまとめて置く。表示は段落末尾の用語チップになる）
2. 導入の地の文（`<p>`）。「なぜそうなるのか」から書く。結論だけを並べない
3. 中心になる図を1つ以上（**必須**）：`sk-figure`（自由な図・絵柄）、`sk-nest`（入れ子・包含）、`sk-flow`（手順・流れ）、`sk-compare`（比較）、`sk-cells`（並んだマス）、`sk-terms`（用語）、`sk-badge-list`（状態の一覧）、表のどれか
4. 図を読み解く地の文。図の中の具体的な値や名前を使って説明する
5. 必要に応じて `sk-callout`（たとえ・POINT・注意・実務メモ）、コード

例題の項目（`type: "example"`）は、`title` に問題文、`body` に `sk-steps` で解き方を書く。手順の中にも図（`sk-cells` など）を入れてよい。例題の直後の穴あき例題（`type: "faded"`）は、同じ書き方で、伏せる段を `<li class="sk-blank">` にする（下の `sk-steps`）。

### 原理は「具体 → 抽象」の順で説明する

規則・原理・仕組み（「〜のときは〜になる」）を説明する項目は、原理を先に書かない。次の順にする。

1. **具体的な場面を2つ並べる**：見た目は違うが、同じ原理で動いている場面を2つ（`sk-compare` で左右に並べるとよい）。値や名前は具体的に書く
2. **共通点を問いかける**：「2つに共通するのは何でしょうか」と地の文で投げかけ、図の中で共通する部分を `sk-fill-mark` などで目立たせる
3. **原理に名前を付ける**：共通点を一般的な言葉でまとめ、ここで初めて用語を出す（`<strong>`）
4. **当てはまらない場面に触れる**（必要なら）：似ているが原理が当てはまらない場面を `sk-callout warn` で1つ挙げる

具体的な場面は図で見せ、抽象的なまとめは文で書く。最初から抽象的な定義と記号だけで説明しない。

- 根拠：2つの事例を比べさせると、1つずつ学ぶより原理を抜き出しやすく、別の場面に使いやすい（Gentner, D., Loewenstein, J., & Thompson, L. (2003). Learning and transfer: A general role for analogical encoding. *Journal of Educational Psychology*, 95(2), 393–408）。具体から始めて、少しずつ抽象に移すと、両方の利点を得られる（Fyfe, E. R., McNeil, N. M., Son, J. Y., & Goldstone, R. L. (2014). Concreteness fading in mathematics and science instruction: A systematic review. *Educational Psychology Review*, 26(1), 9–25）。どちらも書誌と要旨を確認
- 用語の定義だけの項目（「Pod とは」）や、手順だけの項目には使わなくてよい

この節の要点は `keyPoints` に書く（右の列に出る）。本文に `sk-goals` や `sk-summary` を置く必要はない。

部品を使うのは理解を助けるときだけ。飾りのために置かない。1つの項目に同じ部品を何度も並べない（`sk-premise` は固有名詞の数だけ並べてよい）。

## 本文の重要語

`<p>` の中の `<strong>` は、蛍光ペンの線を引いた表示になる。その項目で覚えてほしい語（すぐ確認で問う語）にだけ使う。

一度正解した項目を開き直すと、本文の `<strong>` は伏せ字になり、学習者が思い出してから開く（`references/learning-engine.md`）。そのため：

- `<strong>` は思い出す価値のある語（用語・値・コマンド名など）だけを囲む。文や長い句を囲まない（1語〜10字程度）
- 前後の文から答えが分かってしまう語は囲まない（伏せても思い出す練習にならない）
- 「何か：」のように「：」で終わる見出し語、図・コード・`sk-premise` の中の `<strong>` は伏せない

## 部品カタログ

### sk-premise：固有名詞の前提の説明

固有名詞が教材で初めて出てくる項目に、1語につき1つ置く。書き方のルールは `references/proper-nouns.md`。

**本文には表示しない。** 学習エンジンが本文の流れから外し、その語が最初に出てくる段落（`p`・`li`・`dd`）の末尾に用語チップ（例：`? Kubernetes`）を置く。チップにカーソルを当てる（キーボードならフォーカス、タッチなら押す）と、この説明が「Kubernetes とは」の吹き出しで出る。前提の説明が本文の頭に並んで読みにくくなるのを防ぐため。項目の本文の先頭にまとめて書いてよい

```html
<div class="sk-premise" data-term="Kubernetes">
  <p><strong>何か：</strong>コンテナで動くアプリの配置・起動・増減・復旧を自動で行う、オープンソースのソフトウェアです。読み方は「クバネティス」などで、K8s と略されます。</p>
  <p><strong>誰が作ったか：</strong>Google が社内の経験をもとに開発し、2014年にオープンソースとして公開しました。現在は CNCF という団体が管理しています。</p>
  <p><strong>なぜ必要か：</strong>コンテナが数十・数百に増えると、どのサーバーで動かすか、落ちたら誰が起動し直すかを人手で管理しきれなくなります。それを自動化するために使います。</p>
  <p><strong>この教材との関係：</strong>この教材全体の主役です。以降の節で出てくる Pod や Deployment は、すべて Kubernetes の中の仕組みです。</p>
</div>
```

- `data-term` は必須。本文に出てくる表記そのものを書く（チップを置く段落を探すのと、`validate.py` が初出の位置を調べるのに使う）。「Kubernetes（K8s）」のように書いた場合は、括弧の前の「Kubernetes」でも探す
- 本文にその語が出てこない場合（前提の説明の中にだけ出てくる語など）は、項目の最初の段落にチップを置く
- 中は `<p>` で書き、4つの観点（何か／誰が作ったか／なぜ必要か／この教材との関係）を `<strong>` の見出しで始める。見出しは表現の改修でも消さない
- 説明の中に別の固有名詞が出てきたら、その語にも `sk-premise` を置く（上の例なら CNCF）

### sk-callout：囲み（4種類）

| クラス | 見出し | 使いどころ |
|---|---|---|
| `point` | POINT | 覚えてほしい要点・法則 |
| `warn` | 注意 | よくある誤解・はまりどころ |
| `analogy` | たとえると | 初学者向けのたとえ。たとえで事実を曲げない |
| `tip` | 実務メモ | 現場での使い方（目的が実務のとき） |

```html
<div class="sk-callout analogy"><p>Pod は「お弁当箱」、コンテナは「おかず」です。</p></div>
```

中の文章は `<p>` で書く（表現の改修の対象になる）。

### sk-nest：入れ子の図（包含・所属・階層）

「A の中に B がある」「A が B を管理する」を箱の入れ子で見せる。3段目までは色が変わる。

```html
<div class="sk-nest" data-label="Node（サーバー）">
  <div class="sk-nest" data-label="Pod">
    <span class="sk-item">コンテナ: web</span>
    <span class="sk-item">コンテナ: log</span>
    <p class="sk-caption">同じ Pod のコンテナは localhost で話せる</p>
  </div>
  <div class="sk-nest" data-label="Pod">
    <span class="sk-item">コンテナ: api</span>
  </div>
</div>
```

- `data-label` が箱の見出しになる
- 箱の中の要素は `sk-item`、補足は `p.sk-caption`（属性付きの `<p>` は表現の改修の対象外）

### sk-flow：手順・流れ（番号と矢印つきのカード）

```html
<ol class="sk-flow">
  <li><strong>get pods</strong><br>STATUS を見る</li>
  <li><strong>describe</strong><br>Events を読む</li>
  <li><strong>logs</strong><br>アプリのエラーを読む</li>
</ol>
```

並べ替え問題の元になる手順は、教科書ではこの部品で見せる。

### sk-compare：比較カード（2〜3列）

```html
<div class="sk-compare">
  <div><h4>Docker</h4><ul><li>コンテナを1つずつ起動</li></ul></div>
  <div><h4>Kubernetes</h4><ul><li>Pod にまとめて起動</li></ul></div>
</div>
```

1列目はグレー、2列目は紫、3列目は緑の帯が付く。「前に知っているもの → 今回学ぶもの」の順に並べる。

### sk-cells：並んだマス（ビット・配列・時系列など）

同じ種類のものが並ぶ様子を、マスの列で見せる。`data-label` を付けると、下に括弧と説明が付く。

```html
<div class="sk-cells" data-label="1バイト（8ビット）"><span>0</span><span>1</span><span>0</span><span>0</span><span>0</span><span>0</span><span>0</span><span>1</span></div>
```

- マスの中は短い文字（数字・記号・2〜4文字の語）
- 強調したいマスは `class="on"`（黄色）、過ぎたもの・まだないものは `class="dim"`（薄い点線）
- 例：`<span class="dim">1回目</span><span class="dim">2回目</span><span class="on">前回</span><span>いま</span>`

### sk-steps：解き方の手順（例題で使う）

例題の解き方を、番号付きの段で見せる。各段の中は `<p>` で書き、図を入れてもよい。

```html
<ol class="sk-steps">
  <li><p>1バイトは8ビットです。</p></li>
  <li><p>2バイトは、その8ビットのかたまりが2つです。</p></li>
  <li><p>バイト → ビットは「× 8」なので、2 × 8 ＝ <strong>16ビット</strong>。</p></li>
</ol>
```

`sk-flow`（横に並ぶ手順のカード）は「操作の流れ」、`sk-steps` は「考え方の順序」に使う。

**穴あき例題（`type: "faded"` の項目）では、伏せる段を `<li class="sk-blank">` にする。** 学習エンジンがその段を「？ この段を自分で考えてから、押して開く」に置き換え、学習者が考えてから開く。

```html
<ol class="sk-steps">
  <li><p>3バイトは、8ビットのかたまりが3つです。</p></li>
  <li class="sk-blank"><p>バイト → ビットは「× 8」なので、3 × 8 ＝ <strong>24ビット</strong>。</p></li>
</ol>
```

- 伏せるのは、直前の例題で見せた考え方を使う段。最初の段（問題の読み取り）は伏せない
- 最後の答えの段だけでなく、途中の考え方の段も伏せる。伏せるのは1〜2段にし、すべての段を伏せない
- `sk-blank` は穴あき例題の中でだけ伏せられる（`validate.py` が警告する）

### sk-terms：用語カード

```html
<dl class="sk-terms">
  <div><dt>Pod</dt><dd>1つ以上のコンテナをまとめた、最小のデプロイ単位</dd></div>
  <div><dt>Node</dt><dd>Pod が動くサーバー</dd></div>
</dl>
```

用語定義は表現の改修の対象外。

### sk-badge と sk-badge-list：状態・ステータス

```html
<div class="sk-badge-list">
  <div><span class="sk-badge ok">Running</span><span>コンテナが動いている</span></div>
  <div><span class="sk-badge err">CrashLoopBackOff</span><span>起動と異常終了を繰り返している</span></div>
</div>
```

色は `ok`（緑）・`warn`（橙）・`err`（赤）・`info`（青）。バッジは `<p>` の中に入れない（入れるとその段落が表現の改修の対象外になる）。

### sk-figure：自由な図・絵柄（インライン SVG）

上の部品で表せない図（時間の変化、グラフ、位置関係、繰り返し、ものの絵柄）は SVG で描く。説明の項目では、この部品で「絵」を描くのが最も伝わりやすい。

- `figcaption` は「図 1-2-1　〜」のように、節番号と通し番号を付ける。本文やヒントから「図 1-2-1 の…」と指せるようにする
- ランプ・箱・矢印など、身近なものの形にたとえて描いてよい（例：0 と 1 を消えたランプとついたランプで描く）

```html
<figure class="sk-figure">
  <svg viewBox="0 0 600 200" role="img" aria-label="図の説明">
    <rect x="20" y="40" width="120" height="60" rx="12" class="sk-fill-primary"/>
    <text x="80" y="76" text-anchor="middle" class="sk-text-on">v1</text>
  </svg>
  <figcaption>図の説明（1行）</figcaption>
</figure>
```

- 色は直接書かず、クラスで指定する（配色を変えたときに図の色もまとめて変わるようにするため）

| クラス | 用途 |
|---|---|
| `sk-fill-primary` / `sk-fill-primary-soft` | 主役（青紫）とその薄い色 |
| `sk-fill-accent` / `sk-fill-accent-soft` | 2番目の要素・正常（緑）とその薄い色 |
| `sk-fill-warn` / `sk-fill-warn-soft` | 異常・エラー（橙）とその薄い色 |
| `sk-fill-mark` / `sk-fill-mark-soft` | 目立たせたいもの・光っているもの（黄）と、その光（薄い黄） |
| `sk-fill-muted` / `sk-fill-surface` | 背景・枠の中（図の地より少し暗い／明るい） |
| `sk-stroke` / `sk-stroke-primary` / `sk-stroke-accent` / `sk-stroke-warn` / `sk-stroke-mark` | 線（`fill="none"` と組み合わせる） |
| `sk-text` / `sk-text-muted` | 文字（通常・薄い） |
| `sk-text-on` / `sk-text-dark` | 色付きの図形の上の文字（白／黄色の図形の上の黒） |
| `sk-text-primary` / `sk-text-accent` / `sk-text-warn` | 色付きの文字（強調・正常・異常） |

- `viewBox` を必ず付け、`width` / `height` は書かない（画面幅に合わせて縮む）
- 文字は 12〜16 の大きさで、図形からはみ出さないようにする
- 矢印は `<defs>` の `<marker>` で作り、中の `<path>` にも色のクラスを付ける。`id` は教材の中で重ならない名前にする（例 `ah-crash`）

  ```html
  <defs><marker id="ah-crash" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" class="sk-fill-primary"/></marker></defs>
  <path d="M172 65H220" stroke-width="2" fill="none" class="sk-stroke-primary" marker-end="url(#ah-crash)"/>
  ```
- 外部の画像やフォントは読み込まない。`<script>` や `on〜` 属性は書かない

### sk-goals・sk-summary：わかること・まとめ（任意）

節の要点は `keyPoints` で右の列に出るので、通常は使わない。項目の途中で区切りを付けたいときだけ使う。

```html
<div class="sk-goals"><ul><li>Pod とコンテナの関係</li></ul></div>
<div class="sk-summary"><ul><li>Pod は最小のデプロイ単位</li><li>Pod は Deployment に作らせる</li></ul></div>
```

## 書いてはいけないもの

- `<script>`、`<style>`、`<iframe>`、`on〜` 属性（`validate.py` がエラーにする）
- 外部URLの画像・音声・フォント（オフラインで動かなくなる）
- 部品のクラスに独自の色やサイズを `style` で上書きすること
