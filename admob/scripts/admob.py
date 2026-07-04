#!/usr/bin/env python3
"""admob.py — CLI da AdMob API (relatórios de receita/eCPM + inventário).

A AdMob API só aceita OAuth de USUÁRIO (não aceita service account), então o
setup é: OAuth client "Desktop" + um consentimento único do dono da conta
(ver SETUP.md). Depois disso o refresh token funciona sem interação.

Credenciais (fora do repo, chmod 600):
  ~/.config/bobagi-google/admob-client.json  — client_id/client_secret (aceita o
                                               JSON baixado do GCP com chave "installed")
  ~/.config/bobagi-google/admob-token.json   — refresh_token (gerado por `auth`)

Uso:
  admob.py auth                      # consentimento único (gera o refresh token)
  admob.py doctor
  admob.py accounts
  admob.py apps
  admob.py adunits
  admob.py report [--days 7] [--by DATE|COUNTRY|AD_UNIT|FORMAT|APP]
  admob.py create-adunit --app APP_ID --name NOME --format BANNER|INTERSTITIAL|REWARDED

Escrita (create-adunit etc.) é "limited access" na API do Google — a maioria
das contas recebe 403; o comando tenta e, se negado, imprime o passo manual.
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CFG_DIR = os.path.expanduser(os.environ.get("ADMOB_CFG_DIR", "~/.config/bobagi-google"))
CLIENT_PATH = os.path.join(CFG_DIR, "admob-client.json")
TOKEN_PATH = os.path.join(CFG_DIR, "admob-token.json")
SCOPES = "https://www.googleapis.com/auth/admob.readonly https://www.googleapis.com/auth/admob.monetization"
REDIRECT = "http://localhost:8765"
API = "https://admob.googleapis.com/v1beta"


def die(msg: str, code: int = 1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def load_client() -> dict:
    if not os.path.exists(CLIENT_PATH):
        die(f"OAuth client não encontrado em {CLIENT_PATH}. Siga o SETUP.md da skill admob.")
    with open(CLIENT_PATH) as fh:
        data = json.load(fh)
    return data.get("installed", data)


def http_json(url: str, data: bytes = None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')}") from e


def cmd_auth(_args):
    client = load_client()
    params = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    print("1) Abra esta URL no navegador da SUA máquina, logado na conta dona do AdMob:\n")
    print(f"https://accounts.google.com/o/oauth2/v2/auth?{params}\n")
    print("2) Aceite o consentimento. O navegador vai redirecionar para um endereço")
    print(f"   {REDIRECT}/?code=... que NÃO vai carregar (normal). Copie da barra de")
    print("   endereços o valor do parâmetro `code` (ou cole a URL inteira).\n")
    raw = input("3) Cole aqui o code (ou a URL inteira): ").strip()
    if "code=" in raw:
        raw = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)["code"][0]
    body = urllib.parse.urlencode(
        {
            "code": raw,
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "redirect_uri": REDIRECT,
            "grant_type": "authorization_code",
        }
    ).encode()
    tok = http_json("https://oauth2.googleapis.com/token", data=body)
    if "refresh_token" not in tok:
        die(f"resposta sem refresh_token (revogue o acesso antigo e tente de novo): {list(tok)}")
    os.makedirs(CFG_DIR, exist_ok=True)
    with open(TOKEN_PATH, "w") as fh:
        json.dump({"refresh_token": tok["refresh_token"]}, fh)
    os.chmod(TOKEN_PATH, 0o600)
    print(f"OK: refresh token salvo em {TOKEN_PATH} (chmod 600).")


def access_token() -> str:
    client = load_client()
    if not os.path.exists(TOKEN_PATH):
        die(f"refresh token ausente ({TOKEN_PATH}). Rode: admob.py auth")
    with open(TOKEN_PATH) as fh:
        refresh = json.load(fh)["refresh_token"]
    body = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        }
    ).encode()
    try:
        return http_json("https://oauth2.googleapis.com/token", data=body)["access_token"]
    except RuntimeError as e:
        die(
            f"refresh falhou ({e}).\nSe o consent screen do GCP estiver em modo 'Testing', "
            "o refresh token expira em 7 dias — publique-o em 'In production' (ver SETUP.md) "
            "e rode `admob.py auth` de novo."
        )


def api_get(path: str, token: str):
    return http_json(f"{API}{path}", headers={"Authorization": f"Bearer {token}"})


def publisher_id(token: str) -> str:
    env = os.environ.get("ADMOB_PUBLISHER_ID")
    if env:
        return env
    accounts = api_get("/accounts", token).get("account", [])
    if not accounts:
        die("nenhuma conta AdMob visível para este usuário OAuth.")
    return accounts[0]["publisherId"]


def cmd_doctor(_args):
    print(f"client OAuth : {CLIENT_PATH} {'(ok)' if os.path.exists(CLIENT_PATH) else '(FALTA)'}")
    print(f"refresh token: {TOKEN_PATH} {'(ok)' if os.path.exists(TOKEN_PATH) else '(FALTA — rode auth)'}")
    token = access_token()
    print("token OAuth  : ok")
    pub = publisher_id(token)
    print(f"AdMob API    : ok — publisher {pub}")


def cmd_accounts(_args):
    token = access_token()
    for acc in api_get("/accounts", token).get("account", []):
        print(f"{acc['publisherId']}  ({acc.get('name')}, moeda={acc.get('currencyCode')}, tz={acc.get('reportingTimeZone')})")


def cmd_apps(_args):
    token = access_token()
    pub = publisher_id(token)
    apps = api_get(f"/accounts/{pub}/apps?pageSize=100", token).get("apps", [])
    for a in apps:
        info = a.get("linkedAppInfo", {}) or a.get("manualAppInfo", {})
        print(f"{a['appId']}  platform={a.get('platform')}  {info.get('appStoreId') or info.get('displayName', '')}")


def cmd_adunits(_args):
    token = access_token()
    pub = publisher_id(token)
    units = api_get(f"/accounts/{pub}/adUnits?pageSize=100", token).get("adUnits", [])
    for u in units:
        print(f"{u['adUnitId']}  [{u.get('adFormat')}]  {u.get('displayName')}  app={u.get('appId')}")


def micros(v: dict) -> float:
    return int(v.get("microsValue", 0)) / 1e6


def cmd_report(args):
    token = access_token()
    pub = publisher_id(token)
    end = dt.date.today()
    start = end - dt.timedelta(days=args.days - 1)
    dim = args.by.upper()
    spec = {
        "reportSpec": {
            "dateRange": {
                "startDate": {"year": start.year, "month": start.month, "day": start.day},
                "endDate": {"year": end.year, "month": end.month, "day": end.day},
            },
            "dimensions": [dim],
            "metrics": ["ESTIMATED_EARNINGS", "IMPRESSIONS", "IMPRESSION_RPM", "CLICKS"],
            "localizationSettings": {"currencyCode": "USD"},
            "sortConditions": [{"metric": "ESTIMATED_EARNINGS", "order": "DESCENDING"}],
        }
    }
    rows = http_json(
        f"{API}/accounts/{pub}/networkReport:generate",
        data=json.dumps(spec).encode(),
        headers={"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json"},
    )
    # resposta é um array-stream: [{header},{row},...,{footer}]
    total_earn = total_impr = 0.0
    printed = 0
    print(f"{dim:<28} {'ganhos US$':>12} {'impressões':>11} {'eCPM US$':>9} {'cliques':>8}")
    for item in rows if isinstance(rows, list) else [rows]:
        row = item.get("row")
        if not row:
            continue
        dv = row.get("dimensionValues", {}).get(dim, {})
        label = dv.get("displayLabel") or dv.get("value", "?")
        mv = row.get("metricValues", {})
        earn = micros(mv.get("ESTIMATED_EARNINGS", {}))
        impr = int(mv.get("IMPRESSIONS", {}).get("integerValue", 0))
        rpm = micros(mv.get("IMPRESSION_RPM", {}))
        clicks = int(mv.get("CLICKS", {}).get("integerValue", 0))
        total_earn += earn
        total_impr += impr
        print(f"{str(label)[:28]:<28} {earn:>12.4f} {impr:>11d} {rpm:>9.2f} {clicks:>8d}")
        printed += 1
    if printed == 0:
        print("(sem dados no período — normal com pouco tráfego ou app recém-publicado)")
    else:
        print(f"{'TOTAL':<28} {total_earn:>12.4f} {int(total_impr):>11d}")


def cmd_create_adunit(args):
    token = access_token()
    pub = publisher_id(token)
    body = {
        "appId": args.app,
        "displayName": args.name,
        "adFormat": args.format.upper(),
    }
    try:
        res = http_json(
            f"{API}/accounts/{pub}/adUnits",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        print(f"OK: criado {res.get('adUnitId')} ({res.get('displayName')})")
    except RuntimeError as e:
        if "403" in str(e):
            print(
                "A API negou (403): criação de ad unit é 'limited access' no Google — "
                "contas sem account manager não têm.\n"
                "Caminho manual (2 min): https://apps.admob.com → Apps → Tic Tac Verse → "
                "Ad units → Add ad unit → escolher formato → copiar o ID "
                "ca-app-pub-…/… para o ad_unit_id_provider.dart."
            )
        else:
            die(str(e))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    sub.add_parser("doctor")
    sub.add_parser("accounts")
    sub.add_parser("apps")
    sub.add_parser("adunits")

    rp = sub.add_parser("report")
    rp.add_argument("--days", type=int, default=7)
    rp.add_argument("--by", default="DATE", help="DATE|COUNTRY|AD_UNIT|FORMAT|APP")

    ca = sub.add_parser("create-adunit")
    ca.add_argument("--app", required=True, help="appId AdMob (ver `apps`)")
    ca.add_argument("--name", required=True)
    ca.add_argument("--format", required=True, help="BANNER|INTERSTITIAL|REWARDED")

    args = p.parse_args()
    {
        "auth": cmd_auth,
        "doctor": cmd_doctor,
        "accounts": cmd_accounts,
        "apps": cmd_apps,
        "adunits": cmd_adunits,
        "report": cmd_report,
        "create-adunit": cmd_create_adunit,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
