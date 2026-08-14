#!/usr/bin/env python3
"""Chrome Web Store: sobe um novo pacote (.zip) e publica uma extensao via API.

Faz o que a Play Developer API faz para apps, so que para extensao do Chrome:
upload de pacote + publish. NAO edita a ficha (descricao longa, screenshots,
categoria) - isso a API nao cobre; fica no painel. A publicacao passa pela
REVISAO do Google. Roda no HOST, zero pip (stdlib urllib).

Credenciais (chmod 600, FORA de qualquer repo) em ~/.config/bobagi-google/:
  cws-client.json : OAuth client tipo "Aplicativo da Web" (redirect do Playground)
      {"web":{"client_id":"...","client_secret":"..."}}
  cws-token.json  : {"refresh_token":"..."}   (escopo chromewebstore; ver SETUP.md)
  cws-items.json  : (opcional) apelidos -> itemId, e o default
      {"default":"farolivro","items":{"farolivro":"<32-char-id>"}}

Uso:
  cws.py doctor  [--item X]              confere credenciais + token + estado
  cws.py status  [--item X]              estado do rascunho (uploadState, erros)
  cws.py upload  --zip a.zip [--item X]  sobe um pacote novo
  cws.py publish [--target default|trustedTesters] [--item X]
  cws.py upload-publish --zip a.zip [--target ...] [--item X]
  cws.py items                           lista os apelidos configurados

--item aceita um apelido de cws-items.json ou um itemId cru (32 letras). Sem
--item, usa o "default" do cws-items.json. API v1.1 (funciona ate 2026-10-15).
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CFG = Path.home() / ".config" / "bobagi-google"
API = "https://www.googleapis.com/chromewebstore/v1.1"
UPLOAD = "https://www.googleapis.com/upload/chromewebstore/v1.1"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ITEM_RE = re.compile(r"^[a-p]{32}$")  # itemId da CWS


def _items_cfg():
    p = CFG / "cws-items.json"
    return json.loads(p.read_text()) if p.exists() else {}


def resolve_item(arg):
    cfg = _items_cfg()
    items = cfg.get("items", {})
    if arg:
        if arg in items:
            return items[arg]
        if ITEM_RE.match(arg):
            return arg
        sys.exit(f"item '{arg}' nao e um apelido conhecido nem um itemId valido (32 letras a-p)")
    default = cfg.get("default")
    if default and default in items:
        return items[default]
    sys.exit("sem --item e sem 'default' em cws-items.json; passe --item <id|apelido>")


def _client():
    p = CFG / "cws-client.json"
    if not p.exists():
        sys.exit("faltando ~/.config/bobagi-google/cws-client.json (ver SETUP.md)")
    d = json.loads(p.read_text())
    c = d.get("web") or d.get("installed") or d
    if not (c.get("client_id") and c.get("client_secret")):
        sys.exit("cws-client.json sem client_id/client_secret")
    return c["client_id"], c["client_secret"]


def _refresh_token():
    p = CFG / "cws-token.json"
    if not p.exists():
        sys.exit("faltando ~/.config/bobagi-google/cws-token.json (refresh_token; ver SETUP.md)")
    return json.loads(p.read_text())["refresh_token"]


def access_token():
    cid, secret = _client()
    body = urllib.parse.urlencode({
        "client_id": cid, "client_secret": secret,
        "refresh_token": _refresh_token(), "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:300]
        hint = " (refresh token expirou? se o app OAuth esta em 'Testando', refaca o Playground; ver SETUP.md)" if e.code in (400, 401) else ""
        sys.exit(f"falha ao trocar refresh_token (HTTP {e.code}): {detail}{hint}")


def _call(method, url, tok, data=None, extra=None):
    headers = {"Authorization": f"Bearer {tok}", "x-goog-api-version": "2"}
    if extra:
        headers.update(extra)
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip().startswith("{") else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


def status(item):
    code, body = _call("GET", f"{API}/items/{item}?projection=DRAFT", access_token())
    print(code, json.dumps(body, ensure_ascii=False, indent=2) if isinstance(body, dict) else body)
    return body


def upload(item, zip_path):
    data = Path(zip_path).read_bytes()
    code, body = _call("PUT", f"{UPLOAD}/items/{item}", access_token(), data=data,
                       extra={"Content-Type": "application/zip"})
    print("upload:", code, json.dumps(body, ensure_ascii=False) if isinstance(body, dict) else body)
    if not (isinstance(body, dict) and body.get("uploadState") in ("SUCCESS", "IN_PROGRESS")):
        sys.exit(1)


def publish(item, target="default"):
    code, body = _call("POST", f"{API}/items/{item}/publish?publishTarget={target}", access_token(), data=b"")
    print("publish:", code, json.dumps(body, ensure_ascii=False) if isinstance(body, dict) else body)
    if not (isinstance(body, dict) and "OK" in (body.get("status") or [])):
        sys.exit(1)


def doctor(item):
    cid, _ = _client()
    print(f"OAuth client: cws-client.json (…{cid[-24:]})")
    print("refresh_token:", "presente" if (CFG / "cws-token.json").exists() else "FALTANDO")
    print("item:", item)
    print("access_token:", "OK" if access_token() else "falhou")
    status(item)


def main():
    ap = argparse.ArgumentParser(description="Chrome Web Store publish API")
    ap.add_argument("cmd", choices=["doctor", "status", "upload", "publish", "upload-publish", "items"])
    ap.add_argument("--item")
    ap.add_argument("--zip")
    ap.add_argument("--target", default="default", choices=["default", "trustedTesters"])
    a = ap.parse_args()

    if a.cmd == "items":
        print(json.dumps(_items_cfg(), ensure_ascii=False, indent=2))
        return
    item = resolve_item(a.item)
    if a.cmd == "doctor":
        doctor(item)
    elif a.cmd == "status":
        status(item)
    elif a.cmd == "upload":
        if not a.zip:
            sys.exit("upload precisa de --zip")
        upload(item, a.zip)
    elif a.cmd == "publish":
        publish(item, a.target)
    elif a.cmd == "upload-publish":
        if not a.zip:
            sys.exit("upload-publish precisa de --zip")
        upload(item, a.zip)
        publish(item, a.target)


if __name__ == "__main__":
    main()
