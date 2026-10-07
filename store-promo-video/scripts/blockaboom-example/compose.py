"""Promo video editor: cuts the recorded scenes on the music's bars, adds the
edit-only juice (punch zoom, shake, flash, slow motion on the big clears, popping
captions), and renders 1080x1920 H.264 with the music and the game's own SFX.

Every frame of game footage is the real game (recorded by record.mjs); this
script only frames it, times it and titles it, as the Play promo video policy
asks. Captions are 3 to 5 words, one per scene, readable while muted.

Usage:
  python scripts/promo/compose.py --lang pt-BR [--preview]   (preview = 540x960, fast)
Needs: promo/raw/<lang>/* (record.mjs), promo/audio-src/634684__Cloud-10.mp3,
       node scripts/promo/render-audio.mjs (called here for the remapped SFX track).
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PROMO = ROOT / 'promo'
FFMPEG = r'C:\ComfyUIFiles\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
FPS = 60
W, H = 1080, 1920

# music: "The Room" by Cloud-10 (Freesound 634684, CC0), 129.2 BPM, the drop lands at 28.21 s
MUSIC = PROMO / 'audio-src' / '634684__Cloud-10.mp3'
BEAT = 0.46440
DROP_IN_TRACK = 28.21
T0 = 0.617            # video time of the drop = the hook's 6-line blast
BAR = 4 * BEAT


def bar(n):
    return T0 + n * BAR


# (scene clip, video start, video end, source pieces [(from_frame, to_frame, speed)], caption key, camera)
TIMELINE = [
    ('hook', 0.0, bar(1), [(1, 999, 1.0)], 'hook', None),
    ('chain', bar(1), bar(3), [(10, 999, 1.0)], 'chain', None),
    ('clutch', bar(3), bar(5), [(1, 79, 1.0), (79, 100, 0.35), (100, 999, 1.0)], 'clutch', None),
    ('maps', bar(5), bar(6.5), [(140, 999, 1.0)], 'maps', None),
    ('daily', bar(6.5), bar(7.5), [(60, 999, 1.0)], 'daily', None),
    ('village', bar(7.5), bar(10), [(40, 999, 1.0)], 'village', ('push', 540, 880, 1.05, 1.18)),
    ('finale', bar(10), bar(12), [(1, 47, 1.0), (47, 67, 0.4), (67, 999, 1.0)], 'finale', None),
    ('END', bar(12), bar(14) + 0.5, None, None, None),
]
END_T = TIMELINE[-1][2]

CAPTIONS = {
    'pt-BR': {
        'hook': 'Uma peça, 6 linhas!', 'chain': 'Combos sem parar', 'clutch': 'Só sobrou um lugar...',
        'clutch2': 'Virada!', 'maps': 'Mapas com gemas e gelo', 'daily': 'Um desafio novo todo dia',
        'village': 'Construa sua vila', 'finale': 'Limpe o tabuleiro!', 'tagline': 'Encaixe. Exploda. Construa!'
    },
    'en-US': {
        'hook': 'One piece, 6 lines!', 'chain': 'Combo after combo', 'clutch': 'One spot left...',
        'clutch2': 'Comeback!', 'maps': 'Maps with gems and ice', 'daily': 'A new challenge every day',
        'village': 'Build your own village', 'finale': 'Clear the board!', 'tagline': 'Fit. Blast. Build!'
    },
    'es-419': {
        'hook': '¡Una pieza, 6 líneas!', 'chain': 'Combos sin parar', 'clutch': 'Queda un solo hueco...',
        'clutch2': '¡Remontada!', 'maps': 'Mapas con gemas y hielo', 'daily': 'Un reto nuevo cada día',
        'village': 'Construye tu villa', 'finale': '¡Limpia el tablero!', 'tagline': '¡Encaja. Explota. Construye!'
    },
}

# game "card" inside the 9:16 frame: room above for the caption, no black bars anywhere
CARD_S = 0.86
CARD_W, CARD_H = round(W * CARD_S), round(H * CARD_S)
CARD_X, CARD_Y = (W - CARD_W) // 2, H - CARD_H - 44
RADIUS = 46


def font(size, weight=700):
    f = ImageFont.truetype(str(PROMO / 'fredoka.ttf'), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def ease_out_back(k):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (k - 1) ** 3 + c1 * (k - 1) ** 2


class Clip:
    def __init__(self, lang, name):
        self.dir = PROMO / 'raw' / lang / name
        ev = json.loads((self.dir / 'events.json').read_text())
        self.frames = ev['frames']
        self.marks = ev['marks']
        self.sfx = ev['sfx']
        self.cache = {}

    def get(self, i):
        i = max(1, min(self.frames, i))
        if i not in self.cache:
            if len(self.cache) > 6:
                self.cache.pop(next(iter(self.cache)))
            self.cache[i] = Image.open(self.dir / f'f{i:05d}.jpg').convert('RGB')
        return self.cache[i]

    def at(self, pos):
        """Source position (float frame); blends neighbors in slow motion."""
        a = math.floor(pos)
        k = pos - a
        if k < 0.05:
            return self.get(a)
        if k > 0.95:
            return self.get(a + 1)
        return Image.blend(self.get(a), self.get(a + 1), k)


def source_positions(pieces, n_out):
    """Maps each output frame to a (float) source frame, following the speed pieces."""
    out = []
    pos = pieces[0][0]
    pi = 0
    for _ in range(n_out):
        out.append(pos)
        while pi < len(pieces) - 1 and pos >= pieces[pi][1]:
            pi += 1
        pos += pieces[pi][2]
    return out


def build_plan(lang):
    """Per output frame: (clip, src_pos, seg_index, frame_in_seg). Also the remapped SFX events."""
    clips = {}
    plan = []
    events = []
    booms = []
    for si, (name, t0, t1, pieces, cap, cam) in enumerate(TIMELINE):
        n = round(t1 * FPS) - round(t0 * FPS)
        if name == 'END':
            plan += [(None, 0, si, k) for k in range(n)]
            continue
        clip = clips.setdefault(name, Clip(lang, name))
        pos = source_positions(pieces, n)
        start = round(t0 * FPS)
        for k, p in enumerate(pos):
            plan.append((clip, p, si, k))
        # remap every sound and mark to the first output frame that reaches it
        for e in clip.sfx:
            f_src = 1 + e['t'] * FPS
            hit = next((k for k, p in enumerate(pos) if p >= f_src), None)
            if hit is not None and pos[0] <= f_src:
                events.append({**e, 't': (start + hit) / FPS})
        for m in clip.marks:
            hit = next((k for k, p in enumerate(pos) if p >= m['frame']), None)
            if hit is not None and pos[0] <= m['frame']:
                big = m['name'] == 'boom'
                booms.append((start + hit, 1.0 if big else 0.5))
    return plan, events, booms


def background(frame):
    """The game's own colors, blurred, so the card never sits on black bars."""
    small = frame.resize((108, 192), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    bg = small.resize((W, H), Image.BILINEAR)
    return Image.blend(bg, Image.new('RGB', (W, H), (14, 10, 26)), 0.45)


def card_mask():
    m = Image.new('L', (CARD_W, CARD_H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], RADIUS, fill=255)
    return m


def render_caption(text, size=82):
    f = font(size)
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    while d.textlength(text, font=f) > W - 90 and size > 50:
        size -= 4
        f = font(size)
    tw = int(d.textlength(text, font=f))
    img = Image.new('RGBA', (tw + 60, size + 60), (0, 0, 0, 0))
    dd = ImageDraw.Draw(img)
    dd.text((30, 22), text, font=f, fill=(255, 255, 255, 255), stroke_width=7, stroke_fill=(30, 16, 58, 255))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='pt-BR')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--endloop', default=str(PROMO / 'endloop'))
    a = ap.parse_args()
    lang = a.lang
    caps = CAPTIONS['es-419' if lang.startswith('es') else lang]
    plan, events, booms = build_plan(lang)
    total = len(plan)
    out_dir = PROMO / 'out'
    out_dir.mkdir(exist_ok=True)

    # 1) SFX track: the game's synth, re-rendered on the edited timeline
    tl = PROMO / 'raw' / lang / '_timeline'
    tl.mkdir(exist_ok=True)
    (tl / 'events.json').write_text(json.dumps({'fps': FPS, 'frames': total, 'marks': [], 'sfx': events}))
    subprocess.run(['node', str(ROOT / 'scripts/promo/render-audio.mjs'), '--lang', lang, '--only', '_timeline'], check=True)

    # 2) picture
    ow, oh = (540, 960) if a.preview else (W, H)
    video_tmp = out_dir / f'_video_{lang}.mp4'
    enc = subprocess.Popen([FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{ow}x{oh}',
                            '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast' if a.preview else 'slow',
                            '-crf', '23' if a.preview else '16', '-pix_fmt', 'yuv420p', str(video_tmp)], stdin=subprocess.PIPE)
    mask = card_mask()
    cap_cache = {}
    end_frames = sorted(Path(a.endloop).glob('*.png')) if Path(a.endloop).exists() else []
    icon = Image.open(ROOT / 'assets/master-icon.png').convert('RGB')
    boom_at = dict()
    for f, s in booms:
        boom_at[f] = max(boom_at.get(f, 0), s)
    last_bg = None
    for i, (clip, pos, si, k) in enumerate(plan):
        name, t0, t1, pieces, cap, cam = TIMELINE[si]
        # boom envelope: strongest recent boom drives zoom punch, shake and flash
        punch = shake = flash = 0.0
        for f, s in boom_at.items():
            d = i - f
            if 0 <= d < 14:
                punch = max(punch, s * 0.075 * math.exp(-d / 4.0))
                shake = max(shake, s * 16 * math.exp(-d / 3.0))
                if d < 3:
                    flash = max(flash, s * (0.38 if d < 2 else 0.15))
        if clip is None:
            frame = end_card(k, round((t1 - t0) * FPS), icon, end_frames, caps['tagline'])
        else:
            src = clip.at(pos)
            last_bg = background(src) if (i % 3 == 0 or last_bg is None) else last_bg
            frame = last_bg.copy()
            # camera: segment intro settle (1.05 -> 1.0), optional push-in, boom punch
            z, cx, cy = 1.0, W / 2, H / 2
            if cam and cam[0] == 'push':
                kk = k / max(1, round((t1 - t0) * FPS))
                z = cam[3] + (cam[4] - cam[3]) * kk
                cx, cy = cam[1], cam[2]
            z *= 1 + 0.05 * max(0.0, 1 - k / 8) + punch
            sx = math.sin(i * 1.9) * shake
            sy = math.cos(i * 2.7) * shake
            cw, ch = W / z, H / z
            x0 = min(max(cx - cw / 2 + sx, 0), W - cw)
            y0 = min(max(cy - ch / 2 + sy, 0), H - ch)
            game = src.resize((CARD_W, CARD_H), Image.BICUBIC, box=(x0, y0, min(W, x0 + cw), min(H, y0 + ch)))
            if flash:
                game = Image.blend(game, Image.new('RGB', game.size, (255, 255, 255)), flash)
            # soft glow behind the card
            frame.paste(game, (CARD_X, CARD_Y), mask)
            # caption pops in on each scene (second line for the clutch payoff)
            key = cap
            if name == 'clutch' and pos >= 79:
                key = 'clutch2'
            kc = k if key != 'clutch2' else int(i - next(f for f, _ in booms if f > round(t0 * FPS)))
            if key not in cap_cache:
                cap_cache[key] = render_caption(caps[key])
            c = cap_cache[key]
            kk = min(1.0, kc / 9)
            sc = max(0.01, ease_out_back(kk)) if kk < 1 else 1.0
            cw2, ch2 = max(1, int(c.width * sc)), max(1, int(c.height * sc))
            ci = c.resize((cw2, ch2), Image.BICUBIC)
            frame.paste(ci, (W // 2 - cw2 // 2, CARD_Y // 2 - ch2 // 2 + 4), ci)
        # fade from/to dark at the very ends
        fade = min(1.0, i / 4, (total - 1 - i) / 24)
        if fade < 1:
            frame = Image.blend(Image.new('RGB', (W, H), (10, 7, 20)), frame, max(0.0, fade))
        if a.preview:
            frame = frame.resize((ow, oh), Image.BILINEAR)
        enc.stdin.write(frame.tobytes())
        if i % 120 == 0:
            print(f'  frame {i}/{total}', flush=True)
    enc.stdin.close()
    enc.wait()

    # 3) mix: music (offset so the drop hits the hook) + game SFX, -14 LUFS for YouTube
    m_start = DROP_IN_TRACK - T0
    dur = total / FPS
    final = out_dir / f'blockaboom-promo-{lang}{"-preview" if a.preview else ""}.mp4'
    sfx_wav = tl / 'sfx.wav'
    subprocess.run([
        FFMPEG, '-y', '-loglevel', 'error', '-i', str(video_tmp),
        '-ss', f'{m_start:.3f}', '-t', f'{dur:.3f}', '-i', str(MUSIC), '-i', str(sfx_wav),
        '-filter_complex',
        f'[1:a]aresample=48000,volume=0.55,afade=t=out:st={dur - 1.2:.3f}:d=1.2[m];'
        f'[2:a]atrim=0:{dur:.3f},volume=2.4[s];'
        f'[m][s]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]',
        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', str(final)], check=True)
    video_tmp.unlink()
    print(final)


def end_card(k, n, icon, loop_frames, tagline):
    """Short brand close (store policy: keep it minimal): icon + name + tagline."""
    bg = Image.new('RGB', (W, H), (20, 14, 38))
    g = Image.new('L', (W, H), 0)
    ImageDraw.Draw(g).ellipse([W / 2 - 700, 760 - 700, W / 2 + 700, 760 + 700], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(220))
    bg = Image.composite(Image.new('RGB', (W, H), (74, 51, 132)), bg, g)
    if loop_frames:
        # Wan 2.2 loop of the icon (ComfyUI, wan_loop.py), 32 fps played on the 60 fps timeline
        src = Image.open(loop_frames[int(k * 32 / FPS) % len(loop_frames)]).convert('RGB')
    else:
        src = icon
    kk = min(1.0, k / 14)
    size = int(620 * (ease_out_back(kk) if kk < 1 else 1.0))
    if size > 4:
        ic = src.resize((size, size), Image.BICUBIC)
        m = Image.new('L', (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], int(size * 0.22), fill=255)
        bg.paste(ic, (W // 2 - size // 2, 760 - size // 2), m)
    d = ImageDraw.Draw(bg)
    if k > 8:
        a = min(1.0, (k - 8) / 10)
        f1, f2 = font(128), font(64, 600)
        col = tuple(int(c * a + 20 * (1 - a)) for c in (244, 239, 255))
        d.text((W / 2, 1210), 'Blockaboom', font=f1, fill=col, anchor='mm')
        col2 = tuple(int(c * a + 20 * (1 - a)) for c in (255, 201, 77))
        d.text((W / 2, 1330), tagline, font=f2, fill=col2, anchor='mm')
    return bg


if __name__ == '__main__':
    main()
