"""
tts_voice.py: expressive neural text-to-speech from a JSON of lines to WAV files, fully local (Qwen3-TTS).

Engine: Qwen3-TTS 12Hz 1.7B (Apache-2.0, QwenLM). Two modes, picked per line:
  * CustomVoice (default): a preset speaker (aiden, ryan, uncle_fu, dylan, eric, serena, vivian, sohee, ono_anna)
    plus a plain-words "instruct" string that steers emotion, pace and character ("warm, slow, cheerful old farmer").
  * VoiceDesign: no speaker, the voice itself is described in words ("a frightened young woman, far away").
    Used when a line (or the file) gives a "voice" description and no "speaker". Loads a second model (~3.5 GB).
No real person is cloned: both modes are built-in synthetic voices.

Input JSON (either shape):
  [ {"id": "n1_intro", "text": "...", "delivery": "warm, cheerful, unhurried",
     "speaker": "aiden", "voice": "an elderly farmer ...", "pitch": -2.5, "tempo": 1.0}, ... ]
  { "speaker": "aiden", "voice": "...", "delivery": "...", "pitch": -2.5, "lines": [ {...}, ... ], "cb": [ {...} ] }
Per-line keys override file-level keys. Every list-valued key ("lines", "cb", ...) is merged into one run.
  id        file name, <out>/<id>.wav
  text      what is said (English works best with aiden/ryan; the other speakers are Chinese/Japanese/Korean native)
  delivery  emotion and pace for this line, plain words; appended to the voice description to form the instruct
  voice     who is speaking (age, timbre, accent); for CustomVoice it is part of the instruct, for VoiceDesign it IS the voice
  speaker   CustomVoice preset; set to null or "" to force VoiceDesign for that line
  pitch     semitones, tape style (negative = lower AND slower; -2.5 ages a male voice noticeably); default 0
  tempo     extra speed factor after pitch (0.9 = 10 % slower, pitch kept); default 1.0
  language  default "English"
  temperature  sampling temperature (default 0.9; lower = steadier, higher = more expressive but riskier)
  seed      per-line seed (default: global seed + line index) so a rerun gives the same take

Output: mono PCM 16-bit WAV at --rate Hz (default 48000), trimmed of leading/trailing silence, 60 ms of
silence padded at both ends, peak normalised to -1 dBFS. A tts_manifest.json next to the WAVs records
instruct, seed, duration and generation time per line.

Usage (run with the interpreter of a venv that has torch CUDA + qwen-tts, see the project README-tts.md):
  python tts_voice.py lines.json --out raw/
  python tts_voice.py lines.json --out raw/ --only n1_intro,n4_push --force
  python tts_voice.py lines.json --out raw/ --speaker ryan --pitch -2 --voice "a tired sheriff in his fifties"
Options: --rate 48000  --seed 7  --force (regenerate existing)  --only id,id  --dry (print instructs, no model)
         --model <hf id or local path> (CustomVoice)  --design-model <hf id> (VoiceDesign)  --device cuda:0  --cpu
Timings on an RTX 3060 Ti (8 GB): model load ~70 s, ~4.5 GB VRAM, about 4 s of compute per second of speech.

Install (uv, isolated, Windows or Linux; on Linux replace Scripts/python.exe with bin/python):
  uv venv --python 3.12 .venv
  uv pip install --python .venv/Scripts/python.exe torch torchaudio --index-url https://download.pytorch.org/whl/cu128
  uv pip install --python .venv/Scripts/python.exe qwen-tts soundfile scipy numpy
The "SoX could not be found" banner printed at import is harmless (optional wrapper, not used here).
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
DEFAULT_DESIGN_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
DEFAULTS = dict(speaker="aiden", voice="", delivery="", pitch=0.0, tempo=1.0, language="English",
                temperature=0.9, top_k=50, top_p=1.0, repetition_penalty=1.05, max_new_tokens=2048)


def load_lines(path):
    """Accepts a list of lines or a dict with file-level defaults plus one or more lists of lines."""
    with open(path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if isinstance(cfg, list):
        return {}, cfg
    lines = []
    for val in cfg.values():
        if isinstance(val, list):
            lines.extend(x for x in val if isinstance(x, dict) and "id" in x and "text" in x)
    base = {k: v for k, v in cfg.items() if not isinstance(v, list)}
    return base, lines


def build_instruct(voice, delivery):
    parts = [p.strip().rstrip(".") for p in (voice, delivery) if p and p.strip()]
    return (". ".join(parts) + ".") if parts else None


def trim(d, sr, threshold_db=-45.0, pre=0.01, post=0.05):
    env = np.abs(d)
    keep = np.where(env > env.max() * 10 ** (threshold_db / 20))[0]
    if len(keep) == 0:
        return d
    a = max(0, keep[0] - int(pre * sr))
    b = min(len(d), keep[-1] + int(post * sr))
    return d[a:b]


def resample(d, src, dst):
    if src == dst:
        return d
    g = math.gcd(int(src), int(dst))
    return resample_poly(d, dst // g, src // g)


def postprocess(wav, sr, rate, pitch, tempo, pad=0.06):
    d = np.asarray(wav, dtype=np.float64)
    if d.ndim > 1:
        d = d.mean(axis=1)
    d = trim(d, sr)
    # tape-style pitch: resample so the content plays slower and lower (or faster and higher)
    if abs(pitch) > 1e-3:
        ratio = 2 ** (pitch / 12)
        up, down = int(round(1000 / ratio)), 1000
        g = math.gcd(up, down)
        d = resample_poly(d, up // g, down // g)
    if abs(tempo - 1.0) > 1e-3:
        # speed change without pitch change needs a phase vocoder; librosa ships with qwen-tts
        import librosa
        d = librosa.effects.time_stretch(d.astype(np.float32), rate=float(tempo)).astype(np.float64)
    d = resample(d, sr, rate)
    peak = np.max(np.abs(d)) or 1.0
    d = d / peak * 10 ** (-1.0 / 20)
    z = np.zeros(int(pad * rate))
    return np.concatenate([z, d, z])


class Engine:
    """Lazy holder for the two Qwen3-TTS models so a run that only needs one never downloads the other."""

    def __init__(self, model, design_model, device):
        self.model_id, self.design_id, self.device = model, design_model, device
        self._custom = self._design = None
        self.load_seconds = 0.0

    def _load(self, name):
        import torch
        from qwen_tts import Qwen3TTSModel
        t0 = time.time()
        dtype = torch.bfloat16 if self.device.startswith("cuda") else torch.float32
        m = Qwen3TTSModel.from_pretrained(name, device_map=self.device, dtype=dtype, attn_implementation="sdpa")
        self.load_seconds += time.time() - t0
        print(f"[tts] loaded {name} in {time.time() - t0:.0f}s on {self.device}", flush=True)
        return m

    def custom(self):
        if self._custom is None:
            self._custom = self._load(self.model_id)
        return self._custom

    def design(self):
        if self._design is None:
            self._design = self._load(self.design_id)
        return self._design

    def speak(self, line, seed):
        import torch
        torch.manual_seed(seed)
        if self.device.startswith("cuda"):
            torch.cuda.manual_seed_all(seed)
        kw = dict(do_sample=True, temperature=float(line["temperature"]), top_k=int(line["top_k"]),
                  top_p=float(line["top_p"]), repetition_penalty=float(line["repetition_penalty"]),
                  max_new_tokens=int(line["max_new_tokens"]))
        if line.get("speaker"):
            wavs, sr = self.custom().generate_custom_voice(
                text=line["text"], speaker=str(line["speaker"]).lower(), language=line["language"],
                instruct=line["instruct"], **kw)
        else:
            if not line["instruct"]:
                raise ValueError(f"{line['id']}: VoiceDesign needs a 'voice' or 'delivery' description")
            wavs, sr = self.design().generate_voice_design(
                text=line["text"], instruct=line["instruct"], language=line["language"], **kw)
        return wavs[0], sr


def main(argv=None):
    ap = argparse.ArgumentParser(description="Expressive local TTS (Qwen3-TTS) from a JSON of lines to WAVs; see the module docstring.")
    ap.add_argument("json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry", action="store_true", help="print the instruct of each line, load no model")
    ap.add_argument("--speaker", help="override the speaker for every line (empty string forces VoiceDesign)")
    ap.add_argument("--voice", help="override the voice description for every line")
    ap.add_argument("--pitch", type=float, help="override the pitch shift (semitones) for every line")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--design-model", default=DEFAULT_DESIGN_MODEL)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--cpu", action="store_true")
    a = ap.parse_args(argv)

    base, raw_lines = load_lines(a.json)
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    os.makedirs(a.out, exist_ok=True)
    lines = []
    for i, src in enumerate(raw_lines):
        line = dict(DEFAULTS)
        line.update({k: v for k, v in base.items() if k in DEFAULTS or k == "seed"})
        line.update(src)
        if a.speaker is not None:
            line["speaker"] = a.speaker
        if a.voice is not None:
            line["voice"] = a.voice
        if a.pitch is not None:
            line["pitch"] = a.pitch
        line["instruct"] = build_instruct(line.get("voice", ""), line.get("delivery", ""))
        line["seed"] = int(line.get("seed", a.seed + i))
        line["path"] = os.path.join(a.out, f"{line['id']}.wav")
        if only and line["id"] not in only:
            continue
        lines.append(line)

    if a.dry:
        for l in lines:
            print(f"{l['id']:12s} spk={l.get('speaker') or 'DESIGN':9s} pitch={l['pitch']:+.1f} seed={l['seed']} :: {l['instruct']}")
        return 0

    eng = Engine(a.model, a.design_model, "cpu" if a.cpu else a.device)
    manifest_path = os.path.join(a.out, "tts_manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    t_all = time.time()
    done = skipped = 0
    for l in lines:
        if os.path.exists(l["path"]) and not a.force:
            skipped += 1
            continue
        t0 = time.time()
        wav, sr = eng.speak(l, l["seed"])
        d = postprocess(wav, sr, a.rate, float(l["pitch"]), float(l["tempo"]))
        sf.write(l["path"], d, a.rate, subtype="PCM_16")
        dt = time.time() - t0
        manifest[l["id"]] = dict(text=l["text"], instruct=l["instruct"], speaker=l.get("speaker") or None,
                                 pitch=l["pitch"], tempo=l["tempo"], seed=l["seed"], temperature=l["temperature"],
                                 duration=round(len(d) / a.rate, 2), gen_seconds=round(dt, 1),
                                 model=a.model if l.get("speaker") else a.design_model)
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
        done += 1
        print(f"[tts] {l['id']:12s} {len(d) / a.rate:5.1f}s audio in {dt:5.1f}s  ({l['instruct']})", flush=True)
    print(f"[tts] done: {done} generated, {skipped} kept, "
          f"{time.time() - t_all - eng.load_seconds:.0f}s generating + {eng.load_seconds:.0f}s loading")
    return 0


if __name__ == "__main__":
    sys.exit(main())
