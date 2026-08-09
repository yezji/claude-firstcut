---
name: firstcut-premiere
description: FirstCut(퍼스트컷) — 영상 초벌컷 편집기 (프리미어 프로용). /firstcut 명령 또는 firstcut 언급 시 사용. 전사본(대사) 내용을 기준으로 컷편집을 판단하고, 결과를 프리미어 프로에서 임포트 가능한 FCP7 XML 타임라인으로 출력한다. 렌더링하지 않고, 비파괴로 편집을 넘긴다. 사용자가 영상 컷편집, 초벌 편집, 가편집, NG 제거, 테이크 정리, 무음 제거, 말버릇 제거, "프리미어로 넘겨줘", "타임라인 만들어줘" 등을 요청하면 반드시 이 스킬을 사용한다. 사용자가 파이널컷 프로를 쓴다면 이 스킬 대신 firstcut-fcp를 사용한다. 어느 편집 프로그램을 쓰는지 불명확하면 먼저 물어본다. 렌더링된 최종 영상을 요구하는 경우가 아니라면, 영상 편집 자동화 요청은 모두 이 스킬의 대상이다.
---

# FirstCut — Premiere Pro edition

Performs a content-based rough cut of raw footage and hands off a non-destructive FCP7 XML timeline to Premiere Pro. Core principles and their sources: `references/repo-patterns.md`.

1. **Transcript-first, frames-on-demand.** The transcript is the primary editing surface; cuts land on speech boundaries and silence gaps. But silent spans are never judged blind — contact-sheet frames are viewed before classifying them. Reading, plus looking only where reading fails. (video-use)
2. **Three-layer separation.** Silence detection is math (ffmpeg), transcription is Whisper, and only editorial judgment is LLM work — text only, never media. (Ambar)
3. **Never cut before approval.** Report the analysis, ask about ambiguous spans, generate the timeline only after confirmation. (auto-cut-agent)
4. **No rendering.** Output is an XML timeline; final judgment and polish happen in Premiere.

## Language policy (token economy)

- Do all internal reasoning, planning, and intermediate artifacts (packed transcript analysis, judgment notes) **in English** — it is more token-efficient.
- Everything the user sees is **in Korean**: questions, options, progress reports, content summaries, error guidance, clip names (label/reason — the user reads them in the timeline), subtitles, final reports.
- If the user converses in another language, follow that language. The test is: "does the user see it?"

## Non-technical user protocol (always on)

Assume the user knows nothing about terminals.

- **Never ask the user to type commands.** Claude runs everything.
- When asking for a folder path, say (in Korean): "Finder(맥) 또는 파일 탐색기(윈도우)에서 영상이 든 폴더를 이 창으로 끌어다 놓으세요. 경로가 자동으로 입력돼요." Handle quotes, escapes, spaces, and Korean characters in dropped paths as-is.
- One question at a time, always with example answers.
- Define jargon inline the moment it appears (e.g., "시퀀스 = 편집이 담긴 타임라인").
- On errors, tell the user what to do next, not why it broke internally.

## Execution mode (decide first)

**If running in Claude Code or any environment with filesystem/app access, use fully automated mode**: read `references/claude-code-automation.md` and follow it — ask for the source folder (never request individual file uploads), scan it, guarantee auto media linking via absolute paths in the XML, and automate Premiere launch + XML import (3 tiers: MCP → OS automation → semi-manual).

In attachment-based environments (claude.ai), use the base workflow below.

## Workflow

```
Gather inputs → Transcribe → 3-way judgment → Ask about ambiguous spans → Finalize cutlist → Build XML → Deliver
```

### Step 1: Gather inputs
- **Source footage**: for a folder, batch-scan with `scripts/ingest.py`; for a single file, `scripts/probe.py`.
- **Editing criteria**: never ask open-ended "describe your editing preferences". Use the option-based questions in `references/editing-questions.md` verbatim — pre-transcription: filler-removal intensity (mild/normal/aggressive, with examples) and target length (trim-only/half/custom/short-form). Skip anything the user already answered.
- **Script/screenplay** (optional): if provided, script-matching mode greatly improves accuracy.

Fixed rules (no need to ask): cut speech-gap silences ≥ 0.8s **that sit between utterances** / cut NG utterances ("다시 갈게요" and similar) / for duplicate takes prefer the last one (but classify as candidate for confirmation).

