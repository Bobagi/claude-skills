"""Finds the tempo, the beat grid and the drop of a music track, so the edit can
cut on bars and land the biggest moment of the video on the drop.

  python find_drop.py musica.mp3 [outra.mp3 ...]

Prints, per file: duration, BPM, beat period, the energy curve in 4 s windows
(0..1, the build and the drop are obvious in it) and the beat with the biggest
jump in low-end energy (the drop). Needs: pip install librosa
"""
import sys

import librosa
import numpy as np

for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=22050, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    period = float(np.median(np.diff(beats)))
    rms = librosa.feature.rms(y=y, hop_length=256)[0]
    t = librosa.times_like(rms, sr=sr, hop_length=256)
    low = librosa.feature.melspectrogram(y=y, sr=sr, hop_length=256, n_mels=32)[:4].sum(0)
    win = [float(np.mean(rms[(t >= s) & (t < s + 4)])) for s in range(0, int(t[-1]), 4)]
    mx = max(win) or 1
    per_beat = []
    for b in beats:
        m = (t >= b) & (t < b + period)
        per_beat.append((float(b), float(low[m].mean()) if m.any() else 0.0))
    # drop = beat where the low end jumps the most against the previous bar (4 beats)
    best = max(range(4, len(per_beat)), key=lambda i: per_beat[i][1] - np.mean([p[1] for p in per_beat[i - 4:i]]))
    print(f'{f}')
    print(f'  {len(y) / sr:.1f} s, {60 / period:.1f} BPM, beat {period:.4f} s, bar {4 * period:.4f} s')
    print('  energia/4s:', ' '.join(f'{w / mx:.2f}' for w in win))
    print(f'  drop provavel: {per_beat[best][0]:.2f} s (confira na curva acima)')
