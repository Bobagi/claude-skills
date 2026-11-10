"""Gerador 3D LOCAL (imagem -> GLB) na GPU da maquina, sem credito do Meshy.

  python gen3d_local.py --image ref.png --out <pasta>/<Nome>.glb [--engine trellis2] [--res 1024] [--seed 42]
  python gen3d_local.py --engine hunyuan --image ref.png --out x.glb [--texture]   (SO TESTE, ver licenca)

Engines (instalacao em C:\\ComfyUIFiles\\tools, ver SKILL.md secao 0b):
- trellis2 (PADRAO, MIT): TRELLIS.2 pelos nos nativos do ComfyUI numa instancia SEPARADA
  (tools\\trellis2\\ComfyUI, venv proprio, porta 8190). Sai com textura PBR (cor, metal, rugosidade, normal, AO).
- hunyuan: Hunyuan3D-2mini (tools\\hunyuan3d, venv proprio). Licenca Tencent Hunyuan Community: NAO vale na UE,
  Reino Unido e Coreia do Sul; nada dele vai para o jogo sem decisao do dono.

O script cuida da trava C:\\ComfyUIFiles\\temp\\gpu.lock (espera se for de outro, cria com o nosso nome, apaga no
fim), sobe o servidor 8190 se precisar e o derruba ao terminar (devolve a VRAM). Grava <out>.json com tempo e VRAM.
Depois: optimize_model.py no GLB (nunca importar o original na engine).
"""
import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

TOOLS = Path(os.environ.get("GEN3D_TOOLS", r"C:\ComfyUIFiles\tools"))
LOCK = Path(os.environ.get("GEN3D_LOCK", r"C:\ComfyUIFiles\temp\gpu.lock"))
HERE = Path(__file__).resolve().parent
OWNER = "game-3d-assets/gen3d_local.py"


def take_lock():
    while LOCK.exists() and OWNER not in LOCK.read_text(errors="ignore"):
        print("GPU ocupada por:", LOCK.read_text(errors="ignore").splitlines()[0:1], "- esperando...", flush=True)
        time.sleep(30)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(f"owner: {OWNER}\nsince: {time.strftime('%Y-%m-%d %H:%M')}\npid: {os.getpid()}\n")


def drop_lock():
    if LOCK.exists() and OWNER in LOCK.read_text(errors="ignore"):
        LOCK.unlink()


def server_up():
    try:
        urllib.request.urlopen("http://127.0.0.1:8190/system_stats", timeout=3)
        return True
    except Exception:
        return False


def start_server():
    root = TOOLS / "trellis2"
    env = dict(os.environ, PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    log = open(root / "server.log", "w")
    p = subprocess.Popen([str(root / ".venv" / "Scripts" / "python.exe"), "main.py", "--listen", "127.0.0.1",
                          "--port", "8190", "--disable-auto-launch", "--reserve-vram", "0.8"],
                         cwd=root / "ComfyUI", stdout=log, stderr=subprocess.STDOUT, env=env)
    for _ in range(120):
        if server_up():
            return p
        time.sleep(2)
    p.kill()
    raise SystemExit("servidor TRELLIS.2 (8190) nao subiu; veja tools\\trellis2\\server.log")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=("trellis2", "hunyuan"), default="trellis2")
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", type=int, default=1024, help="trellis2: 512, 1024 ou 1536")
    ap.add_argument("--tex", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--texture", action="store_true", help="hunyuan: gera textura tambem (lento em 8 GB)")
    ap.add_argument("--keep-server", action="store_true", help="trellis2: nao derruba o servidor no fim (lote)")
    a = ap.parse_args()
    take_lock()
    proc = None
    try:
        if a.engine == "trellis2":
            if not server_up():
                proc = start_server()
            cmd = [sys.executable, str(HERE / "trellis2_comfy.py"), "--image", a.image, "--out", a.out,
                   "--res", str(a.res), "--tex", str(a.tex), "--seed", str(a.seed)]
        else:
            py = TOOLS / "hunyuan3d" / ".venv" / "Scripts" / "python.exe"
            cmd = [str(py), str(HERE / "hunyuan3d_run.py"), "--image", a.image, "--out", a.out, "--seed", str(a.seed)]
            if a.texture:
                cmd.append("--texture")
        r = subprocess.run(cmd)
        if r.returncode:
            raise SystemExit(r.returncode)
    finally:
        if proc and not a.keep_server:
            proc.terminate()
        drop_lock()


if __name__ == "__main__":
    main()
