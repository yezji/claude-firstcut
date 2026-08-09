#!/usr/bin/env python3
"""Apply confirmed term corrections consistently across transcript + subtitles.

Division of labor: DETECTING mis-recognitions (phonetic variants of names,
garbled brand terms) is LLM-strength work — Claude spots them and confirms
canonical spellings with the user. APPLYING the confirmed corrections must be
deterministic and exhaustive — that is this script's job.

Usage:
  # corrections as wrong=right pairs
  python apply_glossary.py --fix "새훈=세훈" --fix "아이자벨 마랑=이자벨 마랑" \\
      transcript.json subs.srt

  # or from a JSON map {"wrong": "right", ...}
  python apply_glossary.py --fix-file corrections.json transcript.json subs.srt final_subs.srt

Behavior:
- transcript.json: replaces in segments[].text and words[].w
- .srt/.vtt files: replaces in cue text lines only (never timecodes)
- Longer wrong-strings are applied first (avoids partial-overlap mangling)
- Prints per-term replacement counts; warns on zero-hit terms
- Writes corrections.json next to the first input for reuse (re-runs, /firstcut-subs)
"""
import argparse, json, os, re, sys


def apply_to_text(text, fixes, counts):
    for wrong, right in fixes:
        n = text.count(wrong)
        if n:
            text = text.replace(wrong, right)
            counts[wrong] = counts.get(wrong, 0) + n
    return text


def process_transcript(path, fixes, counts):
    data = json.load(open(path, encoding="utf-8"))
    for seg in data.get("segments", []):
        seg["text"] = apply_to_text(seg["text"], fixes, counts)
        for w in seg.get("words", []):
            w["w"] = apply_to_text(w["w"], fixes, counts)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def process_srt(path, fixes, counts):
    lines = open(path, encoding="utf-8-sig").read().splitlines()
    out = []
    for line in lines:
        # never touch timecode or index lines
        if "-->" in line or re.fullmatch(r"\s*\d+\s*", line or " "):
            out.append(line)
        else:
            out.append(apply_to_text(line, fixes, counts))
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+",
                    help="transcript.json and/or .srt/.vtt files to correct in place")
    ap.add_argument("--fix", action="append", default=[],
                    help="wrong=right (repeatable)")
    ap.add_argument("--fix-file", help='JSON map {"wrong": "right", ...}')
    args = ap.parse_args()

    fixes = {}
    if args.fix_file:
        fixes.update(json.load(open(args.fix_file, encoding="utf-8")))
    for pair in args.fix:
        if "=" not in pair:
            sys.exit(f"Bad --fix (need wrong=right): {pair}")
        wrong, right = pair.split("=", 1)
        fixes[wrong.strip()] = right.strip()
    if not fixes:
        sys.exit("No corrections given (--fix or --fix-file).")

    # longest-first prevents partial overlaps ("세 훈" before "훈")
    ordered = sorted(fixes.items(), key=lambda kv: -len(kv[0]))
    counts = {}
    for f in args.files:
        if not os.path.exists(f):
            print(f"[WARN] missing, skipped: {f}", file=sys.stderr)
            continue
        if f.endswith(".json"):
            process_transcript(f, ordered, counts)
        else:
            process_srt(f, ordered, counts)
        print(f"corrected: {f}")

    print("\nReplacement counts:")
    for wrong, right in ordered:
        n = counts.get(wrong, 0)
        flag = "" if n else "   <- zero hits, check spelling"
        print(f"  {wrong} -> {right}: {n}{flag}")

    save = os.path.join(os.path.dirname(os.path.abspath(args.files[0])),
                        "corrections.json")
    json.dump(fixes, open(save, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nsaved map for reuse: {save}")
