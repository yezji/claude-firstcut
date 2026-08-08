# Contributing to FirstCut

Issues and PRs welcome — real-footage failure reports are the most valuable
contribution (attach the cutlist.json and describe what the timeline got wrong;
never upload footage itself).

## Ground rules
- Keep the language split: Claude-read files in English, user-visible strings in
  Korean (see CLAUDE.md).
- The two builders (build_xml.py / build_fcpxml.py) and remap_subs.py must keep
  identical margin/merge logic — change one, change all three.
- Run the quick pipeline check in CLAUDE.md before submitting.
- No rendering features. FirstCut hands off to the NLE by design.

## Good first contributions
- DaVinci Resolve edition (FCP7 XML already imports there — needs testing + docs)
- Windows auto-import for Premiere (current tier 2 is macOS-only)
- Filler-word lexicons for more languages
