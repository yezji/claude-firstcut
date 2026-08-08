# FCP7 XML (xmeml v4) structure and troubleshooting

What build_xml.py generates. Consult when debugging imports.

## Structure

```
<xmeml version="4">
 <sequence>
  <name>, <duration>, <rate>, <timecode>
  <media>
   <video>
    <format>          ← sequence resolution/framerate
    <track>  V1       ← keep clips (enabled TRUE)
    <track>  V2       ← candidate clips (enabled FALSE)
   </video>
   <audio>
    <track>  A1       ← audio cut identically to V1
   </audio>
  </media>
 </sequence>
</xmeml>
```

## Key concepts

- **A clipitem's four time values**: `<start>/<end>` = timeline position (frames); `<in>/<out>` = source range (frames). This split is what makes the edit non-destructive — stretching a cut boundary in Premiere restores trimmed material.
- **`<enabled>FALSE</enabled>`**: disabled clip — visible (dimmed) but excluded from playback/render. Used for V2 candidates. Re-enable via right-click → Enable.
- **`<file id>` referencing**: full file definition only in the first clipitem; later ones use `<file id="file-1"/>`. Duplicated definitions slow imports or duplicate media.
- **`<link>`**: binds a V1 video clip to its A1 audio clip so they move together.
- **NTSC**: 29.97 etc. is written as `<timebase>30</timebase><ntsc>TRUE</ntsc>`, and sec→frame conversion must use 30×1000/1001. Integer rounding drifts ~18 frames per 10 minutes.

## Usage order in Premiere (guide the user in Korean)

1. File → Import (Ctrl/Cmd+I) → select the XML → a sequence appears in the project panel
2. If media is offline (red frames): right-click a clip → Link Media → Locate → point at the source; matching filenames relink everything at once
3. V2 candidate review by clip name (`[keep?] reason`): keep → right-click → Enable → Ctrl/Cmd-drag into V1 (ripple insert); discard → delete
4. BGM/captions only after candidates are settled (insertions shift later timing)

## Common problems

| Symptom | Cause | Fix |
|---|---|---|
| Imports fine but cuts slightly drift | NTSC ratio miscalculation | ensure cutlist fps equals probe's measured fps; never write 29.97 as 30 |
| Only the first audio track imports | FCP7 XML format limitation (auto-editor #70) | warn upfront for multi-track sources; merge needed tracks into a proxy with ffmpeg, or place the rest manually |
| Korean clip names garbled | encoding | the XML is saved UTF-8; don't re-save with other tools |
| Relink says "attributes don't match" | fps/resolution mismatch | verify cutlist source info matches probe measurements |
| V2 clips cover playback | enabled imported as TRUE | some older Premiere builds; toggle the V2 track output (eye icon) off while reviewing |
