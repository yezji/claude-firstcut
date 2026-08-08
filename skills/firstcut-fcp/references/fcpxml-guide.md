# FCPXML structure and troubleshooting

What build_fcpxml.py generates (FCPXML 1.9).

## Structure
```
<fcpxml>
 <resources>
  <format>  ← framerate/resolution
  <asset>   ← source files (file:// path in media-rep)
 </resources>
 <library><event><project>
  <sequence><spine>
   <asset-clip>           ← confirmed clips on the primary storyline
    <asset-clip lane="1" enabled="0">  ← connected candidate above it
   </asset-clip>
  </spine></sequence>
 </project></event></library>
</fcpxml>
```

## Key concepts
- **Rational time**: every timestamp is a rational-second string like "1001/30000s" and must be an integer multiple of the frame duration, or the import is rejected. build_fcpxml.py computes frames × frameDuration, so it is always consistent.
- **asset-clip times**: `offset` = timeline position, `start` = source in-point, `duration` = length. The non-destructive core.
- **Connected clips (lane 1)**: ride on a parent clip and move with it. `enabled="0"` renders them dimmed and excluded from playback; V toggles enable in Final Cut.
- **Audio**: assets carry hasAudio, so one clip references video+audio together — no separate audio track.
- `.fcpxml` is registered to Final Cut on macOS: `open` / double-click imports it directly.

## Usage order in Final Cut (guide the user in Korean)
1. Double-click the .fcpxml (or Claude runs `open`) → confirm the target library → OK
2. A project appears in the event; double-click to open the timeline
3. Red frames = offline media: select clips → File → Relink Files → point at sources
4. Connected-candidate review (dimmed clips floating above): keep → select, press V (enable), drag into the primary storyline as needed; discard → Delete
5. BGM/captions after candidates settle

## Common problems
| Symptom | Cause | Fix |
|---|---|---|
| "Cannot read XML" | rational times not frame multiples | verify cutlist fps equals probe measurement |
| Media offline | path mismatch | regenerate with absolute paths, or Relink Files |
| Candidates invisible | connected clips off-screen | expand timeline vertically, or search by clip name in the Index (⌘⇧2) |
| Project missing after import | landed in another library | check events under all open libraries in the sidebar |
