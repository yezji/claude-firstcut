#!/usr/bin/env python3
"""cutlist.json -> FCPXML for Final Cut Pro.

Usage: python build_fcpxml.py cutlist.json -o rough_cut.fcpxml

Same cutlist format as the Premiere edition (single source / multi sources).

Final Cut mapping:
  Spine (primary storyline) : decision=="keep" clips in order
  Connected clips (lane=1)  : decision=="candidate", attached to the clip
                              at the related cut point with enabled="0"
                              (dimmed, excluded from playback);
                              name "[keep?] label - reason"
  Audio                     : asset-clips reference video+audio together
                              (no separate track)

Times are FCPXML rational seconds: NTSC 29.97 -> frameDuration 1001/30000s;
all timestamps are exact multiples of the frame duration (imports are
rejected otherwise). On macOS, `open file.fcpxml` imports directly.
User-visible literals (clip names, project name) stay Korean by design.
"""
import argparse, json, sys
from xml.sax.saxutils import escape, quoteattr
from urllib.request import pathname2url


def rate_info(fps):
    for tb in (24, 25, 30, 50, 60):
        if abs(fps - tb) < 0.005:
            return tb, False, float(tb)
        if abs(fps - tb * 1000 / 1001) < 0.005:
            return tb, True, tb * 1000 / 1001
    tb = round(fps)
    return tb, False, float(tb)


def normalize_sources(cutlist):
    if "sources" in cutlist:
        return {s["id"]: s for s in cutlist["sources"]}, cutlist["sources"][0]["id"]
    if "source" in cutlist:
        return {"main": cutlist["source"]}, "main"
    sys.exit("cutlist has no source or sources.")


def apply_margin_and_merge(keeps, margin, srcs):
    expanded = []
    for s in keeps:
        max_sec = float(srcs[s["source"]]["duration_sec"])
        a, b = max(0.0, s["start"] - margin), min(max_sec, s["end"] + margin)
        prev = expanded[-1] if expanded else None
        if prev and prev["source"] == s["source"] and a <= prev["end"] \
                and s["start"] >= prev["start"]:
            prev["end"] = max(prev["end"], b)
            if s.get("label"):
                prev["label"] = prev.get("label") or s["label"]
        else:
            expanded.append({**s, "start": a, "end": b})
    return expanded


