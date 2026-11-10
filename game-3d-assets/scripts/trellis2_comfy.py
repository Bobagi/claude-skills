"""TRELLIS.2 (Microsoft, MIT) imagem -> GLB pelos nos NATIVOS do ComfyUI numa instancia SEPARADA.

A instancia fica em C:\\ComfyUIFiles\\tools\\trellis2\\ComfyUI (venv proprio, porta 8190), sem tocar no ComfyUI
principal (8188). So stdlib: roda com qualquer Python.

  python trellis2_comfy.py --image ref.png --out pasta/obj.glb [--res 1024] [--tex 2048] [--seed 42]

--res 512  = so o estagio de 512 (mais leve)
--res 1024 = cascata 512 -> 1024 (padrao do TRELLIS.2)
--res 1536 = cascata 512 -> 1536 (o padrao do template do Comfy; pesado)
Mede tempo e VRAM de pico (nvidia-smi, GPU inteira; a linha de base vem antes do job) e grava <out>.json.
"""
import argparse
import json
import shutil
import subprocess
import threading
import time
import urllib.request
import uuid
from pathlib import Path

HOST = "http://127.0.0.1:8190"
COMFY_DIR = Path(r"C:\ComfyUIFiles\tools\trellis2\ComfyUI")


def http(path, data=None, ctype="application/json"):
    req = urllib.request.Request(HOST + path, data=data, headers={"Content-Type": ctype} if data else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def upload(img: Path) -> str:
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{img.name}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + img.read_bytes() + \
        f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{boundary}--\r\n".encode()
    out = json.loads(http("/upload/image", body, f"multipart/form-data; boundary={boundary}"))
    return out["name"]


def build(image_name, res, tex, seed, decimate, prefix):
    g = {
        "img": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "bgm": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
        "bg": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["bgm", 0], "image": ["img", 0]}},
        "crop": {"class_type": "ImageCropToMask", "inputs": {"images": ["img", 0], "masks": ["bg", 0], "width": 1024,
                                                            "height": 1024, "pad_factor": 1.1, "grow_mask": 0,
                                                            "background": "#000000"}},
        "dino": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "dino_v3_vit_l.safetensors"}},
        "cond": {"class_type": "Trellis2Conditioning", "inputs": {"clip_vision_model": ["dino", 0], "image": ["crop", 0]}},
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": "trellis_2_int8_convrot.safetensors",
                                                       "weight_dtype": "default"}},
        "svae": {"class_type": "VAELoader", "inputs": {"vae_name": "trellis_2_shape_vae_bf16.safetensors"}},
        "tvae": {"class_type": "VAELoader", "inputs": {"vae_name": "trellis_2_texture_vae_bf16.safetensors"}},
        # estrutura (CFG como no pipeline original)
        "cfgA": {"class_type": "CFGOverride", "inputs": {"model": ["unet", 0], "cfg": 1.0, "start_percent": 0.667,
                                                        "end_percent": 1.0}},
        "rA": {"class_type": "RescaleCFG", "inputs": {"model": ["cfgA", 0], "multiplier": 0.7}},
        "msA": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["rA", 0], "shift": 5.0}},
        "lat0": {"class_type": "EmptyTrellis2LatentStructure", "inputs": {"batch_size": 1}},
        "ks0": {"class_type": "KSampler", "inputs": {"model": ["msA", 0], "positive": ["cond", 0], "negative": ["cond", 1],
                                                     "latent_image": ["lat0", 0], "seed": seed, "steps": 12, "cfg": 7.5,
                                                     "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
        "vox": {"class_type": "VaeDecodeStructureTrellis2", "inputs": {"samples": ["ks0", 0], "vae": ["svae", 0],
                                                                      "resolution": "32"}},
        # forma 512
        "cfgB": {"class_type": "CFGOverride", "inputs": {"model": ["unet", 0], "cfg": 1.0, "start_percent": 0.769,
                                                        "end_percent": 1.0}},
        "rB": {"class_type": "RescaleCFG", "inputs": {"model": ["cfgB", 0], "multiplier": 0.5}},
        "shp": {"class_type": "Trellis2ShapeStage", "inputs": {"positive": ["cond", 0], "negative": ["cond", 1],
                                                              "voxel": ["vox", 0]}},
        "ks1": {"class_type": "KSampler", "inputs": {"model": ["rB", 0], "positive": ["shp", 0], "negative": ["shp", 1],
                                                     "latent_image": ["shp", 2], "seed": seed, "steps": 20, "cfg": 7.5,
                                                     "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
    }
    if res > 512:
        g["up"] = {"class_type": "Trellis2UpsampleStage", "inputs": {"positive": ["shp", 0], "negative": ["shp", 1],
                                                                   "shape_latent": ["ks1", 0], "vae": ["svae", 0],
                                                                   "target_resolution": res}}
        g["ks2"] = {"class_type": "KSampler", "inputs": {"model": ["rB", 0], "positive": ["up", 0], "negative": ["up", 1],
                                                         "latent_image": ["up", 2], "seed": seed, "steps": 12, "cfg": 7.5,
                                                         "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}}
        shape_lat, tpos = ["ks2", 0], "up"
    else:
        shape_lat, tpos = ["ks1", 0], "shp"
    g.update({
        "dshape": {"class_type": "VaeDecodeShapeTrellis", "inputs": {"samples": shape_lat, "vae": ["svae", 0]}},
        "tst": {"class_type": "Trellis2TextureStage", "inputs": {"positive": [tpos, 0], "negative": [tpos, 1],
                                                               "shape_latent": shape_lat}},
        "ks3": {"class_type": "KSampler", "inputs": {"model": ["unet", 0], "positive": ["tst", 0], "negative": ["tst", 1],
                                                     "latent_image": ["tst", 2], "seed": seed + 1, "steps": 12, "cfg": 1.0,
                                                     "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0}},
        "dtex": {"class_type": "VaeDecodeTextureTrellis", "inputs": {"samples": ["ks3", 0], "vae": ["tvae", 0],
                                                                    "shape_subdivides": ["dshape", 1]}},
        # pos-processo do template: remesh solido, decimar, UV, assar cor/metal/rugosidade + normal + AO
        "rem": {"class_type": "RemeshMesh", "inputs": {"mesh": ["dshape", 0], "resolution": 768, "sign_mode": "solid",
                                                       "sign_mode.fill": 20.0, "sign_mode.qef": False, "band": 1.0,
                                                       "project_back": 0.0, "fix_poles": False, "smooth_iters": 20,
                                                       "drop_small_components": 0.01, "precluster_max_verts": 20000000}},
        "dec": {"class_type": "DecimateMesh", "inputs": {"mesh": ["rem", 0], "target_face_count": decimate,
                                                         "placement_mode": "midpoint"}},
        "sm": {"class_type": "MeshSmoothNormals", "inputs": {"mesh": ["dec", 0], "crease_angle": 180.0}},
        "uv": {"class_type": "UnwrapMesh", "inputs": {"mesh": ["sm", 0], "segmenter": "pec", "resolution": tex,
                                                      "padding": 1, "weld_distance": 0.0002}},
        "bake": {"class_type": "BakeTextureFromVoxel", "inputs": {"mesh": ["uv", 0], "voxel_colors": ["dtex", 0],
                                                                  "reference_mesh": ["dshape", 0], "texture_size": tex}},
        "nrm": {"class_type": "BakeNormalMapFromMesh", "inputs": {"low_poly": ["uv", 0], "high_poly": ["rem", 0],
                                                                  "resolution": tex, "cage_distance": 0.05,
                                                                  "ignore_backfaces": True}},
        "ao": {"class_type": "BakeAmbientOcclusion", "inputs": {"low_poly": ["uv", 0], "high_poly": ["rem", 0],
                                                                "resolution": 1024, "samples": 64, "max_distance": 0.71,
                                                                "strength": 1.0, "bias": 0.01}},
        "apply": {"class_type": "ApplyTextureToMesh", "inputs": {"mesh": ["uv", 0], "base_color": ["bake", 0],
                                                                 "metallic": ["bake", 1], "roughness": ["bake", 2],
                                                                 "occlusion": ["ao", 0], "normal_map": ["nrm", 0]}},
        "sm2": {"class_type": "MeshSmoothNormals", "inputs": {"mesh": ["apply", 0], "crease_angle": 180.0}},
        "save": {"class_type": "SaveGLB", "inputs": {"mesh": ["sm2", 0], "filename_prefix": prefix}},
        "savec": {"class_type": "SaveImage", "inputs": {"images": ["crop", 0], "filename_prefix": prefix + "_input"}},
    })
    return g


class VramSampler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.peak, self.stop = 0, False

    def run(self):
        while not self.stop:
            try:
                v = int(subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                                text=True).split()[0])
                self.peak = max(self.peak, v)
            except Exception:
                pass
            time.sleep(0.5)


def vram_now():
    return int(subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                       text=True).split()[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True, help="caminho do .glb de saida")
    ap.add_argument("--res", type=int, default=1024, choices=[512, 1024, 1536])
    ap.add_argument("--tex", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--decimate", type=int, default=300000, help="faces maximas antes da UV (o otimizador reduz depois)")
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    name = upload(Path(a.image))
    prefix = f"gen3d/{out.stem}_{int(time.time())}"
    base = vram_now()
    s = VramSampler()
    s.start()
    t0 = time.time()
    pid = json.loads(http("/prompt", json.dumps({"prompt": build(name, a.res, a.tex, a.seed, a.decimate, prefix),
                                                 "client_id": "gen3d"}).encode()))["prompt_id"]
    while True:
        time.sleep(2)
        h = json.loads(http(f"/history/{pid}"))
        if pid in h:
            st = h[pid]["status"]
            if st.get("completed") or st.get("status_str") in ("success", "error"):
                break
    dt = time.time() - t0
    s.stop = True
    if st.get("status_str") != "success":
        msgs = [m for m in st.get("messages", []) if m[0] == "execution_error"]
        raise SystemExit(f"ERRO: {json.dumps(msgs)[:3000]}")
    glbs = sorted((COMFY_DIR / "output").glob(prefix + "*.glb"))
    if not glbs:
        raise SystemExit("ERRO: nenhum GLB salvo")
    shutil.copy2(glbs[-1], out)
    for p in (COMFY_DIR / "output").glob(prefix + "_input*.png"):
        shutil.copy2(p, out.with_name(out.stem + "_input.png"))
    rep = {"engine": "trellis2-comfy-native", "model": "trellis_2_int8_convrot", "res": a.res, "tex": a.tex,
           "seed": a.seed, "seconds": round(dt, 1), "vram_baseline_mb": base, "vram_peak_total_mb": s.peak,
           "vram_peak_delta_mb": s.peak - base, "glb": str(out)}
    out.with_suffix(".json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
