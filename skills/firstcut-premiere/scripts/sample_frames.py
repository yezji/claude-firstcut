#!/usr/bin/env python3
"""Sample frames from silent spans so Claude can judge them visually —
token-efficiently.

Silence-based cutting is blind to visually meaningful content (B-roll,
product shots, scenery, demonstrations). Long silent spans must be LOOKED AT
before any cut decision. But frames cost tokens (~300 each at 640px), so:

DEFAULT = CONTACT SHEET: one middle frame per span, tiled into a labeled
grid image (up to 9 spans per sheet, ~700 tokens). Triage the whole video
in one or two images.

ESCALATE ONLY WHEN AMBIGUOUS: --span START END pulls first/middle/last
frames (3 images) for a single span that the sheet couldn't settle.

Usage:
  # triage all long silences in one sheet (default flow)
  python sample_frames.py video.mp4 --from-transcript transcript.json \\
      --min-dur 3.0 -o frames/

  # detailed look at one ambiguous span
  python sample_frames.py video.mp4 --span 42.0 51.5 -o frames/
"""
import argparse, json, os, subprocess, sys, tempfile


def extract(media, t, out, width):
    cmd = ["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", media, "-frames:v", "1",
           "-vf", f"scale={width}:-2", "-q:v", "5", out]
    r = subprocess.run(cmd, capture_output=True)
    return r.returncode == 0 and os.path.exists(out)


def ensure_pillow():
    try:
        from PIL import Image, ImageDraw  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pillow",
                        "--break-system-packages", "-q"], check=True)


def contact_sheet(media, spans, outdir, cols=3, cell_w=320):
    """One middle frame per span, tiled with index+timecode labels.
    Returns list of sheet paths (9 spans per sheet)."""
    ensure_pillow()
    from PIL import Image, ImageDraw
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(media))[0]
    sheets, legend = [], []
    per_sheet = cols * cols
    with tempfile.TemporaryDirectory() as td:
        cells = []
        for i, (a, b) in enumerate(spans):
            mid = a + (b - a) / 2
            cell = os.path.join(td, f"c{i}.jpg")
            if extract(media, mid, cell, cell_w):
                cells.append((i, a, b, cell))
        for s0 in range(0, len(cells), per_sheet):
            chunk = cells[s0:s0 + per_sheet]
            imgs = [Image.open(c[3]) for c in chunk]
            ch = max(im.height for im in imgs)
            rows = (len(chunk) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * cell_w, rows * (ch + 18)), "black")
            draw = ImageDraw.Draw(sheet)
            for j, ((idx, a, b, _), im) in enumerate(zip(chunk, imgs)):
                x, y = (j % cols) * cell_w, (j // cols) * (ch + 18)
                sheet.paste(im, (x, y + 18))
                label = f"#{idx + 1}  {a:.0f}-{b:.0f}s ({b - a:.0f}s)"
                draw.text((x + 4, y + 3), label, fill="white")
                legend.append({"index": idx + 1, "start": a, "end": b})
            out = os.path.join(outdir, f"{base}_sheet{s0 // per_sheet + 1}.jpg")
            sheet.save(out, quality=85)
            sheets.append(out)
    return sheets, legend


def span_detail(media, start, end, outdir, width=640):
    """3 frames (first/middle/last) for one ambiguous span."""
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(media))[0]
    dur = max(0.0, end - start)
    inset = min(0.3, dur / 4)
    paths = []
    for i, t in enumerate([start + inset, start + dur / 2, end - inset]):
        out = os.path.join(outdir, f"{base}_{start:.1f}s_{i}.jpg")
        if extract(media, t, out, width):
            paths.append(out)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--from-transcript",
                    help="transcript.json with 'silences'; sheet-triage them all")
    ap.add_argument("--min-dur", type=float, default=3.0)
    ap.add_argument("--span", nargs=2, type=float, metavar=("START", "END"),
                    help="detailed 3-frame look at one span")
    ap.add_argument("-o", "--outdir", default="frames")
    args = ap.parse_args()

    if args.span:
        paths = span_detail(args.media, args.span[0], args.span[1], args.outdir)
        print(f"[{args.span[0]:.1f}-{args.span[1]:.1f}s] -> {len(paths)} frames")
        for p in paths:
            print(f"    {p}")
    elif args.from_transcript:
        data = json.load(open(args.from_transcript, encoding="utf-8"))
        spans = [(s["start"], s["end"]) for s in data.get("silences", [])
                 if s["end"] - s["start"] >= args.min_dur]
        if not spans:
            print(f"No silences >= {args.min_dur}s.")
            sys.exit(0)
        sheets, legend = contact_sheet(args.media, spans, args.outdir)
        json.dump(legend, open(os.path.join(args.outdir, "legend.json"), "w"),
                  indent=2)
        print(f"{len(spans)} silent spans -> {len(sheets)} contact sheet(s):")
        for s in sheets:
            print(f"    {s}")
        print(f"legend: {os.path.join(args.outdir, 'legend.json')}")
        print("View the sheet(s); escalate ambiguous spans with --span START END.")
    else:
        sys.exit("Provide --from-transcript or --span START END.")
