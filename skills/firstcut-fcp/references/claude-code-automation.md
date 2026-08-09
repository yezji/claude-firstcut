# Fully automated mode — Claude Code (Final Cut edition)

End-to-end automation for filesystem/app-access environments. User-facing text in Korean.

## 0. Ask for the source folder
No individual uploads. Korean phrasing:
> "영상이 든 폴더를 Finder에서 이 창으로 끌어다 놓으세요. 경로가 자동으로 입력돼요."
Then the two pre-transcription option questions (filler intensity, target length) from editing-questions.md, file relationships (parts/takes) when multiple, and any script.

## 1. Scan
```
python scripts/ingest.py <folder> -o sources.json
```
Absolute paths → automatic media linking on import. Show the discovered list, ask about exclusions, report warnings.

## 2–5. Transcribe → summarize/recommend → judge → cutlist
Per SKILL.md. sources array goes into the cutlist as-is. After transcription, run sample_frames.py on silences ≥ 3s and view the frames before any judgment — silent spans may be visual content, never auto-cut them.

## 6. Build FCPXML — save to the user's filesystem
```
python scripts/build_fcpxml.py cutlist.json -o <user_path>/rough_cut.fcpxml
```

## 7. Auto import — one line
```
bash scripts/open_in_fcp.sh <user_path>/rough_cut.fcpxml
```
`.fcpxml` is registered to Final Cut, so `open` imports it directly. Final Cut launches and shows an import-confirmation dialog (possibly with library selection) — one click. No MCP or keystroke automation needed, unlike the Premiere edition.

Announce first (Korean): "파이널컷을 열어서 편집본을 넣을게요. 확인 창이 뜨면 확인만 눌러주세요."

## 8. Wrap-up report (Korean)
Timeline summary (clips, time saved, candidates), connected-candidate review (V to enable), subtitle SRT location + source-timecode caveat + `/firstcut-subs`.
