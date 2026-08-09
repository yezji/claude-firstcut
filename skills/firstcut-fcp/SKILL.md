---
name: firstcut-fcp
description: FirstCut(퍼스트컷) — 영상 초벌컷 편집기 (파이널컷 프로용). /firstcut 명령 또는 firstcut 언급 시 사용. 전사본(대사) 내용을 기준으로 컷편집을 판단하고, 결과를 파이널컷 프로에서 바로 열리는 FCPXML 타임라인으로 출력한다. 렌더링하지 않고, 비파괴로 편집을 넘긴다. 사용자가 파이널컷/Final Cut 환경에서 영상 컷편집, 초벌 편집, 가편집, NG 제거, 테이크 정리, 무음 제거, 자막 생성을 요청하면 반드시 이 스킬을 사용한다. 사용자가 프리미어 프로를 쓴다면 이 스킬 대신 firstcut-premiere를 사용한다. 어느 편집 프로그램을 쓰는지 불명확하면 먼저 물어본다.
---

# FirstCut — Final Cut Pro edition

Content-based rough cut with a non-destructive FCPXML handoff to Final Cut Pro. Core principles (transcript-first with contact-sheet frames for silent spans / three-layer separation / no cuts before approval / no rendering) and sources: `references/repo-patterns.md`.

## Language policy (token economy)

- Internal reasoning, planning, and intermediate artifacts: **English** (token-efficient).
- Everything the user sees: **Korean** — questions, options, reports, summaries, errors, clip names (label/reason), subtitles, final reports.
- If the user speaks another language, follow it. Test: "does the user see it?"

## Non-technical user protocol (always on)

- Never ask the user to type commands; Claude runs everything.
- Folder request phrasing (Korean): "Finder에서 영상이 든 폴더를 이 창으로 끌어다 놓으세요. 경로가 자동으로 입력돼요." Handle dropped-path quirks as-is.
- One question at a time, with example answers. Define jargon inline (e.g., "프로젝트 = 편집이 담긴 타임라인"). On errors, say what to do next.

## Execution mode

**Filesystem/app access available (Claude Code etc.) → fully automated mode**: follow `references/claude-code-automation.md` — ask for the source folder, batch-scan, absolute-path FCPXML for auto media linking, and one-line `open` import into Final Cut.

Attachment-based environments → base workflow below.

## Workflow

```
Gather inputs → Transcribe → 3-way judgment → Ask about ambiguous spans → Finalize cutlist → Build FCPXML → Deliver
```

