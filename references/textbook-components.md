# 教科書の部品（body で使うオブジェクト）

教科書は文章だけで書かない。各節で、内容に合う部品を選んで「見て分かる」形にする。
部品の見た目（色・アイコン・ダークモード）は template.html が持っているので、body には下の HTML とクラス名だけを書く。

## 1節の組み立て（目安）

1. `sk-goals`：この節でわかること（必ず先頭に置く）
2. `sk-premise`：この節で初めて出てくる固有名詞の前提の説明（`references/proper-nouns.md`。初出の位置より前に置く）
3. 導入の地の文（`<p>`）
4. 中心になる図を1つ以上：`sk-nest`（入れ子・包含）、`sk-flow`（手順・流れ）、`sk-compare`（比較）、`sk-figure`（自由な図）のどれか
5. 必要に応じて `sk-callout`（たとえ・ポイント・注意・実務メモ）、`sk-terms`（用語）、`sk-badge-list`（状態の一覧）、表、コード
6. `sk-summary`：まとめ（必ず最後に置く）

部品を使うのは理解を助けるときだけ。飾りのために置かない。1節に同じ部品を何度も並べない（`sk-premise` は固有名詞の数だけ並べてよい）。

## 部品カタログ

### sk-goals：この節でわかること

```html
<div class="sk-goals"><ul><li>Pod とコンテナの関係</li><li>Pod を直接作らない理由</li></ul></div>
```

### sk-premise：固有名詞の前提の説明

固有名詞が教材で初めて出てくる節に、1語につき1つ置く。見出し「📘 前提：〇〇 とは」は `data-term` から自動で付く。書き方のルールは `references/proper-nouns.md`。

```html
<div class="sk-premise" data-term="Kubernetes">
  <p><strong>何か：</strong>コンテナで動くアプリの配置・起動・増減・復旧を自動で行う、オープンソースのソフトウェアです。読み方は「クバネティス」などで、K8s と略されます。</p>
  <p><strong>誰が作ったか：</strong>Google が社内の経験をもとに開発し、2014年にオープンソースとして公開しました。現在は CNCF という団体が管理しています。</p>
  <p><strong>なぜ必要か：</strong>コンテナが数十・数百に増えると、どのサーバーで動かすか、落ちたら誰が起動し直すかを人手で管理しきれなくなります。それを自動化するために使います。</p>
  <p><strong>この教材との関係：</strong>この教材全体の主役です。以降の節で出てくる Pod や Deployment は、すべて Kubernetes の中の仕組みです。</p>
</div>
```

- `data-term` には本文に出てくる表記そのものを書く（`validate.py` が初出の位置を調べるのに使う）
- 中は `<p>` で書き、4つの観点（何か／誰が作ったか／なぜ必要か／この教材との関係）を `<strong>` の見出しで始める。見出しは表現の改修でも消さない
- 説明の中に別の固有名詞が出てきたら、その語にも `sk-premise` を置く（上の例なら CNCF）

### sk-callout：囲み（4種類）

| クラス | 見出し | 使いどころ |
|---|---|---|
| `point` | ポイント | 覚えてほしい要点 |
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

### sk-figure：自由な図（インライン SVG）

上の部品で表せない図（時間の変化、グラフ、位置関係）は SVG で描く。

```html
<figure class="sk-figure">
  <svg viewBox="0 0 600 200" role="img" aria-label="図の説明">
    <rect x="20" y="40" width="120" height="60" rx="12" class="sk-fill-primary"/>
    <text x="80" y="76" text-anchor="middle" class="sk-text-on">v1</text>
  </svg>
  <figcaption>図の説明（1行）</figcaption>
</figure>
```

- 色は直接書かず、クラスで指定する（ダークモードで色が変わるため）

| クラス | 用途 |
|---|---|
| `sk-fill-primary` / `sk-fill-primary-soft` | 主役（紫）とその薄い色 |
| `sk-fill-accent` / `sk-fill-accent-soft` | 2番目の要素（緑）とその薄い色 |
| `sk-fill-warn` | 異常・エラー（赤） |
| `sk-fill-muted` / `sk-fill-surface` | 背景・枠の中 |
| `sk-stroke` / `sk-stroke-primary` | 線（`fill="none"` と組み合わせる） |
| `sk-text` / `sk-text-muted` / `sk-text-on` | 文字（通常・薄い・色付きの図形の上） |

- `viewBox` を必ず付け、`width` / `height` は書かない（画面幅に合わせて縮む）
- 文字は 14〜16 の大きさで、図形からはみ出さないようにする
- 外部の画像やフォントは読み込まない。`<script>` や `on〜` 属性は書かない

### sk-summary：まとめ

```html
<div class="sk-summary"><ul><li>Pod は最小のデプロイ単位</li><li>Pod は Deployment に作らせる</li></ul></div>
```

## 書いてはいけないもの

- `<script>`、`<style>`、`<iframe>`、`on〜` 属性（`validate.py` がエラーにする）
- 外部URLの画像・音声・フォント（オフラインで動かなくなる）
- 部品のクラスに独自の色やサイズを `style` で上書きすること
