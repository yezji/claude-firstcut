# Editing-criteria question design

Open-ended questions ("describe your editing preferences") are forbidden. Use the option sets below. In Claude Code, present numbered text options; in claude.ai, use the option-selection UI tool if available. Two timings: 2 mandatory items before transcription, content-based items after.

The quoted Korean blocks are user-facing copy — present them verbatim (they are the product voice).

## Before transcription — 2 mandatory items (present together)

### Question A. Filler-removal intensity
Filler removal always happens; ask only the intensity, always with examples:

> 말버릇("어…", "음", "그니까")은 기본으로 정리해 드려요. 어느 정도로 할까요?
>
> **1. 순한맛** — 문장 사이의 긴 필러만 제거해요.
>    예: "~였습니다. 어… 그래서 다음은" → "~였습니다. 그래서 다음은"
>    문장 중간은 안 건드려서 말투가 자연스럽게 남아요. (브이로그, 인터뷰 추천)
>
> **2. 보통** — 문장 사이 필러에 더해, 반복 말버릇과 어색한 재시작도 정리해요.
>    예: "이게, 이게 뭐냐면" → "이게 뭐냐면" / "그니까 그니까" → "그니까"
>    (대부분의 유튜브 영상에 무난)
>
> **3. 매운맛** — 문장 중간의 "어", "음"까지 단어 단위로 걷어내요.
>    예: "이걸 어… 30퍼센트 늘리면" → "이걸 30퍼센트 늘리면"
>    말 밀도가 최고가 되지만 컷이 많아져 점프컷 느낌이 나요. (정보 전달형, 숏폼 추천)

Candidate policy per intensity: mild keeps all mid-sentence fillers; normal marks only ambiguous mid-sentence fillers as candidate; aggressive removes them but marks jump-risky ones candidate.

### Question B. Target length

> 완성본 분량은 어떻게 할까요?
>
> **1. 다듬기만** — NG·무음·말버릇만 지우고 내용은 전부 살려요. (원본이 이미 계획대로 촬영된 경우)
> **2. 절반쯤 압축** — 곁가지 이야기를 정리해서 원본의 절반 안팎으로 줄여요.
> **3. 시간 지정** — 원하는 분량을 알려주세요. (예: "3분", "10분 안쪽")
> **4. 숏폼** — 60초 안쪽으로, 핵심 한 줄기만 남겨요.

For options 2–4: content removed for length that is still valuable must become candidate, never silent deletion.

### Question C. Domain glossary (optional — ask once, skippable)

Whisper mis-hears proper nouns, brand names, and jargon. If a script was
provided, extract proper nouns from it automatically and skip this question.
Otherwise ask once (Korean), and accept "없어요/스킵":

> 영상에 자주 나오는 브랜드명·전문용어·사람 이름이 있나요?
> 받아쓰기 정확도가 올라가요. (예: "상하, 이자벨 마랑, 코닥 포트라")
> 없거나 모르면 "없어요"라고 하셔도 됩니다.

Person names deserve extra attention — even unlisted ones get caught later:
the post-transcription name loop (SKILL.md) detects inconsistently-spelled
name candidates and confirms them with the user, so missing one here is OK.

Save collected terms to `glossary.txt` (one per line) next to the cutlist for
reuse across re-runs, and pass it to transcription via `--vocab-file`.

## After transcription — content-based recommendation (this skill's differentiator)

Claude now knows the content. Before 3-way judgment, always show the structure and confirm direction:

1. **Content-block summary**: 3–7 numbered blocks with rough durations. **Silent visual spans found via frame sampling are blocks too** — list them so the user knows they were seen, not silently cut (e.g. "⑥ 무음 비주얼 컷 — 제품 클로즈업으로 보임 (40초 지점, 8초)").
   > 전사해 보니 이런 구성이에요 (원본 12분):
   > ① 인사와 근황 (1분 30초)
   > ② 주제 소개 (3분)
   > ③ 직접 겪은 에피소드 (2분 30초)
   > ④ 핵심 정리와 팁 (3분)
   > ⑤ 마무리와 다음 예고 (2분)

2. **Recommendation against the target**: propose drops with reasons, but hand over the decision.
   > 3분 목표면 ②와 ④가 뼈대예요. ①은 첫 문장만 남기고, ⑤는 마지막 한 마디만 남기는 걸 추천해요.
   > ③ 에피소드는 시간상 빼는 게 맞는데, 이 영상에서 제일 사람 냄새 나는 부분이라 아깝긴 해요. 어떻게 할까요?
   > **1. 추천대로** / **2. ③도 살리기 (분량 초과 감수)** / **3. 직접 고르기 (번호로 알려주세요)**

3. **Flag valuable spans at risk**: if a span Claude rates highly (key info, unique story, a great line) falls into the drop zone, always surface it and confirm. Silently discarding good content is the worst failure mode.

4. The confirmed direction becomes the criterion for 3-way judgment. The batched ambiguous-span questions (Step 4) proceed as usual afterward.

## Question etiquette
- Never exceed one screenful at a time. 2 items pre-transcription → 1–2 post.
- Every option carries an example or a "who it suits" note.
- Skip items the user already answered (e.g., "숏폼으로 만들어줘") — just confirm.
- Accept answers by number or by words ("보통으로", "매운맛").
