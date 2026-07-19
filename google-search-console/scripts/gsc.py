#!/usr/bin/env python3
"""
gsc.py — Google Search Console + Site Verification via API, com a MESMA service
account do google-play (claude-play-publisher@bobagi-apps-automation).

Zero dependências de pip: JWT assinado com openssl, HTTP com urllib (mesmo
padrão do gplay.py/admob.py).

A verificação de propriedade é feita por TXT no DNS, criado automaticamente pelo
cf-dns.sh (skill cloudflare) — por isso o fluxo inteiro roda sem o operador:
  token de verificação -> TXT no Cloudflare -> verify -> add -> submit sitemap.

Comandos:
  doctor                          credenciais + APIs + propriedades já verificadas
  verify <dominio>                pega token DNS, cria o TXT e verifica a posse
  add <dominio>                   adiciona a propriedade (sc-domain:) no Search Console
  setup <dominio> [sitemap-url]   verify + add + submit num passo só
  sites                           lista as propriedades da conta
  sitemaps <dominio>              sitemaps submetidos + status/erros
  sitemap-submit <dom> <url>      submete/ressubmete um sitemap
  report <dominio> [dias]         cliques/impressões/CTR/posição + top queries
  pages <dominio> [dias]          páginas com mais cliques
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
    "GSC_SERVICE_ACCOUNT", "/root/.config/bobagi-google/play-service-account.json"
)
CF_DNS = "/root/.claude/skills/cloudflare/scripts/cf-dns.sh"
SCOPE = (
    "https://www.googleapis.com/auth/siteverification "
    "https://www.googleapis.com/auth/webmasters"
)
SV_API = "https://www.googleapis.com/siteVerification/v1"
SC_API = "https://www.googleapis.com/webmasters/v3"


def die(msg: str, code: int = 1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def access_token() -> str:
    if not os.path.exists(SA_PATH):
        die(
            f"service account não encontrada em {SA_PATH}.\n"
            "Veja o SETUP.md desta skill (passo único do operador)."
        )
    with open(SA_PATH) as fh:
        sa = json.load(fh)
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
    data = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": f"{header}.{claims}.{b64url(sig)}",
        }
    ).encode()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(sa["token_uri"], data=data), timeout=30
        ) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        die(f"falha ao obter token OAuth: HTTP {e.code}: {e.read().decode(errors='replace')}")


def api(method: str, url: str, token: str, body=None, quiet404: bool = False):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        if e.code == 404 and quiet404:
            return None
        detail = e.read().decode(errors="replace")
        try:
            detail = json.loads(detail)["error"]["message"]
        except Exception:
            pass
        die(f"{method} {url} -> HTTP {e.code}: {detail}")


def sc_site(domain: str) -> str:
    """Propriedade de DOMÍNIO (cobre http/https e todos os subcaminhos)."""
    return domain if domain.startswith("sc-domain:") else f"sc-domain:{domain}"


def enc(s: str) -> str:
    return urllib.parse.quote(s, safe="")


def bare(domain: str) -> str:
    return domain.replace("sc-domain:", "").rstrip("/")


# ---------------------------------------------------------------------------
# verificação de posse (DNS TXT via Cloudflare)
# ---------------------------------------------------------------------------


def verification_token(domain: str, token: str) -> str:
    res = api(
        "POST",
        f"{SV_API}/token",
        token,
        {
            "site": {"type": "INET_DOMAIN", "identifier": bare(domain)},
            "verificationMethod": "DNS_TXT",
        },
    )
    return res["token"]


def put_txt(domain: str, value: str):
    if not os.access(CF_DNS, os.X_OK):
        die(f"cf-dns.sh não executável em {CF_DNS} (skill cloudflare)")
    out = subprocess.run(
        [CF_DNS, "txt", bare(domain), value], capture_output=True, text=True
    )
    if out.returncode != 0:
        die(f"cf-dns.sh falhou: {out.stderr.strip() or out.stdout.strip()}")
    print(f"  DNS: {out.stdout.strip()}")


def dns_has(domain: str, value: str) -> bool:
    """Confere no resolver público se o TXT já propagou."""
    out = subprocess.run(
        ["dig", "+short", "TXT", bare(domain), "@1.1.1.1"],
        capture_output=True,
        text=True,
    )
    return value in out.stdout


def cmd_verify(args):
    token = access_token()
    dom = bare(args.domain)
    value = verification_token(dom, token)
    print(f"[1/3] token de verificação obtido para {dom}")
    put_txt(dom, value)
    print("[2/3] aguardando propagação do TXT (até 90s)…")
    for i in range(18):
        if dns_has(dom, value):
            print(f"      TXT visível no resolver público após ~{i * 5}s")
            break
        time.sleep(5)
    else:
        print("      AVISO: TXT ainda não visível; tentando verificar mesmo assim")
    res = api(
        "POST",
        f"{SV_API}/webResource?verificationMethod=DNS_TXT",
        token,
        {"site": {"type": "INET_DOMAIN", "identifier": dom}},
    )
    print(f"[3/3] posse VERIFICADA: {res.get('id')}")
    owners = res.get("owners") or []
    if owners:
        print(f"      proprietários: {', '.join(owners)}")


def cmd_add(args):
    token = access_token()
    site = sc_site(args.domain)
    api("PUT", f"{SC_API}/sites/{enc(site)}", token)
    print(f"propriedade adicionada: {site}")


def cmd_sites(args):
    token = access_token()
    res = api("GET", f"{SC_API}/sites", token) or {}
    entries = res.get("siteEntry") or []
    if not entries:
        print("nenhuma propriedade nesta conta (service account)")
        return
    for e in entries:
        print(f"  {e['siteUrl']:<45} {e.get('permissionLevel', '?')}")


def cmd_sitemap_submit(args):
    token = access_token()
    site = sc_site(args.domain)
    api("PUT", f"{SC_API}/sites/{enc(site)}/sitemaps/{enc(args.sitemap)}", token)
    print(f"sitemap submetido: {args.sitemap}")


def cmd_sitemaps(args):
    token = access_token()
    site = sc_site(args.domain)
    res = api("GET", f"{SC_API}/sites/{enc(site)}/sitemaps", token) or {}
    sitemaps = res.get("sitemap") or []
    if not sitemaps:
        print("nenhum sitemap submetido")
        return
    for s in sitemaps:
        n = sum(int(c.get("submitted", 0)) for c in s.get("contents", []) or [])
        warn = s.get("warnings", 0)
        err = s.get("errors", 0)
        pend = " (ainda não processado)" if s.get("isPending") else ""
        print(f"  {s['path']}")
        print(
            f"    URLs: {n} · avisos: {warn} · erros: {err}"
            f" · último download: {s.get('lastDownloaded', '—')}{pend}"
        )


def _query(token, site, days, dimensions, limit):
    end = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 2 * 86400))
    start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - (days + 2) * 86400))
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": limit,
    }
    res = api("POST", f"{SC_API}/sites/{enc(site)}/searchAnalytics/query", token, body)
    return start, end, (res or {}).get("rows") or []


def cmd_report(args):
    token = access_token()
    site = sc_site(args.domain)
    start, end, rows = _query(token, site, args.days, [], 1)
    print(f"Search Console — {bare(args.domain)} ({start} a {end})\n")
    if not rows:
        print("Sem dados ainda. Propriedade nova leva alguns dias para acumular")
        print("(e os dados do Search Console têm ~2 dias de atraso).")
        return
    t = rows[0]
    print(f"  cliques:     {int(t['clicks'])}")
    print(f"  impressões:  {int(t['impressions'])}")
    print(f"  CTR:         {t['ctr'] * 100:.2f}%")
    print(f"  posição méd: {t['position']:.1f}")
    _, _, qrows = _query(token, site, args.days, ["query"], 25)
    if qrows:
        print("\n  Top buscas (query · cliques · impressões · posição):")
        for r in qrows:
            print(
                f"    {r['keys'][0][:52]:<52} {int(r['clicks']):>5} "
                f"{int(r['impressions']):>7} {r['position']:>6.1f}"
            )


def cmd_pages(args):
    token = access_token()
    site = sc_site(args.domain)
    start, end, rows = _query(token, site, args.days, ["page"], 25)
    print(f"Páginas com mais cliques ({start} a {end}):\n")
    if not rows:
        print("Sem dados ainda.")
        return
    for r in rows:
        print(
            f"  {r['keys'][0][:60]:<60} {int(r['clicks']):>5} "
            f"{int(r['impressions']):>7} {r['position']:>6.1f}"
        )


def real_sitemap(url: str) -> bool:
    """
    O sitemap existe DE VERDADE? Uma SPA com catch-all devolve o index.html com
    HTTP 200 para qualquer path — submeter isso registra erro no Search Console.
    Só aceita se o corpo começar como XML de sitemap.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "gsc.py"})
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                return False
            head = r.read(200).decode(errors="replace").lstrip()
    except Exception:
        return False
    return head.startswith("<?xml") or head.startswith("<urlset") or head.startswith("<sitemapindex")


