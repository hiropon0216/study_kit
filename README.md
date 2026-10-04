# study_kit

学習したいトピックから、教科書と問題集を学習エンジン付きの1ファイルのHTMLとして生成する Claude Code スキル（`study-kit`）。

このリポジトリの直下がそのままスキルのフォルダになっている。

## インストール（どのプロジェクトからでも使えるようにする）

ユーザー全体のスキルフォルダに clone する。

```
git clone https://github.com/hiropon0216/study_kit.git ~/.claude/skills/study-kit
```

スキルの改良は `~/.claude/skills/study-kit` の中で行い、そのまま commit・push する。

## 構成

| パス | 内容 |
|---|---|
| `SKILL.md` | スキルの手順（フェーズ0〜5） |
| `assets/template.html` | 全トピック共通のUI・学習エンジン・保存処理 |
| `references/` | ヒアリング・章立て・ファクトシート・スキーマ・問題の作り方・教科書の部品・レビュー観点・学習エンジンの仕様 |
| `scripts/` | 教材JSONの検査・HTMLへの埋め込み・地の文の抜き出しと書き戻し |
| `examples/k8s-practical/` | お手本の教材JSONと、そこから生成した教材HTML・ファクトシート（事実は未検証のサンプル） |

開発時の方針は `CLAUDE.md` にある。