### 1. Gather inputs
- Footage: folder → `scripts/ingest.py`; single file → `scripts/probe.py`
- Criteria: no open-ended questions. Use `references/editing-questions.md` verbatim — pre-transcription 2 items: filler intensity (mild/normal/aggressive with examples) and target length. Skip already-answered items. Script (optional) boosts accuracy.
- Fixed rules (don't ask): cut speech-gap silences ≥ 0.8s **between utterances only** / cut NG utterances / duplicate takes prefer the last (classify as candidate).
- **Silence ≠ cuttable**: B-roll, product shots, scenery, demos, intentional pauses carry no speech but are often the best footage. Long silences follow the visual-check rule below.
- Multiple files → ask about structure: sequential parts or repeated takes.

### 2. Transcribe (Claude does it)
```
python scripts/transcribe.py <video> --language ko -o transcript.json --srt-out subs.srt --vocab-file glossary.txt
```

**Glossary first**: proper nouns from the script if provided, else Question C (skippable) → glossary.txt → biases Whisper (initial_prompt/hotwords). **Post-correction name loop**: after transcribing — ① detect variant clusters of glossary terms AND unlisted suspected person names (same name spelled differently across the video); ② confirm canonical spellings with one batched Korean question (occurrence counts shown, "다 맞아요" accepted); ③ apply deterministically via `python scripts/apply_glossary.py --fix "wrong=right" transcript.json subs.srt` (corrects text + word arrays + SRT cues, longest-first, per-term counts, saves corrections.json); ④ append confirmed names to glossary.txt for future runs, and report the summary.
faster-whisper word timestamps (auto-install). The `--srt-out` SRT ships with the deliverables — usable via File → Import → Captions; note (in Korean) that timecodes are source-based and `/firstcut-subs` regenerates final subtitles after the lock. Model download blocked → the script prints two remedies (allow huggingface.co, or attach an SRT via `--srt`); relay in Korean.

### 2.5. Content summary and recommendation (mandatory, before judgment)
Claude now knows the content. Follow the "after transcription" procedure in `references/editing-questions.md`: 3–7 content blocks → drop/keep recommendation against the target length → flag valuable spans at risk → confirm direction. That direction governs Step 3. Silently discarding good content is the worst failure mode.

### 3. 3-way judgment (core)
- **keep**: main speech, script-matching, essential
- **cut**: short speech-gap silence, NG utterances, clearly superseded earlier takes, setup noise
- **candidate**: everything uncertain — take comparisons needing eyes, flowing ad-libs, reactions, risky mid-sentence fillers, valuable-but-over-length spans

**Silent spans ≥ 3s: mandatory visual check** — `python scripts/sample_frames.py <video> --from-transcript transcript.json --min-dur 3.0 -o frames/` produces labeled **contact sheets** (~9 spans per image, ~700 tokens; escalate ambiguous ones with `--span START END`). View them: meaningful visuals → keep ("비주얼 컷 - ..."), unclear → candidate ("무음이지만 화면 확인 필요"), genuinely dead → cut. Surface discovered visual spans in the Step 2.5 summary.

No overconfidence: wrong cuts cost a full re-review; candidates cost 7 seconds. One-line Korean reason per span.

### 4. Ambiguous spans (hybrid)
- Text-decidable → one batched Korean question set (timecode + transcript + why)
- Needs-watching → do not decide; becomes a **connected clip** in the FCPXML (below)

### 5. Finalize cutlist
Save `cutlist.json` (`references/cutlist-schema.md`, same format as the Premiere edition). Report in Korean: cut count, time saved, longest cuts, candidate count.

### 6. Build FCPXML
```
python scripts/build_fcpxml.py cutlist.json -o rough_cut.fcpxml
```
- **Spine (primary storyline)**: confirmed keeps
- **Connected clips (lane 1, disabled)**: candidates attached above their related cut point, `enabled="0"` so they're dimmed and excluded from playback; name `[keep?] label - reason`, reason also in `<note>`
- Audio is embedded in each asset-clip (no separate track). NTSC-family fps handled as exact rational times (1001/30000s etc.)
- Details/troubleshooting: `references/fcpxml-guide.md`

### 7. Deliver
Hand over fcpxml + cutlist.json + subtitle SRT, then guide in Korean:
1. **On macOS, double-clicking the .fcpxml (or Claude running `open`) imports it straight into Final Cut** — no import-menu dance
2. Absolute paths → media links automatically; otherwise clip → File → Relink Files
3. Connected-candidate review: keep → select clip, press V (enable), drag into the primary storyline (⌘ to insert); discard → Delete
4. BGM/captions after candidates are settled; mention `/firstcut-subs`

## Multiple sources
`sources` array + per-segment `source`. **Timeline order = segment list order** (cross-file rearrangement). Competing takes: keep one, candidate the other — the candidate attaches above its rival for direct comparison. Details: `references/cutlist-schema.md`.

## Final subtitles (after lock — /firstcut-subs)
When the user runs `/firstcut-subs` or asks for final subtitles:
```
python scripts/remap_subs.py cutlist.json --srt subs.srt -o final_subs.srt
```
Multi-source: repeat `--srt <id>=<file>`. Precondition: cutlist must match the real timeline — ask (Korean) which candidates were promoted, flip them to keep, then remap. Cut-region subtitles drop; boundary overlaps are trimmed (<0.3s fragments discarded).

## Re-runs and edits
cutlist.json present → skip transcription/judgment; apply the change and re-run build_fcpxml.py.

## Cautions
- Infer transcription language from context; omit for auto-detect if unsure.
- Final Cut creates an event/project in the currently open library on import.
- Multi-audio-track sources: relay ingest.py warnings to the user.
