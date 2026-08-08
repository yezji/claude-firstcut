#!/usr/bin/env python3
"""Print a video's fps/resolution/duration/audio-track count as JSON.

Usage: python probe.py <video> [-o media_info.json]
"""
import argparse, json, subprocess, sys


def probe(path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", path]
    data = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)

    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio_streams = [s for s in data["streams"] if s["codec_type"] == "audio"]

    info = {"path": path, "duration_sec": float(data["format"].get("duration", 0)),
            "audio_track_count": len(audio_streams)}
    if video:
        num, den = (int(x) for x in video["r_frame_rate"].split("/"))
        fps = num / den
        info.update({"width": int(video["width"]), "height": int(video["height"]),
                     "fps": round(fps, 3),
                     "is_ntsc": den == 1001 or abs(fps - round(fps)) > 0.01})
    if audio_streams:
        info["audio_sample_rate"] = int(audio_streams[0].get("sample_rate", 48000))
        info["audio_channels"] = int(audio_streams[0].get("channels", 2))
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()
    info = probe(args.input)
    out = json.dumps(info, ensure_ascii=False, indent=2)
    if args.output:
        open(args.output, "w").write(out)
    print(out)
    if info["audio_track_count"] > 1:
        print(f"\n[WARN] {info['audio_track_count']} audio tracks. "
              "NLE XML import may only recognize the first.", file=sys.stderr)
