#!/usr/bin/env python3
"""Remap subtitle timecodes to the locked, edited timeline -> final SRT.

Principle: cutlist.json knows exactly which source spans went where on the
timeline. Intersect each subtitle with the keep spans and shift into timeline time.
- Subtitles entirely inside cut regions -> dropped
- Boundary-straddling subtitles -> trimmed to the overlap (split if needed)
- If candidates were promoted in the NLE: first flip those decisions to keep
  in the cutlist (sync cutlist with the real timeline), then run this.

Usage:
  single source: python remap_subs.py cutlist.json --srt subs.srt -o final_subs.srt
  multi source : python remap_subs.py cutlist.json --srt s1=subs_s1.srt --srt s2=subs_s2.srt -o final_subs.srt
"""
import argparse, json, re, sys

TIME_RE = re.compile(r"(\d+):(\d+):(\d+)[.,](\d+)")


def ts_to_sec(ts):
    h, m, s, ms = TIME_RE.match(ts).groups()
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def sec_to_ts(sec):
    sec = max(0.0, sec)
    h = int(sec // 3600); m = int(sec % 3600 // 60)
    s = int(sec % 60); ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(path):
    text = open(path, encoding="utf-8-sig").read()
    entries = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        tline = next((l for l in lines if "-->" in l), None)
        if not tline:
            continue
        a, b = [p.strip().split(" ")[0] for p in tline.split("-->")]
        content = "\n".join(lines[lines.index(tline) + 1:]).strip()
        if content:
            entries.append((ts_to_sec(a), ts_to_sec(b), content))
    return entries


def normalize_sources(cutlist):
    if "sources" in cutlist:
        return {s["id"]: s for s in cutlist["sources"]}, cutlist["sources"][0]["id"]
    if "source" in cutlist:
        return {"main": cutlist["source"]}, "main"
    sys.exit("cutlist has no source/sources")


def apply_margin_and_merge(keeps, margin, srcs):
    """Identical to build_xml/build_fcpxml — must match exactly or timecodes drift."""
    expanded = []
    for s in keeps:
        max_sec = float(srcs[s["source"]]["duration_sec"])
        a, b = max(0.0, s["start"] - margin), min(max_sec, s["end"] + margin)
        prev = expanded[-1] if expanded else None
        if prev and prev["source"] == s["source"] and a <= prev["end"] \
                and s["start"] >= prev["start"]:
            prev["end"] = max(prev["end"], b)
        else:
            expanded.append({**s, "start": a, "end": b})
    return expanded


def remap(cutlist, subs_by_source, min_dur=0.3):
    srcs, default_id = normalize_sources(cutlist)
    margin = float(cutlist.get("margin_sec", 0.2))
    segs = [dict(s, source=s.get("source", default_id))
            for s in cutlist["segments"]]
    keeps = apply_margin_and_merge(
        [s for s in segs if s["decision"] == "keep"], margin, srcs)

    # timeline mapping table: (source_id, src_start, src_end, tl_start)
    table, playhead = [], 0.0
    for k in keeps:
        length = k["end"] - k["start"]
        table.append((k["source"], k["start"], k["end"], playhead))
        playhead += length

    out = []
    for sid, entries in subs_by_source.items():
        for (s, e, text) in entries:
            for (ksid, a, b, tl) in table:
                if ksid != sid:
                    continue
                os_, oe = max(s, a), min(e, b)
                if oe - os_ >= min_dur:
                    out.append((tl + (os_ - a), tl + (oe - a), text))
    out.sort(key=lambda x: x[0])

    # merge same-text fragments that ended up adjacent
    merged = []
    for item in out:
        if merged and merged[-1][2] == item[2] and item[0] - merged[-1][1] < 0.1:
            merged[-1] = (merged[-1][0], item[1], item[2])
        else:
            merged.append(list(item))
    return merged, playhead


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlist")
    ap.add_argument("--srt", action="append", required=True,
                    help="subs.srt or source_id=subs.srt (repeat for multi-source)")
    ap.add_argument("-o", "--output", default="final_subs.srt")
    ap.add_argument("--min-dur", type=float, default=0.3,
                    help="discard remapped fragments shorter than this (default 0.3s)")
    args = ap.parse_args()

    cutlist = json.load(open(args.cutlist, encoding="utf-8"))
    _, default_id = normalize_sources(cutlist)
    subs = {}
    for spec in args.srt:
        if "=" in spec:
            sid, path = spec.split("=", 1)
        else:
            sid, path = default_id, spec
        subs[sid] = parse_srt(path)

    entries, total = remap(cutlist, subs, args.min_dur)
    with open(args.output, "w", encoding="utf-8") as f:
        for i, (a, b, t) in enumerate(entries, 1):
            f.write(f"{i}\n{sec_to_ts(a)} --> {sec_to_ts(b)}\n{t}\n\n")
    print(f"{args.output}: {len(entries)} subtitles (timeline {round(total, 1)}s)")
