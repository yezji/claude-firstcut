---
description: FirstCut — 컷 확정 후 완성본 기준 최종 자막 뽑기
---
Regenerate final subtitles (SRT) matched to the locked, edited timeline.

1. Locate this edit's cutlist.json and the source-based subtitle SRT(s)
   (same working folder). If missing, ask (in Korean) which edit this is
   and where the files live.
2. Ask (Korean): "타임라인의 보류 후보(반투명 클립) 중 살린 게 있나요?
   있다면 어떤 것들인지 알려주세요 (클립 이름이나 대략 위치로)."
   - Promoted candidates → flip decision candidate → keep in cutlist.json.
     Discarded ones stay as-is.
   - If cut boundaries moved significantly, update those keep start/end too.
3. If corrections.json exists from the editing session, apply it to the source
   SRT(s) first via scripts/apply_glossary.py --fix-file corrections.json <srt...>
   so name/term fixes carry into the final subtitles.
4. Run the skill's (firstcut-premiere or firstcut-fcp) scripts/remap_subs.py:
   python scripts/remap_subs.py cutlist.json --srt subs.srt -o final_subs.srt
   (multi-source: repeat --srt <source_id>=<file>)
5. Save final_subs.srt to the user's filesystem, tell them where it is,
   and give a one-line Korean caption-import instruction for their NLE.
Never ask the user to type commands. Reason in English; user-facing output in Korean.
