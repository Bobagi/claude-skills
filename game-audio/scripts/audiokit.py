# audiokit: the editing toolkit for game sound sources (load any format, cut, clean, loop, layer, filter, save as
# game-ready WAV). Imported by the per-project conversion script (e.g. SourceAssets/Tools/convert_sounds.py):
#     sys.path.insert(0, <dir of this file>); from audiokit import *
# Conventions (see SKILL.md "Formato de saida"): 48 kHz, 16-bit PCM WAV; one-shots mono, peak -1 dBFS, silence
# trimmed, short fades; loops stereo, crossfaded seam, RMS matched. Times are in seconds, levels in dB.
import os
import shutil
import subprocess
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

RATE = 48000
SRC = "."   # base folder of the downloaded originals; set by the caller (audiokit.SRC = ...)
DST = "."   # base folder of the game audio (e.g. Assets/_Project/Audio); set by the caller


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # pip install imageio-ffmpeg (bundles a static ffmpeg)
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError("Formato que o libsndfile nao le (m4a/aac/opus): instale ffmpeg ou 'pip install imageio-ffmpeg'")


def read_any(path):
    """(data[n, ch] float64, rate) from wav/flac/ogg/mp3/aiff (libsndfile) or anything else through ffmpeg."""
    try:
        data, sr = sf.read(path, dtype="float64", always_2d=True)
        return data, sr
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), "audiokit_decode.wav")
        subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", path, "-c:a", "pcm_f32le", tmp], check=True)
        data, sr = sf.read(tmp, dtype="float64", always_2d=True)
        return data, sr