def cmd_setup(args):
    """Fluxo completo: verificar posse, adicionar propriedade e submeter sitemap."""
    dom = bare(args.domain)
    sitemap = args.sitemap or f"https://{dom}/sitemap.xml"
    cmd_verify(argparse.Namespace(domain=dom))
    print()
    cmd_add(argparse.Namespace(domain=dom))
    if real_sitemap(sitemap):
        cmd_sitemap_submit(argparse.Namespace(domain=dom, sitemap=sitemap))
    else:
        print(f"sitemap PULADO — {sitemap} não é um XML de sitemap válido.")
        print("  (sem sitemap o Google ainda rastreia seguindo links; para acelerar,")
        print("   gere um e rode: gsc.py sitemap-submit <dominio> <url>)")
    print("\npronto — a indexação começa em horas/dias. Acompanhe com:")
    print(f"  gsc.py sitemaps {dom}    (o Google processou o sitemap?)")
    print(f"  gsc.py report {dom}      (por quais buscas o site aparece)")


def cmd_doctor(args):
    print(f"service account: {SA_PATH}")
    if not os.path.exists(SA_PATH):
        die("arquivo não existe — ver SETUP.md")
    with open(SA_PATH) as fh:
        sa = json.load(fh)
    print(f"  client_email: {sa.get('client_email')}")
    print(f"  project:      {sa.get('project_id')}")
    token = access_token()
    print("token OAuth (siteverification + webmasters): OK")
    res = api("GET", f"{SV_API}/webResource", token) or {}
    items = res.get("items") or []
    print(f"domínios verificados por esta conta: {len(items)}")
    for it in items:
        print(f"  {it['site']['identifier']} ({it['site']['type']})")
    sites = (api("GET", f"{SC_API}/sites", token) or {}).get("siteEntry") or []
    print(f"propriedades no Search Console: {len(sites)}")
    for s in sites:
        print(f"  {s['siteUrl']} ({s.get('permissionLevel')})")
    print(f"cf-dns.sh: {'OK' if os.access(CF_DNS, os.X_OK) else 'AUSENTE'} ({CF_DNS})")


def main():
    p = argparse.ArgumentParser(description="Google Search Console via API")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    sub.add_parser("sites").set_defaults(fn=cmd_sites)

    sp = sub.add_parser("verify")
    sp.add_argument("domain")
    sp.set_defaults(fn=cmd_verify)

    sp = sub.add_parser("add")
    sp.add_argument("domain")
    sp.set_defaults(fn=cmd_add)

    sp = sub.add_parser("setup")
    sp.add_argument("domain")
    sp.add_argument("sitemap", nargs="?")
    sp.set_defaults(fn=cmd_setup)

    sp = sub.add_parser("sitemaps")
    sp.add_argument("domain")
    sp.set_defaults(fn=cmd_sitemaps)

    sp = sub.add_parser("sitemap-submit")
    sp.add_argument("domain")
    sp.add_argument("sitemap")
    sp.set_defaults(fn=cmd_sitemap_submit)

    sp = sub.add_parser("report")
    sp.add_argument("domain")
    sp.add_argument("days", nargs="?", type=int, default=28)
    sp.set_defaults(fn=cmd_report)

    sp = sub.add_parser("pages")
    sp.add_argument("domain")
    sp.add_argument("days", nargs="?", type=int, default=28)
    sp.set_defaults(fn=cmd_pages)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
