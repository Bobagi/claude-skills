"""
tts_chatterbox.py: falas em portugues do Brasil (ou outra das 23 linguas) com a voz de um AUDIO DE REFERENCIA,
local, por Chatterbox Multilingual (Resemble AI, MIT). Complementa o tts_voice.py (Qwen3-TTS):
  * Qwen3-TTS descreve a voz em palavras e a entrega por fala, mas o sotaque pt-BR depende do falante embutido.
  * Chatterbox copia o timbre de um WAV curto (5 a 15 s) e tem um finetune so de pt-BR (ResembleAI/
    Chatterbox-Multilingual-pt-br). Fluxo bom: criar a voz no Qwen (VoiceDesign, voz sintetica) e usar esse WAV
    como referencia aqui. Emocao: um escalar, "exaggeration" (0,25 calmo, 0,5 normal, 0,8 a 1,0 dramatico; com
    exaggeration alto, baixar cfg para 0,3 a 0,4 para nao acelerar).
MEDIDO EM 10/11/2026 (voice_score.py do Beneath the Shroud, referencia erick_dark.wav do Qwen): WER 0 nas 6 falas,
mas sotaque MAIS lusitano que a referencia (marcas PT "ɨ"/coda "ʃ" = 2 a 4 por fala contra 1 da referencia, nenhum
"tʃ/dʒ" em "de dia", "noite", "tia"). O finetune pt-BR carrega o T3, mas o S3Gen v3 dele NAO encaixa no pacote 0.1.7
do PyPI (cai no v2). Conclusao: para pt-BR continue no Qwen3-TTS (tts_voice.py); este script fica para re-testar
quando sair o loader v3 no PyPI, ou para outras linguas.
Regra: a referencia e voz sintetica ou de quem autorizou (Gustavo, Dayse). Nunca clonar pessoa real sem permissao.
A saida leva a marca d'agua inaudivel Perth da Resemble (vem no pacote).

JSON de entrada (lista ou {"ref": ..., "lines": [...]}):
  [ {"id": "erick_porta", "text": "Nao abre essa porta.", "ref": "voz_erick.wav", "exaggeration": 0.7}, ... ]
  id, text           obrigatorios
  ref                WAV de referencia (pode vir no topo do arquivo ou em --ref)
  exaggeration, cfg  por fala (padrao 0,5 e 0,5); temperature (0,8); seed (padrao: seed global + indice)
  language           id curto (padrao "pt")
Saida: WAV mono 16 bits em --rate (48000), sem silencio nas pontas, 60 ms de folga, pico em -1 dBFS,
e tts_manifest.json com os parametros por fala.

Uso (interpretador da venv do Chatterbox; no PC do Gustavo: D:/Tools/AIAudio/chatterbox/.venv):
  python tts_chatterbox.py falas.json --out raw/ [--ptbr] [--cpu] [--only id,id] [--force] [--ref voz.wav]
  --ptbr  usa o finetune pt-BR (T3 pt_br + S3Gen v3); sem ele, o modelo multilingue geral.
Tempos medidos (10/11/2026, na CPU porque a GPU estava ocupada): carga ~40 s, ~40 s por fala de 6 s. Na GPU cabe em ~3 GB.

Instalar (uv, isolado):
  uv venv --python 3.12 .venv
  uv pip install --python .venv/Scripts/python.exe chatterbox-tts==0.1.7 torch==2.6.0 torchaudio==2.6.0 "setuptools<81" \
      --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cu124
  (setuptools<81: o watermarker importa pkg_resources; sem ele o modelo nao carrega, "NoneType is not callable")
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def load_model(device, ptbr):
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    if not ptbr:
        return ChatterboxMultilingualTTS.from_pretrained(device=device)
    from pathlib import Path
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from chatterbox.mtl_tts import MTLTokenizer
    from chatterbox.models.t3 import T3
    from chatterbox.models.t3.modules.t3_config import T3Config
    from chatterbox.models.s3gen import S3Gen
    from chatterbox.models.voice_encoder import VoiceEncoder
    base = Path(snapshot_download("ResembleAI/chatterbox", allow_patterns=["ve.pt", "s3gen.pt"]))
    pt = Path(snapshot_download("ResembleAI/Chatterbox-Multilingual-pt-br",
                                allow_patterns=["t3_pt_br.safetensors", "s3gen_v3.safetensors",
                                                "grapheme_mtl_merged_expanded_v1.json"]))
    ve = VoiceEncoder()
    ve.load_state_dict(torch.load(base / "ve.pt", map_location="cpu", weights_only=True))
    t3 = T3(T3Config.multilingual())
    st = load_file(pt / "t3_pt_br.safetensors")
    t3.load_state_dict(st["model"][0] if "model" in st else st)
    s3 = S3Gen()
    try:
        s3.load_state_dict(load_file(pt / "s3gen_v3.safetensors"), strict=True)
    except Exception as e:
        print("S3Gen v3 nao encaixou nesta versao do pacote, usando o v2:", str(e)[:120])
        s3.load_state_dict(torch.load(base / "s3gen.pt", map_location="cpu", weights_only=True))
    for mod in (ve, t3, s3):
        mod.to(device).eval()
    tok = MTLTokenizer(str(pt / "grapheme_mtl_merged_expanded_v1.json"))
    return ChatterboxMultilingualTTS(t3, s3, ve, tok, device)


def finish(wav, sr, rate):
    x = np.asarray(wav, dtype=np.float32).reshape(-1)
    if sr != rate:
        g = np.gcd(sr, rate)
        x = resample_poly(x, rate // g, sr // g).astype(np.float32)
    env = np.abs(x)
    thr = env.max() * 10 ** (-45 / 20)
    idx = np.where(env > thr)[0]
    if len(idx):
        x = x[max(0, idx[0] - int(0.01 * rate)): idx[-1] + int(0.03 * rate)]
    pad = np.zeros(int(0.06 * rate), np.float32)
    x = np.concatenate([pad, x, pad])
    peak = np.abs(x).max()
    if peak > 0:
        x *= 10 ** (-1 / 20) / peak
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref")
    ap.add_argument("--ptbr", action="store_true")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    cfg = json.load(open(a.lines, encoding="utf-8"))
    top = cfg if isinstance(cfg, dict) else {}
    lines = cfg if isinstance(cfg, list) else [x for v in cfg.values() if isinstance(v, list) for x in v]
    only = set(a.only.split(",")) if a.only else None
    os.makedirs(a.out, exist_ok=True)

    import torch
    device = "cpu" if a.cpu or not torch.cuda.is_available() else "cuda"
    t = time.time()
    model = load_model(device, a.ptbr)
    print(f"modelo carregado em {time.time() - t:.0f} s ({device}, {'pt-BR' if a.ptbr else 'multilingue'})")

    man_path = os.path.join(a.out, "tts_manifest.json")
    manifest = json.load(open(man_path, encoding="utf-8")) if os.path.exists(man_path) else {}
    for i, ln in enumerate(lines):
        lid = ln["id"]
        dst = os.path.join(a.out, lid + ".wav")
        if only and lid not in only:
            continue
        if os.path.exists(dst) and not a.force:
            continue
        ref = ln.get("ref") or top.get("ref") or a.ref
        if not ref:
            sys.exit(f"{lid}: falta 'ref' (WAV de referencia)")
        ex = float(ln.get("exaggeration", top.get("exaggeration", 0.5)))
        cfgw = float(ln.get("cfg", top.get("cfg", 0.5)))
        temp = float(ln.get("temperature", top.get("temperature", 0.8)))
        seed = int(ln.get("seed", a.seed + i))
        torch.manual_seed(seed)
        t = time.time()
        w = model.generate(ln["text"], language_id=ln.get("language", top.get("language", "pt")),
                           audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfgw, temperature=temp)
        x = finish(w.squeeze(0).cpu().numpy(), model.sr, a.rate)
        sf.write(dst, x, a.rate, subtype="PCM_16")
        manifest[lid] = dict(text=ln["text"], ref=ref, exaggeration=ex, cfg=cfgw, temperature=temp, seed=seed,
                             ptbr=a.ptbr, seconds=round(len(x) / a.rate, 2), gen_s=round(time.time() - t, 1))
        print(f"{lid}: {manifest[lid]['seconds']} s de fala em {manifest[lid]['gen_s']} s")
        json.dump(manifest, open(man_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