def build(cutlist):
    srcs, default_id = normalize_sources(cutlist)
    seq_src = srcs[cutlist.get("sequence_source", default_id)]
    fps = float(seq_src["fps"])
    tb, ntsc, true_fps = rate_info(fps)
    width, height = int(seq_src.get("width", 1920)), int(seq_src.get("height", 1080))
    margin = float(cutlist.get("margin_sec", 0.2))
    proj_name = cutlist.get("sequence_name", "초벌컷")

    num_unit = 1001 if ntsc else 1
    den = tb * 1000 if ntsc else tb

    def frames(sec):
        return int(round(sec * true_fps))

    def t(fr):
        """frame count -> FCPXML rational-second string"""
        n = fr * num_unit
        if n == 0:
            return "0s"
        return f"{n}/{den}s"

    frame_dur = f"{num_unit}/{den}s"

    segs = [dict(s, source=s.get("source", default_id)) for s in cutlist["segments"]]
    keeps = apply_margin_and_merge(
        [s for s in segs if s["decision"] == "keep"], margin, srcs)
    cands = [s for s in segs if s["decision"] == "candidate"]
    if not keeps:
        sys.exit("No keep segments.")

    # --- resources ---
    fmt_name = f"FFVideoFormat{height}p{str(fps).replace('.', '')}" if ntsc \
               else f"FFVideoFormat{height}p{tb}"
    res = [f'<format id="r1" name={quoteattr(fmt_name)} '
           f'frameDuration="{frame_dur}" width="{width}" height="{height}"/>']
    asset_ids = {}
    for i, (sid, src) in enumerate(srcs.items()):
        aid = f"a{i + 1}"
        asset_ids[sid] = aid
        path = src["path"]
        url = "file://" + pathname2url(path) if path.startswith("/") \
              else "file:///" + pathname2url(path).lstrip("/")
        sdur = frames(float(src["duration_sec"]))
        ch = int(src.get("audio_channels", 2))
        sr = int(src.get("audio_sample_rate", 48000))
        res.append(
            f'<asset id="{aid}" name={quoteattr(src["name"])} start="0s" '
            f'duration="{t(sdur)}" hasVideo="1" hasAudio="1" format="r1" '
            f'audioSources="1" audioChannels="{ch}" audioRate="{sr}">'
            f'<media-rep kind="original-media" src={quoteattr(url)}/></asset>')

    # --- spine + connected candidates ---
    multi = len(srcs) > 1

    # compute each candidate's insertion point (before the next same-source keep)
    playhead = 0
    keep_meta = []  # (keep dict, tl_start_frame, length)
    for k in keeps:
        sin, sout = frames(k["start"]), frames(k["end"])
        if sout <= sin:
            continue
        keep_meta.append((k, playhead, sout - sin))
        playhead += sout - sin
    total_f = playhead

    def anchor_index(sid, cand_start_sec):
        """Index of the keep clip a candidate attaches to: first same-source keep
        after it; else the last same-source keep; else the first clip."""
        last_same = None
        for idx, (k, _, _) in enumerate(keep_meta):
            if k["source"] != sid:
                continue
            if k["start"] >= cand_start_sec:
                return idx
            last_same = idx
        return last_same if last_same is not None else 0

    attached = {i: [] for i in range(len(keep_meta))}
    for c in cands:
        sin, sout = frames(c["start"]), frames(c["end"])
        if sout <= sin:
            continue
        attached[anchor_index(c["source"], c["start"])].append((c, sin, sout))

    spine = []
    for i, (k, tl, length) in enumerate(keep_meta):
        sin = frames(k["start"])
        base = k.get("label") or k.get("text", "")[:20] or f"컷 {i + 1}"
        name = f"[{k['source']}] {base}" if multi else base
        inner = []
        for (c, csin, csout) in attached[i]:
            cbase = c.get("label") or c.get("text", "")[:15] or "후보"
            clabel = f"[{c['source']}] {cbase}" if multi else cbase
            cname = f"[keep?] {clabel}" + (f" - {c['reason']}" if c.get("reason") else "")
            # connected-clip offset is in the parent's source time: attach at the parent's start
            inner.append(
                f'<asset-clip ref="{asset_ids[c["source"]]}" lane="1" '
                f'offset="{t(sin)}" name={quoteattr(cname)} start="{t(csin)}" '
                f'duration="{t(csout - csin)}" format="r1" enabled="0" '
                f'audioRole="dialogue">'
                f'<note>{escape(c.get("reason", ""))}</note></asset-clip>')
        spine.append(
            f'<asset-clip ref="{asset_ids[k["source"]]}" offset="{t(tl)}" '
            f'name={quoteattr(name)} start="{t(sin)}" duration="{t(length)}" '
            f'format="r1" audioRole="dialogue">{"".join(inner)}</asset-clip>')

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
<resources>
{chr(10).join(res)}
</resources>
<library>
<event name={quoteattr(proj_name)}>
<project name={quoteattr(proj_name)}>
<sequence format="r1" duration="{t(total_f)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
<spine>
{chr(10).join(spine)}
</spine>
</sequence>
</project>
</event>
</library>
</fcpxml>"""

    total_src = sum(float(s["duration_sec"]) for s in srcs.values())
    stats = {"keep_clips": len(keep_meta),
             "candidates": sum(len(v) for v in attached.values()),
             "sources": len(srcs),
             "timeline_sec": round(total_f / true_fps, 1),
             "source_sec": round(total_src, 1)}
    return xml, stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlist")
    ap.add_argument("-o", "--output", default="rough_cut.fcpxml")
    args = ap.parse_args()
    cutlist = json.load(open(args.cutlist, encoding="utf-8"))
    xml, stats = build(cutlist)
    open(args.output, "w", encoding="utf-8").write(xml)
    print(f"{args.output} written")
    print(f"  {stats['sources']} sources / {stats['keep_clips']} confirmed clips "
          f"/ {stats['candidates']} connected candidates")
    print(f"  sources total {stats['source_sec']}s -> timeline {stats['timeline_sec']}s")
