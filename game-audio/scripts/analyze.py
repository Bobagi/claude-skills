# Analyses sound files so they can be cut without listening: format, length, levels, noise floor, where the energy
# sits in frequency, and the separate events with their times. With --png it also draws a sheet per file (waveform
# with the events marked + spectrogram, time axis in seconds) that can be opened with the Read tool.
# Usage: python analyze.py <file or folder> [...] [--png <out dir>] [--above 18] [--gap 0.25]
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audiokit as ak  # noqa: E402

EXT = (".wav", ".flac", ".ogg", ".mp3", ".aiff", ".aif", ".m4a", ".opus", ".aac")


def describe(path, above, gap):
    raw, sr = ak.read_any(path)
    ch = raw.shape[1]
    ak.RATE = 48000
    d = raw
    if sr != 48000:
        from scipy.signal import resample_poly
        g = np.gcd(sr, 48000)
        d = resample_poly(raw, 48000 // g, sr // g, axis=0)
    m = ak.mono(d)[:, 0]
    dur = len(m) / 48000
    pk = ak.to_db(np.abs(d).max())
    rms = ak.rms_db(d)
    frame = 2048
    n = len(m) // frame
    frames = m[:n * frame].reshape(n, frame) if n else m[None, :]
    frms = np.sqrt((frames ** 2).mean(axis=1))
    floor = ak.to_db(np.percentile(frms, 10)) if len(frms) else -120
    spec = np.abs(np.fft.rfft(m[: 48000 * 30] * 1.0))
    freqs = np.fft.rfftfreq(min(len(m), 48000 * 30), 1 / 48000)
    centroid = float((spec * freqs).sum() / max(spec.sum(), 1e-9))
    bands = [(20, 120), (120, 500), (500, 2000), (2000, 8000), (8000, 24000)]
    total = (spec ** 2).sum() + 1e-12
    share = [100 * (spec[(freqs >= a) & (freqs < b)] ** 2).sum() / total for a, b in bands]
    clip = int((np.abs(raw) > 0.999).sum())
    corr = float(np.corrcoef(d[:, 0], d[:, 1])[0, 1]) if ch == 2 and len(d) > 1 else 1.0
    ev = ak.events(d, gap, above)
    return dict(path=path, sr=sr, ch=ch, dur=dur, peak=pk, rms=rms, floor=floor, centroid=centroid, share=share,
                clip=clip, corr=corr, events=ev, data=m)


def report(r):
    name = os.path.basename(r["path"])
    print(f"\n== {name}")
    print(f"   {r['sr']} Hz, {r['ch']} canal(is), {r['dur']:.2f} s | pico {r['peak']:.1f} dB, rms {r['rms']:.1f} dB, "
          f"piso de ruido {r['floor']:.1f} dB | centroide {r['centroid']:.0f} Hz"
          + (f" | L/R corr {r['corr']:.2f}" if r["ch"] == 2 else "")
          + (f" | CLIP {r['clip']} amostras" if r["clip"] else ""))
    labels = ["sub<120", "grave<500", "medio<2k", "agudo<8k", "ar>8k"]
    print("   energia: " + "  ".join(f"{l} {s:4.1f}%" for l, s in zip(labels, r["share"])))
    ev = r["events"]
    print(f"   {len(ev)} evento(s):" + ("" if ev else " nenhum acima do limiar"))
    for i, (a, b, p) in enumerate(ev[:40]):
        print(f"     {i + 1:2d}. {a:7.2f} - {b:7.2f} s  ({b - a:5.2f} s)  pico {p:6.1f} dB")
    if len(ev) > 40:
        print(f"     ... +{len(ev) - 40}")


def sheet(r, out_dir):
    from PIL import Image, ImageDraw
    W, H1, H2, pad = 1600, 220, 260, 30
    img = Image.new("RGB", (W, H1 + H2 + pad * 3), (18, 18, 22))
    dr = ImageDraw.Draw(img)
    m = r["data"]
    n = len(m)
    cols = W - 2 * pad
    step = max(1, n // cols)
    blocks = m[: step * cols].reshape(-1, step) if n >= cols else m[:, None]
    hi, lo = blocks.max(axis=1), blocks.min(axis=1)
    mid = pad + H1 // 2
    scale = (H1 // 2 - 4) / max(np.abs(m).max(), 1e-9)
    for x in range(len(hi)):
        dr.line([(pad + x, mid - hi[x] * scale), (pad + x, mid - lo[x] * scale)], fill=(110, 200, 255))
    dur = r["dur"]
    for i, (a, b, _) in enumerate(r["events"][:60]):
        xa, xb = pad + a / dur * cols, pad + b / dur * cols
        dr.rectangle([xa, pad, xb, pad + H1], outline=(255, 170, 40))
        dr.text((xa + 2, pad + 2), str(i + 1), fill=(255, 200, 80))
    # Spectrogram (log frequency 30 Hz to 20 kHz, dB colour).
    nfft, hop = 2048, max(256, n // cols)
    frames = [m[i:i + nfft] * np.hanning(nfft) for i in range(0, max(1, n - nfft), hop)][:cols]
    if frames:
        S = 20 * np.log10(np.abs(np.fft.rfft(np.array(frames), axis=1)) + 1e-9)
        f = np.fft.rfftfreq(nfft, 1 / 48000)
        rows = np.geomspace(30, 20000, H2)
        idx = np.clip(np.searchsorted(f, rows), 0, len(f) - 1)
        S = S[:, idx]
        S = np.clip((S - (S.max() - 80)) / 80, 0, 1)
        top = pad * 2 + H1
        px = img.load()
        xs = np.linspace(0, len(frames) - 1, cols).astype(int)
        for x in range(cols):
            col = S[xs[x]]
            for y in range(H2):
                v = col[H2 - 1 - y]
                px[pad + x, top + y] = (int(255 * v ** 0.7), int(180 * v ** 1.5), int(90 + 120 * v))
        for hz in (100, 500, 1000, 5000, 10000):
            y = top + H2 - 1 - int(np.searchsorted(rows, hz))
            dr.text((2, y - 6), f"{hz // 1000}k" if hz >= 1000 else str(hz), fill=(200, 200, 200))
    for s in range(0, int(dur) + 1, max(1, int(dur // 20) or 1)):
        x = pad + s / max(dur, 1e-9) * cols
        dr.line([(x, pad + H1), (x, pad + H1 + 6)], fill=(200, 200, 200))
        dr.text((x + 2, pad + H1 + 6), f"{s}s", fill=(200, 200, 200))
    dr.text((pad, 8), f"{os.path.basename(r['path'])}  {dur:.2f}s  pico {r['peak']:.1f} dB", fill=(240, 240, 240))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(r["path"]))[0] + ".png")
    img.save(out)
    print(f"   imagem: {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--png", help="pasta para as imagens (forma de onda + espectrograma)")
    ap.add_argument("--above", type=float, default=18, help="evento = envelope X dB acima do piso de ruido")
    ap.add_argument("--gap", type=float, default=0.25, help="silencio minimo entre eventos (s)")
    a = ap.parse_args()
    files = []
    for p in a.paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                files += [os.path.join(root, n) for n in sorted(names) if n.lower().endswith(EXT)]
        else:
            files.append(p)
    for f in files:
        try:
            r = describe(f, a.above, a.gap)
        except Exception as e:  # keep going through a folder
            print(f"\n== {os.path.basename(f)}: ERRO {e}")
            continue
        report(r)
        if a.png:
            sheet(r, a.png)


if __name__ == "__main__":
    main()
