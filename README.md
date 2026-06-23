# NobelEngine — クラシック判事＆同人誌製作・ナラティブ設計スイート

[![Deploy to GitHub Pages](https://github.com/kaitas/CAIL26/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/kaitas/CAIL26/actions/workflows/deploy-pages.yml)

プレイヤーの「知らない（Unknown）」という認知状態を、ゲーム内の「探求」「検証」を経て「到達（Resolution）」へ深化させる体験設計（Narrativeデザイン）を検証する、**ビルド不要の単一HTMLゲームエンジン兼シミュレーター**です。中学生が同人誌製作で直面するリアルな諸問題（トンボ／予算計算／奥付義務／国会図書館納本／税務）を、体験の深度に比例してタスクが急増する「タスク雪崩（Task Avalanche）」として可視化します。

## 🚀 公開URL（GitHub Pages）

- **エンジン本体**: https://kaitas.github.io/CAIL26/
- **開発・拡張ポータル**: https://kaitas.github.io/CAIL26/nobelengine_agents_portal.html

> `main` への push で GitHub Actions が **検証（CI）→ 自動デプロイ（CD）** を実行します（`.github/workflows/deploy-pages.yml`）。

## 🔄 CI/CD パイプライン

ビルド工程はありませんが、AGENTS.md のガードレールを機械検証する CI ゲートを通してからデプロイします。

| トリガー | 実行内容 | ワークフロー |
|---|---|---|
| Pull Request / `main` 以外への push | **検証のみ**（マージ前チェック） | `.github/workflows/ci.yml` |
| `main` への push / 手動実行 | **検証（CI）→ Pages デプロイ（CD）**（検証失敗時はデプロイしない） | `.github/workflows/deploy-pages.yml` |

検証スクリプト `scripts/validate.mjs`（依存ゼロ）の検査項目:

1. 必須ファイルの存在（`index.html` / ポータル / `AGENTS.md` 等）
2. **単一ファイル原則** — ローカル相対の `src`/`href` を禁止（外部CDN https のみ許可）
3. **主要関数の存在** — `applyCustomThemeColor()` などガードレール対象を含む
4. **多言語整合** — `details ⇔ detailsZh`、`panic ⇔ pressure` の件数一致
5. HTML 基本健全性（`<html>`/`<body>` 対応・非空）

ローカルでも同じ検証を実行できます（CI と同一）:

```bash
npm run validate   # = node scripts/validate.mjs
```

## 📁 構成

| ファイル | 役割 |
|---|---|
| `index.html` | エンジン本体。左：プレイアブルゲーム / 右：開発者監査スイート（5タブ）を**単一ファイル**に同梱 |
| `nobelengine_agents_portal.html` | 開発・拡張ポータル（Chart.js でタスク雪崩・ロードマップを可視化） |
| `AGENTS.md` | 開発・拡張ガイドライン（設計書＋ロードマップ＋ガードレール） |
| `Skill.md` | **学生をゲーム完成まで導く手順書**（日中対訳）。エージェントがこの順で支援 |
| `scripts/validate.mjs` | CI 検証スクリプト（依存ゼロ）。ガードレールを機械検査 |
| `scripts/gen_samples.py` | GPT-Image-2 サンプル画像ジェネレータ → `assets/samples/`（スマホ最適化JPEG） |
| `assets/samples/` | キャラ立ち絵・表紙・エンディング・タイトルのサンプル画像（差し替え前提） |
| `package.json` | ローカル用スクリプトランナー（`npm run validate` 等。**ビルドなし・依存なし**） |

## ✨ 主要機能

- **ナラティブ・フラグ・トラッカー** — 証拠・課題のクリックで認知レベルが 0（知らない）→4（仮説検証）へ深化
- **Magic ToDo & Task Avalanche** — タスク細分化で想定時間が爆発（20h→1200h）し、心理集中度が「不安」へシフト
- **獲得型製本用語辞書** — トンボ／オンデマンド／ノド／PP加工／RGB-CMYK／奥付などが「未理解🔒」→「理解済✨」にアンロック
- **動的カラーテーマ** — CSS Variables ＋カラーピッカーで全体配色をリアルタイム再描画（`applyCustomThemeColor()`）
- **エクスポートエンジン** — シナリオJSONと、単体動作する「スタンドアロン再生機HTML」を動的ビルドしてダウンロード
- **多言語対応（日本語 / 中文）** — UI・ナラティブ・台詞・**辞書・ToDoテキストまで** ja/zh 整合

## 🛠 ローカルでの起動

ビルド不要。`index.html` をブラウザで開くだけです（外部CDN: Tailwind / Lucide / Google Fonts を取得するためネット接続を推奨）。

```bash
open index.html        # macOS
# または任意の静的サーバ
python3 -m http.server 8000   # → http://localhost:8000/
```

## 🧭 開発ガードレール（`AGENTS.md` 準拠）

1. **単一ファイルを維持**（HTML/CSS/JS をインライン結合した状態）
2. 動的テーマ反映の `applyCustomThemeColor()` を破壊しない
3. 多言語（ja/zh）の翻訳を、辞書・ToDoテキストを含めて整合させる
