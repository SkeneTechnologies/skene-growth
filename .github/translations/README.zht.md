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


Skene 是一個面向產品驅動成長的程式碼庫分析工具包。它掃描您的程式碼庫，偵測成長機會，並產生可執行的實施計畫。

## 快速開始

安裝並啟動互動式終端介面：

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

精靈將引導您完成提供商選擇、身份驗證和分析——無需預先設定。

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## 功能介紹

- **技術堆疊偵測** -- 辨識框架、資料庫、身份驗證、部署
- **成長功能探索** -- 尋找現有的註冊流程、分享、邀請、帳務
- **功能登錄檔** -- 跨分析執行追蹤功能，將其與成長迴圈關聯
- **營收流失分析** -- 發現缺失的變現手段和薄弱的定價層級
- **成長計畫產生** -- 產生帶有實施路線圖的優先成長迴圈
- **實施提示詞** -- 為 Cursor、Claude 或其他 AI 工具建構即用型提示詞
- **遙測部署** -- 產生 Supabase 遷移並推送到上游
- **迴圈驗證** -- 驗證成長迴圈需求已被實施
- **互動式聊天** -- 在終端中就您的程式碼庫提問

支援 OpenAI、Gemini、Claude、LM Studio、Ollama 以及任何相容 OpenAI 的端點。提供免費的本機稽核，無需 API 金鑰。

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## 安裝

### 終端介面（建議）

TUI 是一個互動式精靈，引導您完成整個工作流程。無需先決條件——安裝程式會處理一切。

```bash
# 安裝 TUI
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# 啟動
skene
```

### Python CLI

如果您偏好命令列，可以使用 `uvx` 直接執行 Skene（無需安裝）或全域安裝：

```bash
# 安裝 uv（如果您還沒有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 直接執行（無需安裝）
uvx skene

# 或全域安裝
pip install skene
```

有關 CLI 使用詳情，請參閱[文件](https://www.skene.ai/resources/docs/skene)。

## Monorepo 結構

| 目錄 | 說明 | 語言 | 發佈 |
|-----------|-------------|----------|-------------|
| `src/skene/` | CLI + 分析引擎 | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | 互動式終端介面精靈 | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | Cursor IDE 外掛 | — | — |

TUI（`tui/`）是一個 Bubble Tea 應用程式，提供互動式精靈體驗，並透過 `uvx` 協調 Python CLI。每個套件都有獨立的 CI/CD 管線。

## 貢獻

歡迎貢獻。請[建立 issue](https://github.com/SkeneTechnologies/skene/issues) 或提交 [pull request](https://github.com/SkeneTechnologies/skene/pulls)。

## 授權條款

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
