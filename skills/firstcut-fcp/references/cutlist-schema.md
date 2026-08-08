# cutlist.json schema

Input to build_xml.py / build_fcpxml.py and the persistent record of editorial judgment. For re-runs and edits, modify this file and regenerate — never re-transcribe or re-judge.

```json
{
  "source": {
    "path": "/Users/yeji/footage/raw.mp4",
    "name": "raw.mp4",
    "fps": 29.97,
    "width": 1920,
    "height": 1080,
    "duration_sec": 632.4,
    "audio_sample_rate": 48000,
    "audio_channels": 2
  },
  "sequence_name": "초벌컷_raw",
  "margin_sec": 0.2,
  "segments": [
    {"start": 0.0,  "end": 12.3, "decision": "keep",
     "label": "오프닝", "text": "안녕하세요...", "reason": ""},
    {"start": 12.3, "end": 14.6, "decision": "cut",
     "reason": "무음 2.3초"},
    {"start": 14.6, "end": 21.0, "decision": "candidate",
     "label": "애드립", "text": "아 근데 이거 진짜...",
     "reason": "대본에 없지만 흐름 자연스러움"},
    {"start": 21.0, "end": 28.5, "decision": "cut",
     "reason": "NG 앞테이크 (28.5초에 재촬영 존재)"}
  ]
}
```

## Field rules

- `source`: paste probe.py output directly. `path` should ideally be the user's real absolute path (otherwise record the filename and guide relinking).
- `segments`: in source-time order. They need not tile the whole source — time not covered by a keep is simply cut. `cut` segments are for the record (reason preservation) and never appear in the XML.
- `decision`: exactly one of `keep` | `cut` | `candidate`.
- `label`: becomes the clip name. Keep it short (readable in a timeline). **Korean — the user reads it.**
- `reason`: one-line rationale. **Korean.** Candidates render as `[keep?] label - reason` in the clip name and clip comment/note.
- `margin_sec`: air added around each keep (default 0.2s). Overlapping keeps after margin auto-merge.

## Edit workflow example

User: "02:31 애드립 살려줘" → flip that candidate's decision to keep → re-run the builder. No re-transcription or re-judgment.

## Multi-source format

Replace `source` with a `sources` array and tag each segment with a `source` id:

```json
{
  "sources": [
    {"id": "t1", "path": "/footage/take1.mp4", "name": "take1.mp4",
     "fps": 29.97, "width": 1920, "height": 1080, "duration_sec": 312.0,
     "audio_sample_rate": 48000, "audio_channels": 2},
    {"id": "t2", "path": "/footage/take2.mp4", "name": "take2.mp4",
     "fps": 29.97, "width": 1920, "height": 1080, "duration_sec": 120.0,
     "audio_sample_rate": 48000, "audio_channels": 2}
  ],
  "sequence_name": "초벌컷",
  "margin_sec": 0.2,
  "segments": [
    {"source": "t2", "start": 2.0, "end": 8.0, "decision": "keep",
     "label": "오프닝(재촬영)"},
    {"source": "t1", "start": 18.0, "end": 24.0, "decision": "keep",
     "label": "본편"},
    {"source": "t2", "start": 12.0, "end": 20.0, "decision": "candidate",
     "label": "오프닝 다른 버전", "reason": "t1 오프닝과 톤 비교 필요"}
  ]
}
```

Rules:
- **Timeline order = segment list order.** Cross-file rearrangement is just list ordering.
- Omitted `source` defaults to the first source.
- Margin merging happens only between adjacent segments of the same source.
- Competing takes across files: keep one + candidate the other → the candidate lands directly above its rival.
- Per-source fps mismatches trigger a builder warning; sequence settings follow the first source (or `sequence_source`).
- With multiple sources, clip names get an automatic `[source_id]` prefix.
