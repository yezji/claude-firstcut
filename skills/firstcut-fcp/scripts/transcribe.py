#!/usr/bin/env python3
"""Generate transcript.json (+ subtitle SRT).

Default path: Claude transcribes directly.
  1) faster-whisper (default; auto-installs if missing):
     python transcribe.py video.mp4 --language ko -o transcript.json --srt-out subs.srt
  2) srt/vtt parsing (fallback when model download is blocked; e.g. NLE auto-transcribe output):
     python transcribe.py --srt subs.srt -o transcript.json
  3) silence detection only (ffmpeg silencedetect — Ambar layer 1):
     python transcribe.py video.mp4 --silence-only -o silence.json

--srt-out also writes the transcript as a subtitle SRT (for NLE caption import).
Model download requires huggingface.co; if blocked, a clear remedy message is
printed and the script exits.
"""
import argparse, json, re, subprocess, sys, tempfile, os

TIME_RE = re.compile(r"(\d+):(\d+):(\d+)[.,](\d+)")


def ts_to_sec(ts):
    h, m, s, ms = TIME_RE.match(ts).groups()
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def parse_srt(path):
    text = open(path, encoding="utf-8-sig").read()
    segments = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        # skip WEBVTT header/index lines; find the timecode line
        tline = next((l for l in lines if "-->" in l), None)
        if not tline:
            continue
        start_s, end_s = [p.strip().split(" ")[0] for p in tline.split("-->")]
        content = " ".join(lines[lines.index(tline) + 1:]).strip()
        if not content:
            continue
        segments.append({"id": len(segments), "start": round(ts_to_sec(start_s), 3),
                         "end": round(ts_to_sec(end_s), 3), "text": content, "words": []})
    return segments


def detect_silences(media, threshold_db=-35, min_dur=0.8):
    cmd = ["ffmpeg", "-i", media, "-af",
           f"silencedetect=noise={threshold_db}dB:d={min_dur}", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    silences, start = [], None
    for line in out.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and start is not None:
            silences.append({"start": round(start, 3), "end": round(float(m.group(1)), 3),
                             "dur": round(float(m.group(2)), 3)})
            start = None
    return silences


def whisper_transcribe(media, language=None, model_size="small", vocab=None):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Installing faster-whisper...", file=sys.stderr)
        r = subprocess.run([sys.executable, "-m", "pip", "install",
                            "faster-whisper", "--break-system-packages", "-q"])
        if r.returncode != 0:
            sys.exit("faster-whisper install failed. Check pypi.org access in network settings.")
        from faster_whisper import WhisperModel
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "audio.wav")
        subprocess.run(["ffmpeg", "-y", "-i", media, "-ac", "1", "-ar", "16000", wav],
                       capture_output=True, check=True)
        try:
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except Exception as e:
            sys.exit(
                "Whisper model download failed (huggingface.co likely blocked).\n"
                "Two remedies:\n"
                "  1) Add huggingface.co to allowed domains in network egress settings, then retry\n"
                "  2) Provide an SRT from the NLE auto-transcribe via --srt\n"
                f"Original error: {e}")
        kwargs = dict(language=language, word_timestamps=True, vad_filter=True)
        if vocab:
            # Bias decoding toward domain terms: initial_prompt is broadly
            # supported; hotwords exists on newer faster-whisper builds.
            prompt = "다음 용어가 등장할 수 있다: " + ", ".join(vocab)
            kwargs["initial_prompt"] = prompt
            try:
                segs, _ = model.transcribe(wav, hotwords=" ".join(vocab), **kwargs)
            except TypeError:  # hotwords unsupported on this version
                segs, _ = model.transcribe(wav, **kwargs)
        else:
            segs, _ = model.transcribe(wav, **kwargs)
        segments = []
        for s in segs:
            words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
                     for w in (s.words or [])]
            segments.append({"id": len(segments), "start": round(s.start, 3),
                             "end": round(s.end, 3), "text": s.text.strip(), "words": words})
        return segments


def sec_to_ts(sec):
    h = int(sec // 3600); m = int(sec % 3600 // 60)
    s = int(sec % 60); ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments, path, max_chars=22):
    """Transcript segments -> subtitle SRT. Long sentences split at word timestamps.
    max_chars: recommended line length for on-screen readability (Korean)."""
    entries = []
    for seg in segments:
        words = seg.get("words") or []
        if len(seg["text"]) <= max_chars or len(words) < 2:
            entries.append((seg["start"], seg["end"], seg["text"]))
            continue
        chunk, cstart = [], None
        for w in words:
            if cstart is None:
                cstart = w["s"]
            chunk.append(w["w"])
            if len(" ".join(chunk)) >= max_chars:
                entries.append((cstart, w["e"], " ".join(chunk)))
                chunk, cstart = [], None
        if chunk:
            entries.append((cstart, words[-1]["e"], " ".join(chunk)))
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, t) in enumerate(entries, 1):
            f.write(f"{i}\n{sec_to_ts(a)} --> {sec_to_ts(b)}\n{t}\n\n")
    return len(entries)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("media", nargs="?", help="video/audio file (for silence detection and whisper)")
    ap.add_argument("--srt", help="srt/vtt subtitle file (skips whisper)")
    ap.add_argument("--silence-only", action="store_true")
    ap.add_argument("--language", default=None, help="e.g. ko")
    ap.add_argument("--model", default="small")
    ap.add_argument("--silence-db", type=float, default=-35)
    ap.add_argument("--silence-min", type=float, default=0.8)
    ap.add_argument("-o", "--output", default="transcript.json")
    ap.add_argument("--srt-out", default=None,
                    help="also write the transcript as a subtitle SRT (NLE captions)")
    ap.add_argument("--vocab", default=None,
                    help="comma-separated domain terms/brand names/proper nouns "
                         "to bias recognition (initial_prompt + hotwords)")
    ap.add_argument("--vocab-file", default=None,
                    help="text file, one term per line (merged with --vocab)")
    args = ap.parse_args()

    result = {"segments": [], "silences": []}
    if args.media:
        result["silences"] = detect_silences(args.media, args.silence_db, args.silence_min)
    if not args.silence_only:
        if args.srt:
            result["segments"] = parse_srt(args.srt)
        elif args.media:
            vocab = []
            if args.vocab:
                vocab += [v.strip() for v in args.vocab.split(",") if v.strip()]
            if args.vocab_file:
                vocab += [l.strip() for l in open(args.vocab_file, encoding="utf-8")
                          if l.strip()]
            result["segments"] = whisper_transcribe(args.media, args.language,
                                                    args.model, vocab or None)
        else:
            sys.exit("Either --srt or a media file is required.")

    json.dump(result, open(args.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{args.output}: {len(result['segments'])} sentences, {len(result['silences'])} silences")
    if args.srt_out and result["segments"]:
        n = write_srt(result["segments"], args.srt_out)
        print(f"{args.srt_out}: {n} subtitle entries")
