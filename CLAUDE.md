# study-kit の開発ルール

このリポジトリは Claude Code スキル `study-kit` そのもの（直下の `SKILL.md` がスキル本体）。
インストール先 `~/.claude/skills/study-kit` で直接改良し、commit・push する。

## 開発の進め方

- 設計 → 実装 → テストのハーネス（harness-design / harness-build / harness-test）は使わない。design.md は作らず、仕様の変更は `SKILL.md`・`references/`・`assets/template.html` を直接直す
- 学習エンジンの仕様は `references/learning-engine.md` が正。template.html を変えたら必ずこの文書も合わせる

## 横展開の原則

- `assets/template.html` はどのトピックでも共通。トピック名や固有の文言を書き込まない
- トピックごとに変わるのは、リサーチで集めた事実と、そこから作る教材JSONの中身だけ
- 見た目は `references/textbook-components.md` の部品で表す。部品が足りなければ、template.html と部品カタログの両方に追加する

## UI の方針（ユーザーの指示）

- ゲームっぽいデザイン。正解したらクラッカー（紙吹雪）を出す
- 上部バーは進捗率（クローズ済み ÷ 全問題）。レベルや XP は使わない
- 「学習を始める」ボタンで一方的に出題しない。学習者がステージマップから読みたい章・節を選ぶ
- 節のページは インプット → アウトプット の順（本文が先、問題は末尾）
- 問題ごとの状態を番号入りの丸で一目で分かるようにする：未挑戦＝灰、今すぐ解ける＝橙、待ち＝赤（止まれ）、クリア＝緑。待ちの問題には、いつから解けるかを出す
- セッションの時間設定は持たない
- 学習履歴の書き出し・読み込み・削除は、ホームに置かず右上の ⚙ 設定画面に入れる
- 1節の問題は6〜10問
- 教科書の目次は常に表示しない。左下の「☰ 目次」ボタンで左からスライドして出す（背景クリック・✕・Esc で閉じる）
- 横の余白を取りすぎない。本文の最大幅は 1600px（以前の 880px は広い画面で余白が多すぎた）
- 固有名詞は初出の節で必ず前提から説明する（`references/proper-nouns.md`、部品は `sk-premise`）。説明は少し多すぎるくらいでよい

## 動作確認

```
# お手本から教材HTMLを作り直す（Windows は py、それ以外は python3）
py scripts/build_html.py examples/k8s-practical/content.json -o examples/k8s-practical/k8s-practical-20261005.html --factsheet examples/k8s-practical/k8s-practical-20261005_factsheet.md
```

- できた HTML をブラウザで開いて確かめる。URL に `?today=YYYY-MM-DD` を付けると、その日付として動く（日をまたぐ再出題の確認用）
- template.html を直したら、`examples/` の教材HTMLも作り直してコミットする
