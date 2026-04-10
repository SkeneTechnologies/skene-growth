<p align="center">
  <a href="../../README.md">English</a> |
  <a href="README.zh.md">简体中文</a> |
  <a href="README.zht.md">繁體中文</a> |
  <a href="README.ko.md">한국어</a> |
  <a href="README.de.md">Deutsch</a> |
  <a href="README.es.md">Español</a> |
  <a href="README.fr.md">Français</a> |
  <a href="README.it.md">Italiano</a> |
  <a href="README.da.md">Dansk</a> |
  <a href="README.ja.md">日本語</a> |
  <a href="README.pl.md">Polski</a> |
  <a href="README.ru.md">Русский</a> |
  <a href="README.bs.md">Bosanski</a> |
  <a href="README.ar.md">العربية</a> |
  <a href="README.no.md">Norsk</a> |
  <a href="README.br.md">Português (Brasil)</a> |
  <a href="README.th.md">ไทย</a> |
  <a href="README.tr.md">Türkçe</a> |
  <a href="README.uk.md">Українська</a> |
  <a href="README.bn.md">বাংলা</a> |
  <a href="README.gr.md">Ελληνικά</a> |
  <a href="README.vi.md">Tiếng Việt</a> |
  <a href="README.fi.md">Suomi</a> |
  <a href="README.sv.md">Svenska</a>
</p>

<p align="center">
  <img width="4000" height="800" alt="Skene_git" src="https://github.com/user-attachments/assets/2be11c04-6b98-4e26-8905-bf3250c4addb" />
  <a href="https://www.skene.ai"><img width="120" height="42" alt="website" src="https://github.com/user-attachments/assets/8ae8c68f-eeb5-411f-832f-6b6818bd2c34"></a>
  <a href="https://www.skene.ai/resources/docs/skene"><img width="120" height="42" alt="docs" src="https://github.com/user-attachments/assets/f847af52-0f6f-4570-9a48-1b7c8f4f0d7a"></a>
  <a href="https://www.skene.ai/resources/blog"><img width="100" height="42" alt="blog" src="https://github.com/user-attachments/assets/8c62e3b8-39a8-43f6-bb0b-f00b118aff82"></a>
  <a href="https://www.reddit.com/r/plgbuilders/"><img width="153" height="42" alt="reddit" src="https://github.com/user-attachments/assets/b420ea50-26e3-40fe-ab34-ac179f748357"></a>
</p>


Skeneは、プロダクト主導型グロースのためのコードベース分析ツールキットです。コードベースをスキャンし、成長機会を検出し、実行可能な実装プランを生成します。

## クイックスタート

インタラクティブなターミナルUIをインストールして起動します：

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

ウィザードがプロバイダーの選択、認証、分析をガイドします — 事前の設定は不要です。

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## 機能紹介

- **技術スタック検出** -- フレームワーク、データベース、認証、デプロイメントを特定
- **グロース機能の発見** -- 既存のサインアップフロー、共有、招待、課金を検出
- **機能レジストリ** -- 分析実行全体にわたって機能を追跡し、グロースループに紐付け
- **収益漏れ分析** -- 欠落しているマネタイズや弱い価格帯を特定
- **グロースプラン生成** -- 優先順位付けされたグロースループと実装ロードマップを作成
- **実装プロンプト** -- Cursor、Claude、その他のAIツール向けのすぐに使えるプロンプトを構築
- **テレメトリデプロイ** -- Supabaseマイグレーションを生成し、アップストリームにプッシュ
- **ループ検証** -- グロースループの要件が実装されているかを検証
- **インタラクティブチャット** -- ターミナルでコードベースについて質問

OpenAI、Gemini、Claude、LM Studio、Ollama、およびOpenAI互換のエンドポイントをサポート。APIキー不要の無料ローカル監査が利用可能です。

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## インストール

### ターミナルUI（推奨）

TUIは、ワークフロー全体をガイドするインタラクティブなウィザードです。前提条件なし — インストーラーがすべて処理します。

```bash
# TUIをインストール
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# 起動
skene
```

### Python CLI

コマンドラインを好む場合は、`uvx`で直接Skeneを実行できます（インストール不要）。またはグローバルにインストールできます：

```bash
# uvをインストール（未導入の場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 直接実行（インストール不要）
uvx skene

# またはグローバルインストール
pip install skene
```

CLIの使用方法の詳細については、[ドキュメント](https://www.skene.ai/resources/docs/skene)を参照してください。

## モノレポ構成

| ディレクトリ | 説明 | 言語 | 配布 |
|-------------|------|------|------|
| `src/skene/` | CLI + 分析エンジン | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | インタラクティブターミナルUIウィザード | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | Cursor IDEプラグイン | — | — |

TUI（`tui/`）は、インタラクティブなウィザード体験を提供し、`uvx`を介してPython CLIをオーケストレーションするBubble Teaアプリです。各パッケージは独立したCI/CDパイプラインを持っています。

## コントリビューション

コントリビューションを歓迎します。[issueを開く](https://github.com/SkeneTechnologies/skene/issues)か、[pull request](https://github.com/SkeneTechnologies/skene/pulls)を送信してください。

## ライセンス

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
