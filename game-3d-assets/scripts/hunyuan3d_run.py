"""Hunyuan3D-2mini (Tencent) imagem -> GLB, script independente no venv C:\\ComfyUIFiles\\tools\\hunyuan3d\\.venv.

LICENCA: Tencent Hunyuan 3D 2.0 Community License. NAO vale na Uniao Europeia, Reino Unido e Coreia do Sul.
So para TESTE; nada dele entra no jogo ate o Gustavo decidir.

  .venv\\Scripts\\python.exe hunyuan3d_run.py --image ref.png --out pasta/obj.glb [--texture] [--steps 50]
Forma: hunyuan3d-dit-v2-mini (0,6 B). Textura (opcional): hunyuan3d-paint-v2-0-turbo + delight do Hunyuan3D-2,
com offload para a CPU (precisa do custom_rasterizer compilado). Mede tempo e VRAM (torch + nvidia-smi).
"""
import argparse
import json
import os
import subprocess
import threading
import time
from pathlib import Path

os.environ.setdefault("HY3DGEN_MODELS", r"C:\ComfyUIFiles\tools\hunyuan3d\models")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch  # noqa: E402
from PIL import Image  # noqa: E402


def vram_now():
    return int(subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                       text=True).split()[0])


class VramSampler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.peak, self.stop = 0, False

    def run(self):
        while not self.stop:
            try:
                self.peak = max(self.peak, vram_now())
            except Exception:
                pass
            time.sleep(0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--octree", type=int, default=380)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--texture", action="store_true")
    ap.add_argument("--max-faces", type=int, default=40000, help="reducao antes da textura (padrao do repo)")
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import (DegenerateFaceRemover, FaceReducer, FloaterRemover,
                                  Hunyuan3DDiTFlowMatchingPipeline)

    image = Image.open(a.image)
    if image.mode != "RGBA" or image.getextrema()[3][0] == 255:
        image = BackgroundRemover()(image.convert("RGB"))
    image.save(out.with_name(out.stem + "_input.png"))

    base = vram_now()
    s = VramSampler()
    s.start()
    t0 = time.time()
    pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "tencent/Hunyuan3D-2mini", subfolder="hunyuan3d-dit-v2-mini", variant="fp16", use_safetensors=True)
    t_load = time.time() - t0
    torch.cuda.reset_peak_memory_stats()
    mesh = pipe(image=image, num_inference_steps=a.steps, octree_resolution=a.octree, num_chunks=20000,
                generator=torch.manual_seed(a.seed), output_type="trimesh")[0]
    t_shape = time.time() - t0 - t_load
    peak_shape = torch.cuda.max_memory_reserved() / 2**20
    raw_faces = len(mesh.faces)
    mesh.export(out.with_name(out.stem + "_raw.glb"))
    mesh = FloaterRemover()(mesh)
    mesh = DegenerateFaceRemover()(mesh)
    rep = {"engine": "hunyuan3d-2mini", "steps": a.steps, "octree": a.octree, "seed": a.seed,
           "load_s": round(t_load, 1), "shape_s": round(t_shape, 1), "torch_peak_shape_mb": round(peak_shape),
           "raw_faces": raw_faces}
    if a.texture:
        del pipe
        torch.cuda.empty_cache()
        mesh = FaceReducer()(mesh, max_facenum=a.max_faces)
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        t1 = time.time()
        tex = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2", subfolder="hunyuan3d-paint-v2-0-turbo")
        tex.enable_model_cpu_offload()
        torch.cuda.reset_peak_memory_stats()
        mesh = tex(mesh, image=image)
        rep["texture_s"] = round(time.time() - t1, 1)
        rep["torch_peak_texture_mb"] = round(torch.cuda.max_memory_reserved() / 2**20)
    mesh.export(out)
    s.stop = True
    rep.update({"seconds_total": round(time.time() - t0, 1), "vram_baseline_mb": base, "vram_peak_total_mb": s.peak,
                "vram_peak_delta_mb": s.peak - base, "glb": str(out)})
    out.with_suffix(".json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