**Silence ≠ cuttable.** A span with no speech can still be the most valuable footage — B-roll, product shots, scenery, demonstrations, intentional pauses, comedic beats. The silence rule above applies only to short dead air between sentences. Long silences follow the visual-check rule in Step 3.

### Step 2: Transcribe (Claude does it)

```
python scripts/transcribe.py <video> --language ko -o transcript.json --srt-out subs.srt --vocab-file glossary.txt
```

**Glossary first.** Build `glossary.txt` before transcribing: proper nouns extracted from the user's script if provided, else Question C in editing-questions.md (skippable). It biases Whisper via initial_prompt/hotwords.

**Post-correction pass (after transcription, before judgment) — the name loop.** Whisper garbles proper nouns and renders the same person's name differently across a video ("세훈/새훈/세 훈"). Run this loop:

1. **Detect (Claude, LLM-strength):** scan the transcript for (a) phonetically-similar variants of glossary terms, and (b) *unlisted* suspected names — recurring tokens that look like person names but appear with inconsistent spellings. Cluster the variants.
2. **Confirm (one batched Korean question):** show each cluster with its occurrence count and ask for the canonical spelling; let the user answer per item or "다 맞아요":
   > 받아쓰기에서 확인이 필요한 이름/용어가 있어요:
   > ① "새훈 / 새 훈"으로 들리는 이름이 7번 나와요 → 정확한 표기는? (예: 세훈)
   > ② "아이자벨 마랑" 2번 → "이자벨 마랑"이 맞을까요?
3. **Apply (deterministic):**
   ```
   python scripts/apply_glossary.py --fix "새훈=세훈" --fix "새 훈=세훈" transcript.json subs.srt
   ```
   It corrects transcript text + word arrays + all SRT cue lines (never timecodes), longest-first, reports per-term counts, flags zero-hit terms, and saves corrections.json for reuse.
4. **Persist:** append confirmed names to glossary.txt so re-transcriptions and future sessions get them right from the start. Report the correction summary to the user.

ffmpeg audio extraction + faster-whisper word timestamps (auto-installs if missing). `--srt-out` also produces a subtitle SRT — include it in the final deliverables; it imports directly as Premiere captions. Note to the user (in Korean) that its timecodes are source-based and that `/firstcut-subs` will regenerate final subtitles after the cut is locked. Subtitle lines are split at word timestamps for on-screen readability.

If the user attached an SRT: `python scripts/transcribe.py --srt input.srt -o transcript.json` (parse only, skip Whisper).

If the Whisper model download (huggingface.co) is blocked, the script prints two remedies — add the domain to network egress settings, or attach an SRT. Relay them to the user in Korean and ask which way to go.

Do not ask which language the video is in; infer from context (`ko` for Korean conversations). If unsure, omit for auto-detection.

### Step 2.5: Content summary and recommendation (after transcription, before judgment — mandatory)

Claude now knows the content. Do not judge yet. Follow the "after transcription" procedure in `references/editing-questions.md`: summarize the video into 3–7 content blocks, recommend what to drop vs. keep against the target length, flag anything valuable that would fall to cuts, and get direction confirmed. That confirmed direction becomes the criterion for Step 3. Silently discarding good content is this skill's worst failure mode.

### Step 3: 3-way judgment (the core — Claude judges directly)

Classify every span of transcript.json:

- **keep**: main-body speech, matches the script, essential to flow
- **cut**: short speech-gap silence, NG utterances, an earlier take clearly superseded by a later one, setup noise
- **candidate**: anything uncertain goes here. Duplicate takes whose winner can't be picked from text alone (tone/expression require watching), off-script ad-libs that flow well, laughter/reactions, mid-sentence fillers whose removal might cause a jump, spans that should go for length but are content-valuable

**Silent spans ≥ 3s: mandatory visual check before classification.** Transcript-blindness is this pipeline's known weakness — never classify a long silence as cut without looking:

```
python scripts/sample_frames.py <video> --from-transcript transcript.json --min-dur 3.0 -o frames/
```

This produces **contact sheets** — one labeled grid image per ~9 spans (~700 tokens each), not per-span frame sets. View the sheet(s) to triage everything at once; escalate only spans the sheet can't settle with `--span START END` (3 detailed frames). This keeps visual checking ~90% cheaper than per-span sampling.

