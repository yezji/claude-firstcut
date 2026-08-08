#!/usr/bin/env python3
"""cutlist.json -> FCP7 XML (xmeml v4) for Premiere Pro import.

Usage: python build_xml.py cutlist.json -o rough_cut.xml

Single/multi source both supported:
  single: "source": {...}                (legacy, backward compatible)
  multi : "sources": [{"id": "a", ...}]  + per-segment "source": "a"

Tracks:
  V1 : decision=="keep" clips back to back
       (timeline order = segment list order; cross-file rearrangement OK)
  V2 : decision=="candidate" clips above their related V1 cut point,
       <enabled>FALSE</enabled>, name "[keep?] label - reason"
  A1 : audio cut identically to V1, linked to video

NTSC-family fps (23.976/29.97/59.94) written as timebase+ntsc=TRUE with
sec->frame conversion at the true ratio (timebase*1000/1001).
User-visible literals (clip names, sequence name) stay Korean by design.
"""
import argparse, json, sys
from xml.sax.saxutils import escape
from urllib.request import pathname2url


def rate_info(fps):
    for tb in (24, 25, 30, 50, 60):
        if abs(fps - tb) < 0.005:
            return tb, False, float(tb)
        if abs(fps - tb * 1000 / 1001) < 0.005:
            return tb, True, tb * 1000 / 1001
    tb = round(fps)
    return tb, False, float(tb)


def to_frames(sec, true_fps):
    return int(round(sec * true_fps))


def normalize_sources(cutlist):
    """Normalize single source / multi sources into {id: source_dict}."""
    if "sources" in cutlist:
        srcs = {s["id"]: s for s in cutlist["sources"]}
        default_id = cutlist["sources"][0]["id"]
    elif "source" in cutlist:
        srcs = {"main": cutlist["source"]}
        default_id = "main"
    else:
        sys.exit("cutlist has no source or sources.")
    return srcs, default_id


