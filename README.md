# 🎬 FirstCut · 퍼스트컷

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-d97757.svg)](https://claude.com/claude-code)
[![GitHub stars](https://img.shields.io/github/stars/yezji/claude-firstcut?style=social)](https://github.com/yezji/claude-firstcut/stargazers)

**말로 시키는 초벌컷.** 촬영본 폴더를 [클로드 코드](https://claude.com/claude-code)에 건네면 — 대사를 받아쓰고, NG·무음·중복 테이크를 판단하고, 헷갈리는 건 물어본 뒤, 프리미어 프로 또는 파이널컷 프로에 편집 타임라인을 띄워 줍니다. 렌더링 없음, 원본 무손상, 영상 업로드 없음.

```
/firstcut → 폴더 → 선택지 답하기 → 받아쓰기 → 내용 추천 → 타임라인 → NLE 자동 임포트
```

## Quick Start

터미널에 한 줄 (처음 한 번):

```bash
curl -fsSL https://raw.githubusercontent.com/yezji/claude-firstcut/main/install.sh | bash
```

클로드 코드를 열고:

```
/firstcut
```

**끝입니다.** 클로드가 편집 프로그램과 영상 폴더를 물어보고 나머지를 이끕니다. 터미널은 설치 한 줄이 전부고, 이후로는 대화만 하면 됩니다.

**필요한 것:** [클로드 코드](https://claude.com/claude-code) · 프리미어 프로 또는 파이널컷 프로 · ffmpeg (없으면 설치 스크립트가 시도하고, 실패 시 클로드에게 부탁하면 됩니다)

## 무엇을 해주나요

- ✂️ **내용 기준 편집** — 무음만 자르는 게 아니라 대사를 읽고 판단합니다. "NG는 마지막 테이크만", "3분으로 압축" 같은 지시를 이해합니다
- 🎚️ **선택지로 묻는 편집 기준** — 말버릇 정리 강도(순한맛/보통/매운맛), 목표 분량을 예시와 함께 보기로 묻습니다
- 🧠 **전사 후 내용 추천** — 받아쓴 뒤 영상 구성을 요약하고, 뺄 것·살릴 것을 추천합니다. 좋은 콘텐츠를 조용히 버리지 않습니다
- 🙋 **애매하면 보류** — 텍스트로 판단 가능한 건 모아서 질문, 영상을 봐야 아는 건(톤·표정) 타임라인에 반투명 "보류 후보"로 올려 근거와 함께 남깁니다
- 🔒 **비파괴 핸드오프** — 출력은 XML 타임라인 설계도. 컷 경계를 늘리면 잘린 부분이 되살아납니다
- 🔐 **프라이버시** — 클로드가 읽는 것은 대사 텍스트뿐, 영상 파일은 어디에도 업로드되지 않습니다
- 📝 **자막 두 번** — 받아쓴 자막(원본 기준), 그리고 컷 확정 후 `/firstcut-subs`로 완성본 시간에 맞춘 최종 자막

## Commands

| 명령 | 설명 |
| --- | --- |
| `/firstcut` | 초벌컷 편집 시작 — 폴더 → 질문 → 전사 → 판단 → 타임라인 → NLE 자동 임포트 |
| `/firstcut-subs` | 컷 확정 후, 완성본 타임라인 기준 최종 자막(srt) 재생성 |

## Skills

| 스킬 | 대상 | 출력 | 자동 임포트 |
| --- | --- | --- | --- |
| `firstcut-premiere` | 어도비 프리미어 프로 | FCP7 XML (V1 확정 / V2 보류 후보) | MCP 연동 → 키 입력 자동화(맥) → Ctrl+I 안내, 3티어 |
| `firstcut-fcp` | 애플 파이널컷 프로 | FCPXML (스파인 / 연결 클립 후보) | `open` 한 줄로 바로 임포트 |

두 스킬 모두 자동 설치되며, 대화에서 쓰는 프로그램에 맞는 쪽이 동작합니다. 절대경로가 XML에 기록되므로 **미디어 연결(relink)이 필요 없습니다.**

## Workflow

```
/firstcut
   │
   ├─ ① 폴더 스캔 ─────── 영상 목록 확인, 제외 파일 선택
   ├─ ② 편집 기준 ─────── 말버릇 강도 · 목표 분량 (보기 선택)
   ├─ ③ 전사 ──────────── faster-whisper 단어 타임스탬프 (+자막 srt)
   ├─ ④ 내용 추천 ─────── 구성 블록 요약 → 뺄 것/살릴 것 확인
   ├─ ⑤ 3분류 판단 ────── keep / cut / candidate(보류)
   ├─ ⑥ 애매 구간 질문 ── 타임코드+전사+사유 일괄 질문
   ├─ ⑦ 타임라인 생성 ─── FCP7 XML 또는 FCPXML (비파괴)
   └─ ⑧ NLE 자동 임포트 ─ 시퀀스가 열린 상태로 완성

(편집 프로그램에서 보류 후보 정리)
   └─ /firstcut-subs ──── 완성본 기준 최종 자막
```

## Project Structure

```
claude-firstcut/
├── install.sh                     # 한 줄 설치 스크립트
├── commands/                      # /firstcut, /firstcut-subs
├── skills/
│   ├── firstcut-premiere/
│   │   ├── SKILL.md               # 워크플로우 (영어 — 클로드가 읽음)
│   │   ├── scripts/               # probe, ingest, transcribe, build_xml,
│   │   │                          #   remap_subs, open_in_premiere
│   │   └── references/            # 편집 질문 설계, cutlist 스키마,
│   │                              #   XML 가이드, 자동화 절차, 차용 패턴
│   └── firstcut-fcp/
│       ├── SKILL.md
│       ├── scripts/               # build_fcpxml, open_in_fcp + 공용
│       └── references/
├── docs/
│   └── getting-started.md         # 초보자용 시작 가이드
├── CLAUDE.md                      # 이 레포를 클로드 코드로 열었을 때의 컨텍스트
└── CONTRIBUTING.md
```

## Documentation

- [시작 가이드](docs/getting-started.md) — 처음부터 완성까지, 초보자 기준
- [편집 질문 설계](skills/firstcut-premiere/references/editing-questions.md) — 무엇을 어떻게 묻는가
- [cutlist 스키마](skills/firstcut-premiere/references/cutlist-schema.md) — 판단 기록 형식 (재실행·수정의 기준점)
- [FCP7 XML 가이드](skills/firstcut-premiere/references/fcp7-xml-guide.md) · [FCPXML 가이드](skills/firstcut-fcp/references/fcpxml-guide.md) — 구조와 트러블슈팅
- [차용한 오픈소스 패턴](skills/firstcut-premiere/references/repo-patterns.md) — 설계 근거 (자립형 지식 문서)

## 자주 묻는 질문

**원본이 망가질 수 있나요?**
아니요. 원본 파일은 수정되지 않습니다. 출력은 "어디를 어떻게 잘랐는지" 적힌 설계도(XML)이며, 편집 프로그램에서 언제든 되돌릴 수 있습니다.

**받아쓰기가 안 된다고 해요.**
음성 인식 모델 다운로드(huggingface.co)가 막힌 환경일 수 있습니다. 클로드가 두 가지 해결책을 안내합니다: 네트워크 허용 목록에 주소 추가, 또는 편집 프로그램의 받아쓰기로 만든 srt 첨부.

**영어 영상도 되나요?**
네. 언어는 자동 감지됩니다.

**수정은요?**
"2분 31초 애드립 살려줘" — 판단 기록(cutlist.json)만 고쳐서 타임라인을 다시 만듭니다. 재분석하지 않습니다.

## Credits

검증된 오픈소스 프로젝트들의 패턴을 조합했습니다. 각 패턴의 상세와 출처는 [repo-patterns.md](skills/firstcut-premiere/references/repo-patterns.md)에 자립형 문서로 정리되어 있습니다.

[video-use](https://github.com/browser-use/video-use) (전사 기반 편집 철학, 토큰 설계) ·
[Ambar](https://github.com/Robelob/Ambar-AI-Video-Editor-Plugin-For-Premiere-Pro) (3층 아키텍처) ·
[auto-cut-agent](https://github.com/rafcopy/auto-cut-agent) (승인 UX, 컷 파라미터) ·
[auto-editor](https://github.com/WyattBlue/auto-editor) (XML 핸드오프, NTSC 함정) ·
문서 구성은 [claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit)을 참고했습니다.

## License

MIT — [LICENSE](LICENSE)

---

Built for use with [Claude Code](https://claude.com/claude-code) by Anthropic.