def load(rel, start=None, end=None):
    """File under SRC, resampled to RATE, optionally cut to [start, end) seconds."""
    data, sr = read_any(os.path.join(SRC, rel))
    if sr != RATE:
        g = np.gcd(sr, RATE)
        data = resample_poly(data, RATE // g, sr // g, axis=0)
    a = 0 if start is None else int(start * RATE)
    b = len(data) if end is None else int(end * RATE)
    return data[a:b]


def db(x):
    return 10 ** (x / 20)


def to_db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def mono(d):
    return d.mean(axis=1, keepdims=True)


def stereo(d):
    return np.repeat(d, 2, axis=1) if d.shape[1] == 1 else d


def cut(d, start, end=None):
    return d[int(start * RATE): None if end is None else int(end * RATE)]


def silence(seconds, channels=1):
    return np.zeros((int(seconds * RATE), channels))


def trim(d, threshold_db=-50, pre=0.01, post=0.05):
    """Drops leading/trailing audio quieter than threshold_db below the peak."""
    env = np.abs(d).max(axis=1)
    keep = np.where(env > env.max() * db(threshold_db))[0]
    if len(keep) == 0:
        return d
    a = max(0, keep[0] - int(pre * RATE))
    b = min(len(d), keep[-1] + int(post * RATE))
    return d[a:b]


def fade(d, fade_in=0.004, fade_out=0.03):
    d = d.copy()
    n_in, n_out = min(int(fade_in * RATE), len(d)), min(int(fade_out * RATE), len(d))
    if n_in:
        d[:n_in] *= np.linspace(0, 1, n_in)[:, None]
    if n_out:
        d[-n_out:] *= np.linspace(1, 0, n_out)[:, None]
    return d


def gain(d, gain_db):
    return d * db(gain_db)


def peak(d, target_db=-1.0):
    p = np.abs(d).max()
    return d * (db(target_db) / p) if p > 0 else d


def rms_db(d):
    return to_db(np.sqrt((d ** 2).mean()))


def loudness(d, rms_target_db=-24.0, ceiling_db=-1.0):
    """Matches RMS, then soft-limits only the peaks above the ceiling (for loops and beds)."""
    rms = np.sqrt((d ** 2).mean())
    d = d * (db(rms_target_db) / max(rms, 1e-9))
    c = db(ceiling_db)
    if np.abs(d).max() > c:
        d = np.where(np.abs(d) > c, np.sign(d) * (c + (1 - c) * np.tanh((np.abs(d) - c) / (1 - c))), d)
        d = d * (c / np.abs(d).max())
    return d


def loop(d, seconds=None, crossfade=2.0, start=0.0):
    """Seamless loop: the tail after the cut is crossfaded (equal power) into the start."""
    d = d[int(start * RATE):]
    x = min(int(crossfade * RATE), len(d) // 3)
    length = len(d) - x if seconds is None else min(int(seconds * RATE), len(d) - x)
    out = d[:length].copy()
    t = np.linspace(0, np.pi / 2, x)[:, None]
    out[:x] = out[:x] * np.sin(t) + d[length:length + x] * np.cos(t)
    return out


def highpass(d, hz, order=4):
    return sosfilt(butter(order, hz, "highpass", fs=RATE, output="sos"), d, axis=0)


def lowpass(d, hz, order=4):
    return sosfilt(butter(order, hz, "lowpass", fs=RATE, output="sos"), d, axis=0)


def bandpass(d, low, high, order=4):
    return sosfilt(butter(order, [low, high], "bandpass", fs=RATE, output="sos"), d, axis=0)


def pitch(d, semitones):
    """Pitch and speed together (tape style): +12 = an octave up and twice as fast."""
    ratio = 2 ** (semitones / 12)
    up, down = int(round(1000 / ratio)), 1000
    g = np.gcd(up, down)
    return resample_poly(d, up // g, down // g, axis=0)


def reverse(d):
    return d[::-1].copy()


def gate(d, floor_db=-55, release=0.08):
    """Simple downward gate: mutes what stays below floor_db (relative to peak); keeps room tone out of one-shots."""
    env = np.abs(d).max(axis=1)
    win = max(1, int(0.01 * RATE))
    env = np.convolve(env, np.ones(win) / win, mode="same")
    open_ = (env > env.max() * db(floor_db)).astype(float)
    k = max(1, int(release * RATE))
    smooth = np.convolve(open_, np.ones(k) / k, mode="same")
    return d * np.clip(smooth * 2, 0, 1)[:, None]


def mix(*layers):
    """Layers [(data, offset_seconds, gain_db), ...] or plain arrays, summed into one buffer."""
    items = [(l, 0.0, 0.0) if isinstance(l, np.ndarray) else (l[0], l[1] if len(l) > 1 else 0.0, l[2] if len(l) > 2 else 0.0)
             for l in layers]
    ch = max(i[0].shape[1] for i in items)
    n = max(int(o * RATE) + len(a) for a, o, _ in items)
    out = np.zeros((n, ch))
    for a, o, g in items:
        a = stereo(a) if ch == 2 else a
        s = int(o * RATE)
        out[s:s + len(a)] += a * db(g)
    return out


def concat(*parts, crossfade=0.01):
    out = parts[0]
    for p in parts[1:]:
        x = min(int(crossfade * RATE), len(out), len(p))
        if x:
            t = np.linspace(0, 1, x)[:, None]
            seam = out[-x:] * (1 - t) + p[:x] * t
            out = np.concatenate([out[:-x], seam, p[x:]])
        else:
            out = np.concatenate([out, p])
    return out


def envelope_db(d, hop=0.005):
    """Peak-hold envelope in dB, one value per `hop` seconds (keeps 1 ms clicks that an average would wash out)."""
    m = np.abs(mono(d)[:, 0])
    h = max(1, int(hop * RATE))
    n = len(m) // h
    if n == 0:
        return np.array([to_db(m.max() if len(m) else 0)]), h
    return 20 * np.log10(m[:n * h].reshape(n, h).max(axis=1) + 1e-12), h


def events(d, min_gap=0.25, above_floor_db=18, below_peak_db=40, min_len=0.0):
    """[(start, end, peak_db)] of separate events: where the peak envelope rises `above_floor_db` over the noise
    floor (10th percentile) and is within `below_peak_db` of the loudest moment; closer than min_gap = same event."""
    env, h = envelope_db(d)
    floor = np.percentile(env, 10)
    thr = max(floor + above_floor_db, env.max() - below_peak_db)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return []
    gap = max(1, int(min_gap * RATE / h))
    out, start, prev = [], idx[0], idx[0]
    for j in idx[1:]:
        if j - prev > gap:
            out.append((start, prev))
            start = j
        prev = j
    out.append((start, prev))
    return [(a * h / RATE, (b + 1) * h / RATE, float(env[a:b + 1].max())) for a, b in out
            if (b + 1 - a) * h / RATE >= min_len]


def save(d, rel, quiet=False):
    path = os.path.join(DST, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.clip(d, -1, 1), RATE, subtype="PCM_16")
    if not quiet:
        print(f"{rel:58s} {d.shape[1]}ch {len(d) / RATE:6.2f}s  pico {to_db(np.abs(d).max()):6.1f} dB  rms {rms_db(d):6.1f} dB")
    return path


# Shorthands used by conversion scripts --------------------------------------------------------------------------

def oneshot(src, dst, gain_db=-1.0, start=None, end=None, threshold_db=-50, fade_out=0.03):
    """A single event, mono, trimmed, faded, peak normalised."""
    return save(peak(fade(trim(mono(load(src, start, end)), threshold_db), 0.004, fade_out), gain_db), dst)


def segment(src, dst, start, end, fade_out=0.25, gain_db=-1.0):
    """One event cut by time from a longer take."""
    return oneshot(src, dst, gain_db, start, end, -45, fade_out)


def split(src, dst_pattern, count, min_gap=0.25, max_len=0.8, pre=0.02, skip=0, gain_db=-1.0, above_floor_db=18):
    """The `count` loudest separate events of a take, each saved as a one-shot (dst_pattern has {0} = 1..count)."""
    d = mono(load(src))
    ev = events(d, min_gap, above_floor_db)
    order = sorted(sorted(range(len(ev)), key=lambda k: -ev[k][2])[skip:skip + count])
    paths = []
    for n, k in enumerate(order):
        a = max(0.0, ev[k][0] - pre)
        nxt = ev[k + 1][0] - pre if k + 1 < len(ev) else len(d) / RATE
        b = min(nxt, a + max_len, len(d) / RATE)
        paths.append(save(peak(fade(trim(cut(d, a, b), -45), 0.002, 0.04), gain_db), dst_pattern.format(n + 1)))
    return paths


def make_loop(src, dst, seconds=None, crossfade=2.0, start=0.0, rms_target_db=-24.0, to_mono=False):
    d = load(src)
    if to_mono:
        d = mono(d)
    return save(loudness(loop(d, seconds, crossfade, start), rms_target_db), dst)