View the sheet frames. Meaningful visuals (B-roll, product close-up, scenery, on-screen action, demonstration) → **keep** with a Korean label like "비주얼 컷 - 제품 클로즈업"; unclear or borderline (static face, ambiguous pause) → **candidate** with reason "무음이지만 화면 확인 필요"; genuinely dead (setup, black, frozen waiting) → cut. Include discovered visual spans in the Step 2.5 content-block summary so the user knows they exist.

**No overconfidence.** A wrong cut forces the user to re-review the whole source; a candidate costs 7 seconds to check. Record a one-line Korean reason per span (it becomes the clip name).

### Step 4: Ambiguous spans (hybrid)

Split candidates two ways:

**A. Decidable from text → batch questions in chat.** Never one at a time. Each item: timecode + transcript + why it's ambiguous, in Korean:

> ⚠️ 02:31–02:38 "아 근데 이거 진짜 웃긴 게…" — 대본에 없는 애드립인데 흐름상 자연스러움. keep?
> ⚠️ 04:12–04:19 vs 04:25–04:31 — 같은 문장 두 테이크. 어느 쪽?

Fold answers into the cutlist.

**B. Requires watching (tone, expression, NG nuance) → V2 track.** Do not decide. These go into the XML's V2 track as disabled candidate clips named `[keep?] label - reason` so the timeline alone is reviewable.

### Step 5: Finalize the cutlist

Save `cutlist.json` (schema: `references/cutlist-schema.md`). Report in Korean: total cuts, minutes saved, longest cuts, candidate count. (The Analyze-report-then-Apply rhythm from auto-cut-agent.)

### Step 6: Build the XML

```
python scripts/build_xml.py cutlist.json -o rough_cut.xml
```

- **V1**: confirmed keeps, back to back
- **V2**: candidates above their related cut points, `<enabled>FALSE</enabled>` (visible but excluded from playback), names carry the reason
- **A1**: audio cut identically to V1, linked to video
- NTSC-family fps (23.976/29.97/59.94) handled at the true 1000/1001 ratio

XML details and troubleshooting: `references/fcp7-xml-guide.md`.

### Step 7: Deliver

Hand over the XML, cutlist.json, and the subtitle SRT (if Claude transcribed), then guide in Korean:
1. Premiere: File → Import (Ctrl/Cmd+I) → select the XML
2. If media is offline, right-click → Link Media → point at the source (skipped entirely when absolute paths were recorded)
3. V2 candidate review: to keep, right-click → Enable, then Ctrl/Cmd-drag into V1 (ripple insert); to discard, delete
4. Add BGM/captions only after candidates are settled (insertions shift later timing); mention `/firstcut-subs` for final subtitles

## Multiple sources

Use the `sources` array plus a per-segment `source` field (`references/cutlist-schema.md`). **Timeline order = segment list order**, not file order — cross-file rearrangement is just list ordering. For competing takes across files, keep one and mark the other candidate; the candidate lands on V2 directly above its rival for side-by-side comparison. Ask about footage structure first: sequential parts vs. repeated takes changes the main job (ordering vs. selection).

## Final subtitles (after the cut is locked — /firstcut-subs)

When the user runs `/firstcut-subs` or asks for final subtitles:

```
python scripts/remap_subs.py cutlist.json --srt subs.srt -o final_subs.srt
```

Multi-source: repeat `--srt <source_id>=<file>`. **Precondition: the cutlist must match the actual timeline.** If the user promoted candidates in Premiere, first ask (in Korean) which ones, flip those decisions to keep, then remap. Subtitles in cut regions are dropped; boundary-straddling ones keep only the overlap (fragments < 0.3s discarded). The result imports directly as captions.

## Re-runs and edits

With cutlist.json present, skip transcription/judgment: apply the requested change ("02:31 애드립 살려줘" → flip that decision) and re-run build_xml.py.

## Cautions

- ffmpeg silencedetect default is -35dB / 0.8s. If silences are over- or under-detected (quiet sources hovering near -25dB invert detection), measure the real noise floor with ffmpeg volumedetect and adjust — never guess (auto-cut-agent).
- Multi-audio-track sources (OBS etc.): Premiere's FCP7 XML import may only see the first track. ingest.py warns; relay to the user.
- Source paths are recorded as absolute file:// URLs. Knowing the real path removes the relink step; otherwise record the filename and guide relinking.
