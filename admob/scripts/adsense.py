#!/usr/bin/env python3
"""AdSense Management API v2 (SOMENTE leitura) com o mesmo OAuth client do AdMob.

Responde, sem abrir o painel: o site está aprovado? tem alerta ou problema de
política? quanto rendeu? A API não aprova site nem cria bloco de anúncio
(isso é no painel, pelo operador).

Credenciais (fora do repo):
  ~/.config/bobagi-google/admob-client.json   OAuth client "installed" (o do AdMob)
  ~/.config/bobagi-google/adsense-token.json  refresh_token com escopo adsense.readonly

Setup único (2 passos, sem terminal interativo):
  adsense.py auth-url              -> abrir a URL logado na conta dona do AdSense
  adsense.py auth-code '<url|code>' -> cola a URL de localhost para onde o Google redirecionou

Uso:
  adsense.py sites | alerts | policy | adclients
  adsense.py report [--days 30]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CFG_DIR = os.path.expanduser(os.environ.get("ADMOB_CFG_DIR", "~/.config/bobagi-google"))
CLIENT_PATH = os.path.join(CFG_DIR, "admob-client.json")
TOKEN_PATH = os.path.join(CFG_DIR, "adsense-token.json")
SCOPES = "https://www.googleapis.com/auth/adsense.readonly"
REDIRECT = "http://localhost:8765"
API = "https://adsense.googleapis.com/v2"


def die(msg, code=1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def load_client():
    if not os.path.exists(CLIENT_PATH):
        die(f"OAuth client não encontrado em {CLIENT_PATH}. Siga o SETUP.md da skill admob.")
    with open(CLIENT_PATH) as fh:
        data = json.load(fh)
    return data.get("installed", data)


def http_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:1500]}") from e


def cmd_auth_url(_a):
    c = load_client()
    q = urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPES, "access_type": "offline", "prompt": "consent",
    })
    print(f"https://accounts.google.com/o/oauth2/v2/auth?{q}")


def cmd_auth_code(a):
    raw = a.code.strip()
    if "code=" in raw:
        raw = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)["code"][0]
    c = load_client()
    tok = http_json("https://oauth2.googleapis.com/token", data=urllib.parse.urlencode({
        "code": raw, "client_id": c["client_id"], "client_secret": c["client_secret"],
        "redirect_uri": REDIRECT, "grant_type": "authorization_code",
    }).encode())
    if "refresh_token" not in tok:
        die(f"resposta sem refresh_token: {list(tok)}")
    os.makedirs(CFG_DIR, exist_ok=True)
    with open(TOKEN_PATH, "w") as fh:
        json.dump({"refresh_token": tok["refresh_token"]}, fh)
    os.chmod(TOKEN_PATH, 0o600)
    print(f"OK: refresh token salvo em {TOKEN_PATH} (chmod 600).")


def access_token():
    if not os.path.exists(TOKEN_PATH):
        die(f"token ausente ({TOKEN_PATH}). Rode: adsense.py auth-url")
    with open(TOKEN_PATH) as fh:
        refresh = json.load(fh)["refresh_token"]
    c = load_client()
    tok = http_json("https://oauth2.googleapis.com/token", data=urllib.parse.urlencode({
        "refresh_token": refresh, "client_id": c["client_id"], "client_secret": c["client_secret"],
        "grant_type": "refresh_token",
    }).encode())
    return tok["access_token"]


def get(path, params=None):
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    return http_json(url, headers={"Authorization": f"Bearer {access_token()}"})


def account():
    accs = get("accounts").get("accounts", [])
    if not accs:
        die("nenhuma conta AdSense visível para este login")
    return accs[0]["name"]


def cmd_sites(_a):
    acc = account()
    print(f"conta: {acc}")
    for s in get(f"{acc}/sites").get("sites", []):
        print(f"  {s.get('domain'):<30} state={s.get('state')}  autoAds={s.get('autoAdsEnabled')}")


def cmd_alerts(_a):
    alerts = get(f"{account()}/alerts").get("alerts", [])
    if not alerts:
        print("nenhum alerta")
    for x in alerts:
        print(f"[{x.get('severity')}] {x.get('type')}: {x.get('message')}")


def cmd_policy(_a):
    issues = get(f"{account()}/policyIssues").get("policyIssues", [])
    if not issues:
        print("nenhum problema de política")
    for x in issues:
        print(json.dumps({k: x.get(k) for k in ("site", "entityType", "action", "policyTopics", "uri",
                                                "adRequestCount", "lastDetectedDate", "warningEscalationDate")},
                         ensure_ascii=False))


def cmd_adclients(_a):
    for c in get(f"{account()}/adclients").get("adClients", []):
        print(f"  {c.get('name')}  product={c.get('productCode')}  state={c.get('state')}")


def cmd_report(a):
    acc = account()
    r = get(f"{acc}/reports:generate", {
        "dateRange": "CUSTOM",
        **_range(a.days),
        "dimensions": ["DATE"],
        "metrics": ["PAGE_VIEWS", "AD_REQUESTS", "MATCHED_AD_REQUESTS", "IMPRESSIONS", "CLICKS", "ESTIMATED_EARNINGS"],
    })
    heads = [h["name"] for h in r.get("headers", [])]
    print("  ".join(heads))
    for row in r.get("rows", []):
        print("  ".join(c.get("value", "") for c in row["cells"]))
    tot = r.get("totals", {}).get("cells")
    if tot:
        print("TOTAL " + "  ".join(c.get("value", "") for c in tot))


def _range(days):
    import datetime as dt
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    return {"startDate.year": start.year, "startDate.month": start.month, "startDate.day": start.day,
            "endDate.year": end.year, "endDate.month": end.month, "endDate.day": end.day}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth-url")
    ac = sub.add_parser("auth-code")
    ac.add_argument("code")
    for n in ("sites", "alerts", "policy", "adclients"):
        sub.add_parser(n)
    rp = sub.add_parser("report")
    rp.add_argument("--days", type=int, default=30)
    a = p.parse_args()
    fn = {"auth-url": cmd_auth_url, "auth-code": cmd_auth_code, "sites": cmd_sites, "alerts": cmd_alerts,
          "policy": cmd_policy, "adclients": cmd_adclients, "report": cmd_report}[a.cmd]
    try:
        fn(a)
    except RuntimeError as e:
        die(str(e))


if __name__ == "__main__":
    main()
