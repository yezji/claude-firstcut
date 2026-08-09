---
description: FirstCut — 영상 초벌컷 자동 편집 시작
---
Start a FirstCut rough-cut session.

1. Confirm which NLE the user works in (ask in Korean if unknown):
   - Premiere Pro → use the `firstcut-premiere` skill
   - Final Cut Pro → use the `firstcut-fcp` skill
2. Read that skill's SKILL.md and follow the fully automated workflow
   (references/claude-code-automation.md) from the top: ask for the footage
   folder (drag-and-drop guidance) → option questions (filler intensity,
   target length) → transcribe → contact-sheet check of silent spans →
   content summary & recommendation →
   judgment → build timeline → auto-import into the NLE.
3. Assume the user knows nothing about terminals; never ask them to type commands.
4. Reason internally in English (token economy); everything the user sees is in Korean.
