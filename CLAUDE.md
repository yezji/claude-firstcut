# FirstCut — repo context for Claude Code

This repository IS the product: two Claude Code skills plus slash commands that
turn raw footage into a rough-cut NLE timeline. If a user opened this repo and
asks to edit video, do not improvise — use the skills.

## What lives where
- `skills/firstcut-premiere/` — Premiere Pro edition. SKILL.md is the workflow;
  scripts/ are the executable pipeline; references/ hold question design,
  cutlist schema, FCP7 XML guide, automation tiers, borrowed patterns.
- `skills/firstcut-fcp/` — Final Cut edition (FCPXML, connected-clip candidates,
  one-line `open` import). Shares probe/ingest/transcribe/remap_subs.
- `commands/` — `/firstcut` (start a session), `/firstcut-subs` (final subtitles).
- `install.sh` — copies skills to ~/.claude/skills and commands to ~/.claude/commands.
- `docs/getting-started.md` — beginner guide (Korean, user-facing).

## Conventions (follow when editing this repo)
- Claude-read files (SKILL.md, references, comments, help text): **English**.
- User-visible strings (question copy, clip-name literals like "컷 1"/"후보",
  sequence name "초벌컷", README, install.sh echo messages): **Korean** — intentional.
- cutlist.json is the single source of truth for an edit; builders and
  remap_subs must share identical margin/merge logic or timecodes drift.
- NTSC fps must use the true 1000/1001 ratio (see rate_info in both builders).
- Never render video; never touch originals; candidates are never silently dropped.

## Quick pipeline check after changes
```
python skills/firstcut-premiere/scripts/build_xml.py <cutlist> -o /tmp/t.xml
python skills/firstcut-fcp/scripts/build_fcpxml.py <cutlist> -o /tmp/t.fcpxml
python skills/firstcut-premiere/scripts/remap_subs.py <cutlist> --srt <srt> -o /tmp/t.srt
```
