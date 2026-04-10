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


Skene는 제품 주도 성장을 위한 코드베이스 분석 툴킷입니다. 코드베이스를 스캔하고, 성장 기회를 감지하며, 실행 가능한 구현 계획을 생성합니다.

## 빠른 시작

대화형 터미널 UI를 설치하고 실행합니다:

```bash
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash
skene
```

마법사가 프로바이더 선택, 인증, 분석을 안내합니다 — 사전 설정이 필요 없습니다.

<p align="center">
  <img src="https://github.com/user-attachments/assets/49dcd0c4-2bad-4fd3-b29e-89ba2b85c669" width="100%" height="auto"/>
<p>

## 주요 기능

- **기술 스택 감지** -- 프레임워크, 데이터베이스, 인증, 배포를 식별
- **성장 기능 발견** -- 기존 가입 플로우, 공유, 초대, 결제를 탐지
- **기능 레지스트리** -- 분석 실행 전반에 걸쳐 기능을 추적하고 성장 루프에 연결
- **수익 누수 분석** -- 누락된 수익화 및 취약한 가격 등급을 발견
- **성장 계획 생성** -- 우선순위가 지정된 성장 루프와 구현 로드맵을 생성
- **구현 프롬프트** -- Cursor, Claude 또는 기타 AI 도구를 위한 바로 사용 가능한 프롬프트를 구축
- **텔레메트리 배포** -- Supabase 마이그레이션을 생성하고 업스트림으로 푸시
- **루프 검증** -- 성장 루프 요구사항이 구현되었는지 확인
- **대화형 채팅** -- 터미널에서 코드베이스에 대해 질문

OpenAI, Gemini, Claude, LM Studio, Ollama 및 모든 OpenAI 호환 엔드포인트를 지원합니다. API 키 없이 무료 로컬 감사를 사용할 수 있습니다.

<img width="1662" height="393" alt="ide_git" src="https://github.com/user-attachments/assets/0b9de3f8-9083-4dc8-b68e-105abc7ea0b4" />

## 설치

### 터미널 UI (권장)

TUI는 전체 워크플로우를 안내하는 대화형 마법사입니다. 사전 요구사항 없음 — 설치 프로그램이 모든 것을 처리합니다.

```bash
# TUI 설치
curl -fsSL https://raw.githubusercontent.com/SkeneTechnologies/skene/main/tui/install.sh | bash

# 실행
skene
```

### Python CLI

명령줄을 선호하는 경우, `uvx`로 Skene를 직접 실행하거나(설치 불필요) 전역으로 설치할 수 있습니다:

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 직접 실행 (설치 불필요)
uvx skene

# 또는 전역 설치
pip install skene
```

CLI 사용법에 대한 자세한 내용은 [문서](https://www.skene.ai/resources/docs/skene)를 참조하세요.

## 모노레포 구조

| 디렉토리 | 설명 | 언어 | 배포 |
|----------|------|------|------|
| `src/skene/` | CLI + 분석 엔진 | Python | [PyPI](https://pypi.org/project/skene/) |
| `tui/` | 대화형 터미널 UI 마법사 | Go | [GitHub Releases](https://github.com/SkeneTechnologies/skene/releases) |
| `cursor-plugin/` | Cursor IDE 플러그인 | — | — |

TUI(`tui/`)는 대화형 마법사 경험을 제공하고 `uvx`를 통해 Python CLI를 오케스트레이션하는 Bubble Tea 앱입니다. 각 패키지는 독립적인 CI/CD 파이프라인을 가지고 있습니다.

## 기여하기

기여를 환영합니다. [이슈를 열거나](https://github.com/SkeneTechnologies/skene/issues) [풀 리퀘스트](https://github.com/SkeneTechnologies/skene/pulls)를 제출해 주세요.

## 라이선스

[MIT](https://opensource.org/licenses/MIT)

<img width="4000" height="800" alt="Skene_end_git" src="https://github.com/user-attachments/assets/04119cd1-ee00-4902-9075-5fc3e1e5ec48" />
