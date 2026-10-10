#!/usr/bin/env python3
"""Cliente de linha de comando da Meshy API (texto/imagem para 3D, textura, remesh, rig, animacao, imagens).

Chave em ~/.config/ai-workers/meshy.key (ou env MESHY_API_KEY). Nunca imprime a chave.

Uso:
  meshy.py balance
  meshy.py create <tipo> --body '{"prompt": "..."}' [--wait] [--out pasta]
  meshy.py get <tipo> <id>
  meshy.py wait <tipo> <id> [--out pasta]
  meshy.py download <tipo> <id> --out pasta
  meshy.py library [--q texto]            # biblioteca de animacoes (gratis)
  meshy.py raw METODO /openapi/v1/... [--body json]

Tipos: text-to-3d, image-to-3d, multi-image-to-3d, retexture, remesh, rigging, animations,
       text-to-image, image-to-image. Valores de campo que sao caminho de arquivo local em
       image_url, image_style_url, texture_image_url e reference_image_urls viram data URI.
Fluxo de modelo: text-to-3d preview -> refine (mode no body) -> remesh/rigging/animations.
"""
import argparse, base64, json, mimetypes, os, sys, time, urllib.request, urllib.error

BASE = "https://api.meshy.ai"
PATHS = {
    "text-to-3d": "/openapi/v2/text-to-3d",
    "image-to-3d": "/openapi/v1/image-to-3d",
    "multi-image-to-3d": "/openapi/v1/multi-image-to-3d",
    "retexture": "/openapi/v1/retexture",
    "remesh": "/openapi/v1/remesh",
    "rigging": "/openapi/v1/rigging",
    "animations": "/openapi/v1/animations",
    "text-to-image": "/openapi/v1/text-to-image",
    "image-to-image": "/openapi/v1/image-to-image",
}
FILE_FIELDS = ("image_url", "image_style_url", "texture_image_url")
FILE_LIST_FIELDS = ("image_urls", "reference_image_urls", "multiview_image_urls")


def key():
    k = os.environ.get("MESHY_API_KEY")
    if not k:
        with open(os.path.expanduser("~/.config/ai-workers/meshy.key")) as f:
            k = f.read().strip()
    return k


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        sys.exit("HTTP %d: %s" % (e.code, e.read().decode()[:600]))


def to_data_uri(v):
    if isinstance(v, str) and not v.startswith(("http://", "https://", "data:")) and os.path.isfile(v):
        mime = mimetypes.guess_type(v)[0] or "application/octet-stream"
        with open(v, "rb") as f:
            return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())
    return v


def prep(body):
    for f in FILE_FIELDS:
        if f in body:
            body[f] = to_data_uri(body[f])
    for f in FILE_LIST_FIELDS:
        if f in body:
            body[f] = [to_data_uri(x) for x in body[f]]
    return body


def task_path(kind, tid=""):
    return PATHS[kind] + ("/" + tid if tid else "")


def wait(kind, tid, every=6):
    last = -1
    while True:
        t = call("GET", task_path(kind, tid))
        p = t.get("progress", 0)
        if p != last:
            print("  %s %s %s%%" % (tid[:8], t.get("status"), p), file=sys.stderr)
            last = p
        if t.get("status") in ("SUCCEEDED", "FAILED", "CANCELED"):
            if t["status"] != "SUCCEEDED":
                sys.exit("tarefa %s: %s %s" % (t["status"], tid, json.dumps(t.get("task_error", ""))))
            return t
        time.sleep(every)


def urls(t):
    out = {}
    for k, v in (t.get("model_urls") or {}).items():
        if v:
            out["model." + k] = v
    for i, v in enumerate(t.get("texture_urls") or []):
        for k, u in v.items():
            out["texture%d_%s" % (i, k)] = u
    for i, u in enumerate(t.get("image_urls") or []):
        out["image%d" % i] = u
    for k in ("thumbnail_url", "alpha_thumbnail_url", "animation_glb_url", "animation_fbx_url"):
        if t.get(k):
            out[k] = t[k]
    for k, v in (t.get("result") or {}).items() if isinstance(t.get("result"), dict) else []:
        if isinstance(v, str) and v.startswith("http"):
            out["result_" + k] = v
    return out


def download(t, out):
    os.makedirs(out, exist_ok=True)
    for name, u in urls(t).items():
        ext = os.path.splitext(u.split("?")[0])[1] or ""
        dest = os.path.join(out, name.replace("model.", "") + ext if name.startswith("model.") else name + ext)
        if name.startswith("model."):
            dest = os.path.join(out, "model" + ext)
        urllib.request.urlretrieve(u, dest)
        print("salvo", dest)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("balance")
    c = sp.add_parser("create"); c.add_argument("kind", choices=PATHS); c.add_argument("--body", required=True)
    c.add_argument("--wait", action="store_true"); c.add_argument("--out")
    for n in ("get", "wait", "download"):
        g = sp.add_parser(n); g.add_argument("kind", choices=PATHS); g.add_argument("id"); g.add_argument("--out")
    l = sp.add_parser("library"); l.add_argument("--q", default="")
    r = sp.add_parser("raw"); r.add_argument("method"); r.add_argument("path"); r.add_argument("--body")
    a = ap.parse_args()

    if a.cmd == "balance":
        print(json.dumps(call("GET", "/openapi/v1/balance")))
    elif a.cmd == "create":
        body = prep(json.loads(a.body))
        res = call("POST", task_path(a.kind), body)
        tid = res.get("result") if isinstance(res, dict) else None
        print("id", tid)
        if a.wait and tid:
            t = wait(a.kind, tid)
            print(json.dumps({k: t.get(k) for k in ("id", "status", "consumed_credits")}))
            if a.out:
                download(t, a.out)
    elif a.cmd == "get":
        print(json.dumps(call("GET", task_path(a.kind, a.id)), indent=1))
    elif a.cmd == "wait":
        t = wait(a.kind, a.id)
        print(json.dumps({k: t.get(k) for k in ("id", "status", "consumed_credits")}))
        if a.out:
            download(t, a.out)
    elif a.cmd == "download":
        download(call("GET", task_path(a.kind, a.id)), a.out)
    elif a.cmd == "library":
        lib = call("GET", "/openapi/v1/animations/library?page_size=100" + ("&search=" + a.q if a.q else ""))
        items = lib if isinstance(lib, list) else lib.get("result", lib.get("items", lib))
        print(json.dumps(items, ensure_ascii=False)[:20000])
    elif a.cmd == "raw":
        print(json.dumps(call(a.method.upper(), a.path, json.loads(a.body) if a.body else None), indent=1))


if __name__ == "__main__":
    main()
