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


Skene 是一个面向产品驱动增长的代码库分析工具包。它扫描您的代码库，检测增长机会，并生成可执行的实施计划。

## 快速开始

安装并启动交互式终端界面：

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

向导将引导您完成提供商选择、身份验证和分析——无需预先配置。

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## 功能介绍

- **技术栈检测** -- 识别框架、数据库、身份验证、部署
- **增长功能发现** -- 查找现有的注册流程、分享、邀请、计费
- **功能注册表** -- 跨分析运行跟踪功能，将其与增长循环关联
- **收入泄漏分析** -- 发现缺失的变现手段和薄弱的定价层级
- **增长计划生成** -- 生成带有实施路线图的优先级增长循环
- **实施提示词** -- 为 Cursor、Claude 或其他 AI 工具构建即用型提示词
- **遥测部署** -- 生成 Supabase 迁移并推送到上游
- **循环验证** -- 验证增长循环需求已被实施
- **交互式聊天** -- 在终端中就您的代码库提问

支持 OpenAI、Gemini、Claude、LM Studio、Ollama 以及任何兼容 OpenAI 的端点。提供免费的本地审计，无需 API 密钥。

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## 安装

### 终端界面（推荐）

TUI 是一个交互式向导，引导您完成整个工作流程。无需前置条件——安装程序会处理一切。

```bash
# 安装 TUI
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# 启动
skene
```

### Python CLI

如果您更喜欢命令行，可以使用 `uvx` 直接运行 Skene（无需安装）或全局安装：

```bash
# 安装 uv（如果您还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 直接运行（无需安装）
uvx skene

# 或全局安装
pip install skene
```

有关 CLI 使用详情，请参阅[文档](https://www.skene.ai/resources/docs/skene)。

## Monorepo 结构

| 目录 | 描述 | 语言 | 分发 |
|-----------|-------------|----------|-------------|
| `src/skene/` | CLI + 分析引擎 | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | 交互式终端界面向导 | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | Cursor IDE 插件 | — | — |

TUI（`tui/`）是一个 Bubble Tea 应用程序，提供交互式向导体验，并通过 `uvx` 编排 Python CLI。每个包都有独立的 CI/CD 流水线。

## 贡献

欢迎贡献。请[创建 issue](https://github.com/SkeneTechnologies/skene/issues) 或提交 [pull request](https://github.com/SkeneTechnologies/skene/pulls)。

## 许可证

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
