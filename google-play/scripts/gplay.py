#!/usr/bin/env python3
"""gplay.py — CLI da Google Play Developer API (androidpublisher v3).

Autentica com uma SERVICE ACCOUNT (JSON) assinando o JWT via binário `openssl`,
então não depende de nenhum pacote pip — só python3 + openssl + curl.

Credenciais (fora do repo, chmod 600):
  ~/.config/bobagi-google/play-service-account.json   (override: GPLAY_SA_JSON)

Pacote padrão: com.bobagi.tictacverse (override: GPLAY_PACKAGE ou --package).

Uso:
  gplay.py doctor
  gplay.py tracks [--package PKG]
  gplay.py bundles [--package PKG]
  gplay.py upload --aab ARQ [--track internal] [--notes TXT] [--notes-file ARQ]
                  [--rollout 1.0] [--package PKG]
  gplay.py promote --from-track internal --to-track production [--rollout 0.2]
  gplay.py rollout --fraction 0.5 [--track production]
  gplay.py reviews [--limit 10]
  gplay.py reviews-reply --review-id ID --text TXT
  gplay.py listing [--lang pt-BR]
  gplay.py listing-set --lang pt-BR [--title T] [--short S] [--full ARQ]

Trava de segurança: qualquer escrita no track `production` exige
GPLAY_CONFIRM_PROD=yes no ambiente (setar só depois de o operador confirmar).
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

SA_PATH = os.environ.get(
    "GPLAY_SA_JSON",
    os.path.expanduser("~/.config/bobagi-google/play-service-account.json"),
)
DEFAULT_PACKAGE = os.environ.get("GPLAY_PACKAGE", "com.bobagi.tictacverse")
SCOPE = "https://www.googleapis.com/auth/androidpublisher"
API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
UPLOAD_API = (
    "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications"
)


def die(msg: str, code: int = 1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def load_sa() -> dict:
    if not os.path.exists(SA_PATH):
        die(
            f"service account não encontrada em {SA_PATH}.\n"
            "Siga o SETUP.md da skill google-play (passo único do operador)."
        )
    with open(SA_PATH) as fh:
        return json.load(fh)


def access_token() -> str:
    sa = load_sa()
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = b64url(
        json.dumps(
            {
                "iss": sa["client_email"],
                "scope": SCOPE,
                "aud": sa["token_uri"],
                "iat": now,
                "exp": now + 3600,
            }
        ).encode()
    )
    signing_input = f"{header}.{claims}".encode()
    fd, key_path = tempfile.mkstemp(suffix=".pem")
    try:
        with os.fdopen(fd, "w") as kf:
            kf.write(sa["private_key"])
        sig = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input,
            capture_output=True,
            check=True,
        ).stdout
    finally:
        os.unlink(key_path)
    assertion = f"{header}.{claims}.{b64url(sig)}"
    data = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode()
    req = urllib.request.Request(sa["token_uri"], data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        die(f"falha ao obter token OAuth: HTTP {e.code}: {e.read().decode(errors='replace')}")


def api(method: str, path: str, token: str, body=None, ok404=False):
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        if ok404 and e.code == 404:
            return None
        err = e.read().decode(errors="replace")
        die(f"HTTP {e.code} em {method} {path}:\n{err}")


def new_edit(pkg: str, token: str) -> str:
    return api("POST", f"/{pkg}/edits", token, body={})["id"]


def delete_edit(pkg: str, edit_id: str, token: str):
    api("DELETE", f"/{pkg}/edits/{edit_id}", token)


def commit_edit(pkg: str, edit_id: str, token: str):
    """Commita a edit; se o app usa 'managed publishing', re-tenta com
    changesNotSentForReview=true (a mudança fica pendente de envio manual)."""
    url = f"{API}/{pkg}/edits/{edit_id}:commit"
    req = urllib.request.Request(
        url, data=b"", method="POST", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        if "changesNotSentForReview" in err:
            req = urllib.request.Request(
                url + "?changesNotSentForReview=true",
                data=b"",
                method="POST",
                headers={"Authorization": f"Bearer {token}"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                print(
                    "AVISO: commit feito com changesNotSentForReview=true — "
                    "envie para revisão na Play Console (Publishing overview)."
                )
                return json.load(r)
        die(f"HTTP {e.code} no commit:\n{err}")


def guard_production(track: str):
    if track == "production" and os.environ.get("GPLAY_CONFIRM_PROD") != "yes":
        die(
            "escrita no track 'production' bloqueada.\n"
            "Peça confirmação explícita ao operador na conversa e rode de novo com "
            "GPLAY_CONFIRM_PROD=yes no ambiente."
        )


def fmt_release(rel: dict) -> str:
    frac = rel.get("userFraction")
    frac_s = f" rollout={frac:.0%}" if frac else ""
    return (
        f"    - {rel.get('name', '(sem nome)')} | status={rel.get('status')}"
        f" | versionCodes={rel.get('versionCodes', [])}{frac_s}"
    )


# ---------------------------------------------------------------- comandos


def cmd_doctor(args):
    print(f"pacote alvo : {args.package}")
    print(f"credencial  : {SA_PATH}")
    if not os.path.exists(SA_PATH):
        die("arquivo da service account NÃO existe. Siga o SETUP.md.")
    mode = oct(os.stat(SA_PATH).st_mode & 0o777)
    print(f"permissões  : {mode} {'(ok)' if mode == '0o600' else '(recomendo chmod 600)'}")
    sa = load_sa()
    print(f"SA e-mail   : {sa.get('client_email')}")
    for tool in ("openssl", "curl"):
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            die(f"binário obrigatório ausente: {tool}")
    print("openssl/curl: ok")
    token = access_token()
    print("token OAuth : ok")
    edit = new_edit(args.package, token)
    delete_edit(args.package, edit, token)
    print("Play API    : ok — service account tem acesso ao app. Tudo pronto.")


def cmd_tracks(args):
    token = access_token()
    edit = new_edit(args.package, token)
    try:
        tracks = api("GET", f"/{args.package}/edits/{edit}/tracks", token)
    finally:
        delete_edit(args.package, edit, token)
    for t in tracks.get("tracks", []):
        print(f"track: {t['track']}")
        for rel in t.get("releases", []):
            print(fmt_release(rel))


def cmd_bundles(args):
    token = access_token()
    edit = new_edit(args.package, token)
    try:
        bundles = api("GET", f"/{args.package}/edits/{edit}/bundles", token)
    finally:
        delete_edit(args.package, edit, token)
    for b in bundles.get("bundles", []):
        print(f"versionCode={b['versionCode']} sha256={b.get('sha256', '?')}")


def _release_notes(args):
    text = args.notes
    if args.notes_file:
        with open(args.notes_file) as fh:
            text = fh.read().strip()
    if not text:
        return None
    return [
        {"language": lang, "text": text} for lang in ("pt-BR", "en-US", "es-ES")
    ]


def cmd_upload(args):
    guard_production(args.track)
    if not os.path.exists(args.aab):
        die(f"arquivo não existe: {args.aab}")
    token = access_token()
    edit = new_edit(args.package, token)
    print(f"edit criada: {edit}")
    print(f"enviando {args.aab} ({os.path.getsize(args.aab) / 1e6:.1f} MB)…")
    url = f"{UPLOAD_API}/{args.package}/edits/{edit}/bundles?uploadType=media"
    out = subprocess.run(
        [
            "curl", "-sS", "--fail-with-body", "-X", "POST",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/octet-stream",
            "--data-binary", f"@{args.aab}",
            url,
        ],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        delete_edit(args.package, edit, token)
        die(f"upload falhou:\n{out.stdout}\n{out.stderr}")
    bundle = json.loads(out.stdout)
    vc = bundle["versionCode"]
    print(f"bundle aceito: versionCode={vc}")

    release = {
        "name": args.release_name or str(vc),
        "versionCodes": [str(vc)],
        "status": "completed" if args.rollout >= 1 else "inProgress",
    }
    if args.rollout < 1:
        release["userFraction"] = args.rollout
    notes = _release_notes(args)
    if notes:
        release["releaseNotes"] = notes
    api(
        "PUT",
        f"/{args.package}/edits/{edit}/tracks/{args.track}",
        token,
        body={"track": args.track, "releases": [release]},
    )
    commit_edit(args.package, edit, token)
    print(f"OK: versionCode {vc} publicado no track '{args.track}' "
          f"(status={release['status']}).")


def cmd_promote(args):
    guard_production(args.to_track)
    token = access_token()
    edit = new_edit(args.package, token)
    src = api("GET", f"/{args.package}/edits/{edit}/tracks/{args.from_track}", token, ok404=True)
    if not src or not src.get("releases"):
        delete_edit(args.package, edit, token)
        die(f"track de origem '{args.from_track}' sem releases.")
    rel = dict(src["releases"][0])
    rel["status"] = "completed" if args.rollout >= 1 else "inProgress"
    rel.pop("userFraction", None)
    if args.rollout < 1:
        rel["userFraction"] = args.rollout
    api(
        "PUT",
        f"/{args.package}/edits/{edit}/tracks/{args.to_track}",
        token,
        body={"track": args.to_track, "releases": [rel]},
    )
    commit_edit(args.package, edit, token)
    print(f"OK: {rel.get('versionCodes')} promovido "
          f"{args.from_track} → {args.to_track} (rollout={args.rollout:.0%}).")


def cmd_rollout(args):
    guard_production(args.track)
    token = access_token()
    edit = new_edit(args.package, token)
    cur = api("GET", f"/{args.package}/edits/{edit}/tracks/{args.track}", token, ok404=True)
    if not cur or not cur.get("releases"):
        delete_edit(args.package, edit, token)
        die(f"track '{args.track}' sem release para ajustar.")
    rel = dict(cur["releases"][0])
    if args.fraction >= 1:
        rel["status"] = "completed"
        rel.pop("userFraction", None)
    else:
        rel["status"] = "inProgress"
        rel["userFraction"] = args.fraction
    api(
        "PUT",
        f"/{args.package}/edits/{edit}/tracks/{args.track}",
        token,
        body={"track": args.track, "releases": [rel]},
    )
    commit_edit(args.package, edit, token)
    print(f"OK: rollout do track '{args.track}' agora em {args.fraction:.0%}.")


def cmd_reviews(args):
    token = access_token()
    res = api("GET", f"/{args.package}/reviews?maxResults={args.limit}", token)
    reviews = res.get("reviews", [])
    if not reviews:
        print("Nenhuma avaliação recente via API (a API só expõe as últimas semanas).")
        return
    for rv in reviews:
        uc = rv["comments"][0]["userComment"]
        stars = uc.get("starRating", "?")
        text = (uc.get("text") or "").strip().replace("\n", " ")
        print(f"[{stars}★] id={rv['reviewId']} — {text[:160]}")


def cmd_reviews_reply(args):
    token = access_token()
    api(
        "POST",
        f"/{args.package}/reviews/{args.review_id}:reply",
        token,
        body={"replyText": args.text},
    )
    print("OK: resposta publicada.")


def cmd_details(args):
    token = access_token()
    edit = new_edit(args.package, token)
    try:
        data = api("GET", f"/{args.package}/edits/{edit}/details", token)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    finally:
        delete_edit(args.package, edit, token)


def cmd_details_set(args):
    # ATENÇÃO: contactWebsite é onde o rastreador do AdMob procura o app-ads.txt.
    token = access_token()
    edit = new_edit(args.package, token)
    body = {}
    if args.website:
        body["contactWebsite"] = args.website
    if args.email:
        body["contactEmail"] = args.email
    if not body:
        delete_edit(args.package, edit, token)
        die("nada para alterar (use --website e/ou --email)")
    api("PATCH", f"/{args.package}/edits/{edit}/details", token, body=body)
    commit_edit(args.package, edit, token)
    print("OK: detalhes de contato atualizados.")


def cmd_listing(args):
    token = access_token()
    edit = new_edit(args.package, token)
    try:
        if args.lang:
            data = api(
                "GET", f"/{args.package}/edits/{edit}/listings/{args.lang}", token, ok404=True
            )
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            data = api("GET", f"/{args.package}/edits/{edit}/listings", token)
            for l in data.get("listings", []):
                print(f"[{l['language']}] {l.get('title')}\n  short: {l.get('shortDescription')}")
    finally:
        delete_edit(args.package, edit, token)


def cmd_listing_set(args):
    token = access_token()
    edit = new_edit(args.package, token)
    cur = api(
        "GET", f"/{args.package}/edits/{edit}/listings/{args.lang}", token, ok404=True
    ) or {"language": args.lang}
    if args.title:
        cur["title"] = args.title
    if args.short:
        cur["shortDescription"] = args.short
    if args.full:
        with open(args.full) as fh:
            cur["fullDescription"] = fh.read().strip()
    api("PUT", f"/{args.package}/edits/{edit}/listings/{args.lang}", token, body=cur)
    commit_edit(args.package, edit, token)
    print(f"OK: listing [{args.lang}] atualizada.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--package", default=DEFAULT_PACKAGE)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")
    sub.add_parser("tracks")
    sub.add_parser("bundles")

    up = sub.add_parser("upload")
    up.add_argument("--aab", required=True)
    up.add_argument("--track", default="internal")
    up.add_argument("--notes")
    up.add_argument("--notes-file")
    up.add_argument("--rollout", type=float, default=1.0)
    up.add_argument("--release-name")

    pr = sub.add_parser("promote")
    pr.add_argument("--from-track", required=True)
    pr.add_argument("--to-track", required=True)
    pr.add_argument("--rollout", type=float, default=1.0)

    ro = sub.add_parser("rollout")
    ro.add_argument("--fraction", type=float, required=True)
    ro.add_argument("--track", default="production")

    rv = sub.add_parser("reviews")
    rv.add_argument("--limit", type=int, default=10)

    rr = sub.add_parser("reviews-reply")
    rr.add_argument("--review-id", required=True)
    rr.add_argument("--text", required=True)

    sub.add_parser("details")

    ds = sub.add_parser("details-set")
    ds.add_argument("--website")
    ds.add_argument("--email")

    li = sub.add_parser("listing")
    li.add_argument("--lang")

    ls = sub.add_parser("listing-set")
    ls.add_argument("--lang", required=True)
    ls.add_argument("--title")
    ls.add_argument("--short")
    ls.add_argument("--full", help="arquivo .txt com a descrição longa")

    args = p.parse_args()
    handlers = {
        "doctor": cmd_doctor,
        "tracks": cmd_tracks,
        "bundles": cmd_bundles,
        "upload": cmd_upload,
        "promote": cmd_promote,
        "rollout": cmd_rollout,
        "reviews": cmd_reviews,
        "reviews-reply": cmd_reviews_reply,
        "details": cmd_details,
        "details-set": cmd_details_set,
        "listing": cmd_listing,
        "listing-set": cmd_listing_set,
    }
    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
