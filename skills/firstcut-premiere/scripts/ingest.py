#!/usr/bin/env python3
"""Scan a source folder and emit a cutlist-ready sources block.

Usage: python ingest.py /path/to/footage -o sources.json

- Collects video files (mp4/mov/mkv/avi/mxf/m4v) in filename order
- Probes each (ffprobe) for fps/resolution/duration/audio tracks
- Records absolute paths -> media auto-links on XML import (no relink)
- Reports warnings: fps mismatch, multiple audio tracks
"""
import argparse, json, os, sys
from probe import probe

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".mxf", ".m4v", ".mts", ".webm"}


def ingest(folder):
    folder = os.path.abspath(os.path.expanduser(folder))
    if not os.path.isdir(folder):
        sys.exit(f"Folder not found: {folder}")
    files = sorted(f for f in os.listdir(folder)
                   if os.path.splitext(f)[1].lower() in VIDEO_EXT
                   and not f.startswith("."))
    if not files:
        sys.exit(f"No video files found in {folder}. "
                 f"(supported: {', '.join(sorted(VIDEO_EXT))})")

    sources, warnings = [], []
    for i, f in enumerate(files):
        path = os.path.join(folder, f)
        try:
            info = probe(path)
        except Exception as e:
            warnings.append(f"{f}: probe failed, skipped ({e})")
            continue
        sid = f"s{i + 1}"
        sources.append({"id": sid, "path": path, "name": f,
                        "fps": info.get("fps"), "width": info.get("width"),
                        "height": info.get("height"),
                        "duration_sec": info["duration_sec"],
                        "audio_sample_rate": info.get("audio_sample_rate", 48000),
                        "audio_channels": info.get("audio_channels", 2)})
        if info["audio_track_count"] > 1:
            warnings.append(f"{f}: {info['audio_track_count']} audio tracks - "
                            "XML import may only see the first")

    fps_set = {s["fps"] for s in sources if s.get("fps")}
    if len(fps_set) > 1:
        warnings.append(f"fps differs across files: {sorted(fps_set)} - "
                        "sequence follows the first; the NLE conforms the rest")

    return {"folder": folder, "sources": sources, "warnings": warnings}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("-o", "--output", default="sources.json")
    args = ap.parse_args()
    result = ingest(args.folder)
    json.dump(result, open(args.output, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    total = sum(s["duration_sec"] for s in result["sources"])
    print(f"Found {len(result['sources'])} videos, {round(total / 60, 1)} min total:")
    for s in result["sources"]:
        print(f"  [{s['id']}] {s['name']} — {round(s['duration_sec'], 1)}s, "
              f"{s['fps']}fps, {s['width']}x{s['height']}")
    for w in result["warnings"]:
        print(f"  [WARN] {w}", file=sys.stderr)
