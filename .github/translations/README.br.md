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


Skene é um kit de ferramentas de análise de código para crescimento liderado pelo produto. Ele escaneia sua base de código, detecta oportunidades de crescimento e gera planos de implementação acionáveis.

## Início Rápido

Instale e inicie a interface de terminal interativa:

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

O assistente guia você pela seleção do provedor, autenticação e análise — nenhuma configuração prévia necessária.

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## O Que Ele Faz

- **Detecção de stack tecnológico** -- identifica frameworks, bancos de dados, autenticação, implantação
- **Descoberta de funcionalidades de crescimento** -- encontra fluxos de cadastro existentes, compartilhamento, convites, faturamento
- **Registro de funcionalidades** -- rastreia funcionalidades entre execuções de análise, vincula-as a loops de crescimento
- **Análise de vazamento de receita** -- identifica monetização ausente e faixas de preço fracas
- **Geração de plano de crescimento** -- produz loops de crescimento priorizados com roteiros de implementação
- **Prompts de implementação** -- cria prompts prontos para uso no Cursor, Claude ou outras ferramentas de IA
- **Implantação de telemetria** -- gera migrações Supabase e envia para o upstream
- **Validação de loops** -- verifica se os requisitos do loop de crescimento foram implementados
- **Chat interativo** -- faça perguntas sobre sua base de código no terminal

Suporta OpenAI, Gemini, Claude, LM Studio, Ollama e qualquer endpoint compatível com OpenAI. Auditoria local gratuita disponível sem necessidade de chave de API.

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## Instalação

### Interface de Terminal (recomendado)

A TUI é um assistente interativo que guia você por todo o fluxo de trabalho. Sem pré-requisitos — o instalador cuida de tudo.

```bash
# Instalar a TUI
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# Iniciar
skene
```

### Python CLI

Se você prefere a linha de comando, pode executar o Skene diretamente com `uvx` (sem necessidade de instalação) ou instalá-lo globalmente:

```bash
# Instalar uv (se você não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Executar diretamente (sem necessidade de instalação)
uvx skene

# Ou instalar globalmente
pip install skene
```

Para detalhes de uso do CLI, consulte a [documentação](https://www.skene.ai/resources/docs/skene).

## Estrutura do Monorepo

| Diretório | Descrição | Linguagem | Distribuição |
|-----------|-------------|----------|-------------|
| `src/skene/` | CLI + motor de análise | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | Assistente interativo de terminal | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | Plugin para Cursor IDE | — | — |

A TUI (`tui/`) é um aplicativo Bubble Tea que fornece uma experiência de assistente interativo e orquestra o Python CLI via `uvx`. Cada pacote possui pipelines de CI/CD independentes.

## Contribuindo

Contribuições são bem-vindas. Por favor, [abra uma issue](https://github.com/SkeneTechnologies/skene/issues) ou envie um [pull request](https://github.com/SkeneTechnologies/skene/pulls).

## Licença

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