def apply_margin_and_merge(keeps, margin, srcs):
    """Add margin to keeps; merge overlapping adjacent spans of the same source."""
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
    sr = int(seq_src.get("audio_sample_rate", 48000))
    margin = float(cutlist.get("margin_sec", 0.2))
    seq_name = cutlist.get("sequence_name", "초벌컷")
    ntsc_s = "TRUE" if ntsc else "FALSE"

    for sid, s in srcs.items():
        if abs(float(s["fps"]) - fps) > 0.01:
            print(f"[WARN] source '{sid}' fps ({s['fps']}) differs from sequence fps ({fps}). "
                  f"The NLE will conform it, but verify.", file=sys.stderr)

    segs = [dict(s, source=s.get("source", default_id)) for s in cutlist["segments"]]
    keeps = apply_margin_and_merge(
        [s for s in segs if s["decision"] == "keep"], margin, srcs)
    cands = [s for s in segs if s["decision"] == "candidate"]
    if not keeps:
        sys.exit("No keep segments. Check cutlist.json.")

    RATE = f"<rate><timebase>{tb}</timebase><ntsc>{ntsc_s}</ntsc></rate>"
    file_defined = set()

    def file_el(sid):
        src = srcs[sid]
        fid = f"file-{sid}"
        if sid in file_defined:
            return f'<file id="{fid}"/>'
        file_defined.add(sid)
        path = src["path"]
        url = "file://localhost" + pathname2url(path) if path.startswith("/") \
              else "file://localhost/" + pathname2url(path).lstrip("/")
        sdur = to_frames(float(src["duration_sec"]), true_fps)
        return (f'<file id="{fid}"><name>{escape(src["name"])}</name>'
                f'<pathurl>{escape(url)}</pathurl>{RATE}'
                f'<duration>{sdur}</duration>'
                f'<media><video><samplecharacteristics>{RATE}'
                f'<width>{int(src.get("width", width))}</width>'
                f'<height>{int(src.get("height", height))}</height>'
                f'<anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio>'
                f'</samplecharacteristics></video>'
                f'<audio><samplecharacteristics><depth>16</depth>'
                f'<samplerate>{int(src.get("audio_sample_rate", sr))}</samplerate>'
                f'</samplecharacteristics>'
                f'<channelcount>{int(src.get("audio_channels", 2))}</channelcount>'
                f'</audio></media></file>')

    def clipitem(cid, name, sid, tl_start, tl_end, src_in, src_out, enabled,
                 media="video", link_ids=None, comment=""):
        parts = [f'<clipitem id="{cid}">',
                 f'<name>{escape(name)}</name>',
                 f'<enabled>{"TRUE" if enabled else "FALSE"}</enabled>',
                 f'<duration>{src_out - src_in}</duration>', RATE,
                 f'<start>{tl_start}</start><end>{tl_end}</end>',
                 f'<in>{src_in}</in><out>{src_out}</out>',
                 file_el(sid)]
        if media == "audio":
            parts.append('<sourcetrack><mediatype>audio</mediatype>'
                         '<trackindex>1</trackindex></sourcetrack>')
        if comment:
            parts.append(f'<comments><mastercomment1>{escape(comment)}'
                         f'</mastercomment1></comments>')
        for lid in (link_ids or []):
            parts.append(f'<link><linkclipref>{lid}</linkclipref></link>')
        parts.append('</clipitem>')
        return "".join(parts)

    # --- V1 + A1 ---
    v1_items, a1_items = [], []
    playhead = 0
    junctions = []  # (source_id, source_start_sec, timeline_start_frame)
    multi = len(srcs) > 1
    for i, k in enumerate(keeps):
        sin, sout = to_frames(k["start"], true_fps), to_frames(k["end"], true_fps)
        if sout <= sin:
            continue
        length = sout - sin
        vid, aid = f"clip-v1-{i}", f"clip-a1-{i}"
        base = k.get("label") or k.get("text", "")[:20] or f"컷 {i + 1}"
        name = f"[{k['source']}] {base}" if multi else base
        junctions.append((k["source"], k["start"], playhead))
        v1_items.append(clipitem(vid, name, k["source"], playhead, playhead + length,
                                 sin, sout, True, "video", [vid, aid]))
        a1_items.append(clipitem(aid, name, k["source"], playhead, playhead + length,
                                 sin, sout, True, "audio", [vid, aid]))
        playhead += length
    total_f = playhead

    # --- V2 ---
    def junction_frame(sid, cand_start_sec):
        """Timeline position of the first same-source keep after the candidate = insertion point.
        No same-source keep -> end of timeline."""
        last_same = None
        for (ksid, kstart, tl) in junctions:
            if ksid != sid:
                continue
            if kstart >= cand_start_sec:
                return tl
            last_same = tl
        return total_f if last_same is None else last_same

    v2_items = []
    for j, c in enumerate(cands):
        sin, sout = to_frames(c["start"], true_fps), to_frames(c["end"], true_fps)
        if sout <= sin:
            continue
        length = sout - sin
        tl = max(0, min(junction_frame(c["source"], c["start"]), total_f - length))
        base = c.get("label") or c.get("text", "")[:15] or "후보"
        label = f"[{c['source']}] {base}" if multi else base
        name = f"[keep?] {label}" + (f" - {c['reason']}" if c.get("reason") else "")
        v2_items.append(clipitem(f"clip-v2-{j}", name, c["source"], tl, tl + length,
                                 sin, sout, False, "video",
                                 comment=c.get("reason", "")))

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
<sequence id="sequence-1">
<name>{escape(seq_name)}</name>
<duration>{total_f}</duration>
{RATE}
<timecode>{RATE}<string>00:00:00:00</string><frame>0</frame>
<displayformat>{"DF" if ntsc else "NDF"}</displayformat></timecode>
<media>
<video>
<format><samplecharacteristics>{RATE}
<width>{width}</width><height>{height}</height>
<anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio>
</samplecharacteristics></format>
<track>{"".join(v1_items)}<enabled>TRUE</enabled><locked>FALSE</locked></track>
<track>{"".join(v2_items)}<enabled>TRUE</enabled><locked>FALSE</locked></track>
</video>
<audio>
<format><samplecharacteristics><depth>16</depth><samplerate>{sr}</samplerate>
</samplecharacteristics></format>
<track>{"".join(a1_items)}<enabled>TRUE</enabled><locked>FALSE</locked></track>
</audio>
</media>
</sequence>
</xmeml>"""

    total_src = sum(float(s["duration_sec"]) for s in srcs.values())
    stats = {"keep_clips": len(v1_items), "candidates": len(v2_items),
             "sources": len(srcs),
             "timeline_sec": round(total_f / true_fps, 1),
             "source_sec": round(total_src, 1)}
    return xml, stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlist")
    ap.add_argument("-o", "--output", default="rough_cut.xml")
    args = ap.parse_args()
    cutlist = json.load(open(args.cutlist, encoding="utf-8"))
    xml, stats = build(cutlist)
    open(args.output, "w", encoding="utf-8").write(xml)
    print(f"{args.output} written")
    print(f"  {stats['sources']} sources / {stats['keep_clips']} confirmed clips "
          f"/ {stats['candidates']} V2 candidates")
    print(f"  sources total {stats['source_sec']}s -> timeline {stats['timeline_sec']}s")
