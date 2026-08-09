# Fully automated mode — Claude Code (Premiere edition)

The end-to-end automated sequence for environments with filesystem/app access. Follow in order. All user-facing text in Korean.

## 0. Start: ask for the source folder

Never request individual file uploads — footage is usually multiple files, and weaving them into one timeline is this skill's job. Ask (Korean):

> "촬영본이 들어 있는 폴더를 Finder(맥)/파일 탐색기(윈도우)에서 이 창으로 끌어다 놓으세요. 폴더 안의 영상을 전부 읽어서 하나로 엮을게요."

After receiving the folder, ask the two pre-transcription items from editing-questions.md (filler intensity, target length) as options, confirm file relationships (parts vs. takes) when multiple, and collect a script if one exists.

## 1. Scan the folder

```
python scripts/ingest.py <folder> -o sources.json
```

- Collects video files in filename order and probes them all.
- **Absolute paths land in sources — this is the automation keystone**: build_xml.py writes them into the XML pathurl, so media links automatically at import. The relink step disappears.
- Report warnings (multi audio tracks, fps mismatch) and confirm before proceeding.
- Show the discovered list (name, duration, fps) and ask (Korean): "이 파일들이 맞나요? 제외할 파일 있나요?" — folders often contain B-roll or test shots.

## 2. Per-file transcription

For each source:

```
python scripts/transcribe.py <file> --language ko -o transcript_<id>.json --srt-out subs_<id>.srt --vocab-file glossary.txt
```

Run sequentially with progress reports in Korean ("3/7번째 파일 전사 중, 예상 2분"). Model-download failures: see SKILL.md.

After transcription, sample frames from long silences (`sample_frames.py --from-transcript ... --min-dur 3.0`) and view them before judgment — silent spans may be B-roll or product shots, never auto-cut them.

## 3–5. Judgment → questions → cutlist

Same as SKILL.md Steps 2.5–5. Put the sources array from sources.json straight into the cutlist and tag each segment's `source`. Cross-file take comparison is the heart of the judgment.

## 6. Build the XML

```
python scripts/build_xml.py cutlist.json -o <folder>/rough_cut.xml
```

**Save the XML to the user's filesystem** (source or project folder) — Premiere can't open files inside a container.

## 7. Auto import into Premiere (3 tiers)

Try top-down; fall through on failure. Media linking is already automatic at every tier.

### Tier 1 — Premiere MCP (most reliable, fully automatic)

If `adobe-premiere-pro-mcp` (hetpatel-11) is installed and connected:
1. `verify_premiere_connection`
2. Create a project if none is open
3. Import rough_cut.xml via the import tool
4. Open the created sequence

If not installed, offer the one-time setup (then it's always fully automatic):

```
npm install -g adobe-premiere-pro-mcp
premiere-pro-mcp --install-cep
# restart Premiere → Window → Extensions → MCP Bridge → register in Claude Code → verify_premiere_connection
```

Declined → Tier 2.

### Tier 2 — OS automation (macOS)

```
bash scripts/open_in_premiere.sh /abs/path/rough_cut.xml
```

Launches Premiere → Import (Cmd+I) → path field (Cmd+Shift+G) → types the XML path → Open. Constraints:
- First run needs Accessibility permission for the terminal (System Settings → Accessibility); explain if the permission error appears.
- **Import requires an open project.** Stuck at the home screen → ask the user to open a project, then retry.
- UI timing can slip; failure is harmless. Retry once, then Tier 3.
- Windows: launch only, then print the Ctrl+I instruction (SendKeys is unreliable for focus).

Announce before running (Korean): "프리미어에 가져오기 명령을 자동으로 보낼게요. 잠깐 키보드/마우스를 건드리지 마세요."

### Tier 3 — semi-manual (final fallback)

Launch Premiere and guide (Korean):

> "프리미어에서 Ctrl+I(맥 Cmd+I) → rough_cut.xml 선택, 이 한 번이면 끝나요. 미디어는 자동으로 연결됩니다."

## 8. Wrap-up report (Korean)

- Timeline summary (clip count, time saved, candidate count)
- V2 review instructions (SKILL.md Step 7)
- Subtitle SRT location + source-timecode caveat + `/firstcut-subs`

## Cautions

- Tier 2 sends keystrokes: announce beforehand; auto-import is opt-in — if the user declines app control, go straight to Tier 3.
- Always leave XML, cutlist.json, and subtitle SRTs on the user's filesystem (the anchor for re-runs and edits).
