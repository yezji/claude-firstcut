# Borrowed open-source patterns — self-contained knowledge

Written so the original repos never need revisiting. Links are attribution only.

## 1. browser-use/video-use — editing philosophy and token design
https://github.com/browser-use/video-use (17k+ stars, MIT)

**Core insight: "The LLM never watches the video. It reads it."** Naive frame-dumping is 30,000 frames × 1,500 tokens = 45M tokens of noise. video-use does the same job with a ~12KB packed transcript plus a handful of on-demand PNGs — the same idea as browser-use handing an LLM a structured DOM instead of screenshots.

**Two-layer input:**
- Layer 1 — audio transcript (always loaded): word timestamps + speaker diarization + audio events (`(laughter)`, `(applause)`, `(sigh)`). All takes pack into one document:
  ```
  ## C0103  (duration: 43.0s, 8 phrases)
    [002.52-005.36] S0 Ninety percent of what a web agent does is wasted.
    [006.08-006.74] S0 We fixed this.
  ```
  → FirstCut implication: pack multi-source transcripts in this shape (fileID + span + speaker + sentence) for token efficiency and cross-file comparison.
- Layer 2 — visual composite (on demand): filmstrip + waveform + word-label PNG, called only at decision points (ambiguous pauses, retake comparisons, cut sanity checks).

**Pipeline:** Transcribe → Pack → LLM Reasons → EDL → Render → Self-Eval (fix + re-render, max 3). Self-eval inspects the rendered output at every cut boundary for visual jumps, audio pops, hidden subtitles.

**Five design principles (condensed):** ① text + on-demand visuals, no frame dumps ② audio primary, cuts on speech boundaries and silence gaps ③ Ask → Confirm → Execute → Self-Eval → Persist; never cut without strategy approval ④ zero assumptions about content type — look, ask, edit ⑤ hard production-correctness rules, artistic freedom elsewhere.

**Also worth stealing:** 30ms audio fades at every cut boundary (pop prevention); session memory persisted to `project.md` so next session resumes; outputs isolated in an `edit/` folder beside the sources. In FirstCut, cutlist.json plays the session-memory role.

## 2. Robelob/Ambar-AI-Video-Editor-Plugin — three-layer architecture
https://github.com/Robelob/Ambar-AI-Video-Editor-Plugin-For-Premiere-Pro

Premiere UXP+CEP plugin. Three layers buy cost, privacy, and speed:

- **Layer 1 — silence detection = pure math.** Reads source PCM via AudioContext, RMS amplitude. No AI, no network. Returns silence ranges + speech segments. → FirstCut uses ffmpeg silencedetect for the same role.
- **Layer 2 — transcription = Whisper, speech segments only.** Only small speech-only WAV slices go to Whisper (Groq/OpenAI/local); each word time is offset by its segment start to rebuild the global timeline. Never uploads the whole file — fast and cheap.
- **Layer 3 — editorial judgment = LLM, text only (~2KB).** A transcript summary goes to the LLM; it returns `confirmedCuts + retakes + broll` suggestions as JSON. **No video file is ever uploaded — the cloud only receives text.**

**Non-destructive stance:** results become timeline markers, not cuts ("no cuts"); B-roll suggestions land on V2 (broll-placer); per-sequence session state persists in a Project.Memory panel.

→ FirstCut implications: judgment input is only the packed transcript + silence list; treating retakes (repeated-take detection) as a first-class judgment output also comes from here.

## 3. rafcopy/auto-cut-agent — approval UX and cut-parameter vocabulary
https://github.com/rafcopy/auto-cut-agent

Premiere UXP panel + local Node server. Silence removal + LLM repeated-take dedup.

**Approval rhythm (adopted verbatim):** Analyze reports "how many cuts, how much time removed, the longest ones." **Nothing touches the timeline until Apply.**

**Measure, don't guess:** "Measure from audio" reads the actual noise floor with ffmpeg to set the dB threshold. → FirstCut: if the -35dB default misfires, measure mean/max volume with ffmpeg volumedetect and adjust.

**Cut-parameter vocabulary (for questions/tuning):**
| Parameter | Meaning | Effect |
|---|---|---|
| Silence threshold (dB) | below = silence | less negative = cuts more |
| Min silence duration | shorter quiet is kept | protects natural word gaps |
| Cut margin | air at each cut edge | prevents clipped-feeling cuts |
| Merge adjacent cuts | close cuts become one | avoids machine-gun micro-cuts |
| Absorb fragments | tiny kept slivers absorbed into surrounding cut | removes meaningless shards |

**Preset idea:** talking head / interview / screencast / aggressive. Other lessons: skip (don't cut) speed-ramped clips; treat nested sequences as opaque blocks; analyze the real file on disk, not the editor's render.

## 4. WyattBlue/auto-editor — XML handoff and field-tested traps
https://github.com/WyattBlue/auto-editor (4k+ stars, actively maintained)

`auto-editor video.mp4 --export premiere` is the original render-free FCP7 XML handoff (also resolve / final-cut-pro / shotcut). `--margin 0.2sec` for cut air.

**Mines it stepped on (FirstCut avoids in code):**
- **NTSC ratio:** 23.976/29.97/59.94 are exactly timebase×1000/1001. Integer approximations drift cuts cumulatively (~18 frames per 10 minutes); auto-editor only fixed this in 2026. → handled by rate_info() in build_xml/build_fcpxml.
- **Multiple audio tracks (#70):** Premiere's FCP7 XML import may recognize only the first audio track. → ingest.py warns.
- **Low audio levels (#404):** sources hovering near -25dB invert detection with default thresholds — speech gets cut, silence stays. → fix by measuring.

## 5. Others (brief)
- **OpenTimelineIO**: the recommended Premiere interchange is FCP7 XML, not AAF (AAF appends suffixes to clip names, breaking relink). FirstCut generates XML directly for disabled-clip control.
- **hetpatel-11/Adobe_Premiere_Pro_MCP**: 283 tools over a CEP bridge. `npm i -g adobe-premiere-pro-mcp` → `premiere-pro-mcp --install-cep` → Premiere: Window → Extensions → MCP Bridge. Used for tier-1 auto import.
- **pymiere**: unmaintained; its author recommends XML generation (OTIO → XML) for programmatic Premiere files.
