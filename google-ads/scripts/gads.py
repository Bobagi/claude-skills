#!/usr/bin/env python3
"""gads.py — CLI da Google Ads API (status de campanha, gasto, CPI, conversões).

Somente LEITURA (GAQL search). A Google Ads API exige, além do OAuth do dono
da conta, um DEVELOPER TOKEN aprovado (Central da API dentro do Google Ads —
ver SETUP.md). Token em nível "conta de teste" NÃO lê contas reais
(erro DEVELOPER_TOKEN_NOT_APPROVED até o acesso Básico ser aprovado).

Credenciais (fora do repo, chmod 600):
  ~/.config/bobagi-google/admob-client.json — OAuth client (REUSADO do AdMob)
  ~/.config/bobagi-google/gads-token.json   — refresh token escopo adwords (`auth`)
  ~/.config/bobagi-google/gads-config.json  — developer_token, customer_id,
                                              api_version (auto), login_customer_id (opcional)

Uso:
  gads.py set-config --developer-token TOKEN [--customer-id 1234567890]
  gads.py auth                    # consentimento único (escopo adwords)
  gads.py doctor
  gads.py accounts                # contas acessíveis pelo usuário OAuth
  gads.py campaigns [--days 7]    # custo/impr/cliques/conversões por campanha
  gads.py groups [--days 7]       # idem por grupo de anúncios
  gads.py daily [--days 14]       # totais por dia
  gads.py search --gaql "SELECT ..."   # consulta GAQL crua (escape hatch)
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

CFG_DIR = os.path.expanduser(os.environ.get("GADS_CFG_DIR", "~/.config/bobagi-google"))
CLIENT_PATH = os.path.join(CFG_DIR, "admob-client.json")  # mesmo OAuth client do AdMob
TOKEN_PATH = os.path.join(CFG_DIR, "gads-token.json")
CONFIG_PATH = os.path.join(CFG_DIR, "gads-config.json")
SCOPE = "https://www.googleapis.com/auth/adwords"
REDIRECT = "http://localhost:8765"
API_HOST = "https://googleads.googleapis.com"
VERSION_CANDIDATES = ["v22", "v21", "v20", "v19", "v18"]


def die(msg: str, code: int = 1):
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def load_client() -> dict:
    if not os.path.exists(CLIENT_PATH):
        die(f"OAuth client não encontrado em {CLIENT_PATH} (é o mesmo do AdMob; ver SETUP.md).")
    with open(CLIENT_PATH) as fh:
        data = json.load(fh)
    return data.get("installed", data)


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as fh:
        return json.load(fh)


def save_config(cfg: dict):
    os.makedirs(CFG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as fh:
        json.dump(cfg, fh, indent=2)
    os.chmod(CONFIG_PATH, 0o600)


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
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    print("1) Abra esta URL no navegador da SUA máquina, logado na conta dona do Google Ads:\n")
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
        die(f"resposta sem refresh_token (revogue o acesso antigo em myaccount.google.com/permissions e tente de novo): {list(tok)}")
    os.makedirs(CFG_DIR, exist_ok=True)
    with open(TOKEN_PATH, "w") as fh:
        json.dump({"refresh_token": tok["refresh_token"]}, fh)
    os.chmod(TOKEN_PATH, 0o600)
    print(f"OK: refresh token salvo em {TOKEN_PATH} (chmod 600).")


def cmd_set_config(args):
    cfg = load_config()
    if args.developer_token:
        cfg["developer_token"] = args.developer_token.strip()
    if args.customer_id:
        cfg["customer_id"] = args.customer_id.replace("-", "").strip()
    if args.login_customer_id:
        cfg["login_customer_id"] = args.login_customer_id.replace("-", "").strip()
    if not cfg:
        die("nada para salvar (use --developer-token / --customer-id)")
    save_config(cfg)
    print(f"OK: config salva em {CONFIG_PATH}: {sorted(cfg)}")


def access_token() -> str:
    client = load_client()
    if not os.path.exists(TOKEN_PATH):
        die(f"refresh token ausente ({TOKEN_PATH}). Rode: gads.py auth")
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
            "o refresh token expira em 7 dias — publique-o e rode `gads.py auth` de novo."
        )


def base_headers(token: str) -> dict:
    cfg = load_config()
    dev = cfg.get("developer_token")
    if not dev:
        die(f"developer token ausente. Rode: gads.py set-config --developer-token XXX (ver SETUP.md)")
    h = {"Authorization": f"Bearer {token}", "developer-token": dev, "Content-Type": "application/json"}
    if cfg.get("login_customer_id"):
        h["login-customer-id"] = cfg["login_customer_id"]
    return h


def friendly_api_error(e: RuntimeError):
    s = str(e)
    if "DEVELOPER_TOKEN_NOT_APPROVED" in s:
        die(
            "o developer token ainda está em nível 'Conta de teste' — não lê contas reais.\n"
            "Solicite o acesso Básico: Google Ads → Ferramentas → Central da API → "
            "'Solicitar acesso básico' (aprovação típica: 1–3 dias úteis). Depois rode de novo."
        )
    if "DEVELOPER_TOKEN_PROHIBITED" in s or "NOT_ADS_USER" in s:
        die(f"a conta OAuth não tem acesso ao Google Ads (logou com o e-mail certo?): {s}")
    die(s)


def api_version(token: str) -> str:
    cfg = load_config()
    ver = cfg.get("api_version")
    if ver:
        return ver
    for v in VERSION_CANDIDATES:
        try:
            http_json(
                f"{API_HOST}/{v}/customers:listAccessibleCustomers",
                headers=base_headers(token),
            )
        except RuntimeError as e:
            if "HTTP 404" in str(e):
                continue
            # 403/401 etc: a versão existe; o erro é de permissão — serve pra fixar a versão
        cfg["api_version"] = v
        save_config(cfg)
        return v
    die("nenhuma versão da Google Ads API respondeu (candidatas: " + ", ".join(VERSION_CANDIDATES) + ")")


def list_accessible(token: str) -> list:
    ver = api_version(token)
    try:
        res = http_json(f"{API_HOST}/{ver}/customers:listAccessibleCustomers", headers=base_headers(token))
    except RuntimeError as e:
        friendly_api_error(e)
    return [r.split("/")[-1] for r in res.get("resourceNames", [])]


def customer_id(token: str) -> str:
    cfg = load_config()
    if cfg.get("customer_id"):
        return cfg["customer_id"]
    ids = list_accessible(token)
    if len(ids) == 1:
        cfg["customer_id"] = ids[0]
        save_config(cfg)
        return ids[0]
    if not ids:
        die("nenhuma conta Google Ads acessível para este usuário OAuth.")
    die("mais de uma conta acessível: " + ", ".join(ids) + f"\nEscolha uma: gads.py set-config --customer-id ID")


def gaql(token: str, query: str) -> list:
    ver = api_version(token)
    cid = customer_id(token)
    rows, page_token = [], None
    while True:
        body = {"query": query}
        if page_token:
            body["pageToken"] = page_token
        try:
            res = http_json(
                f"{API_HOST}/{ver}/customers/{cid}/googleAds:search",
                data=json.dumps(body).encode(),
                headers=base_headers(token),
            )
        except RuntimeError as e:
            friendly_api_error(e)
        rows.extend(res.get("results", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            return rows


def cmd_doctor(_args):
    cfg = load_config()
    print(f"OAuth client   : {CLIENT_PATH} {'(ok)' if os.path.exists(CLIENT_PATH) else '(FALTA)'}")
    print(f"refresh token  : {TOKEN_PATH} {'(ok)' if os.path.exists(TOKEN_PATH) else '(FALTA — rode auth)'}")
    print(f"developer token: {'ok' if cfg.get('developer_token') else 'FALTA — rode set-config (ver SETUP.md)'}")
    token = access_token()
    print("token OAuth    : ok")
    ver = api_version(token)
    print(f"API version    : {ver}")
    ids = list_accessible(token)
    print(f"contas         : {', '.join(ids) or '(nenhuma)'}")
    cid = customer_id(token)
    rows = gaql(token, "SELECT customer.descriptive_name, customer.currency_code, customer.time_zone FROM customer")
    c = rows[0]["customer"] if rows else {}
    print(f"conta ativa    : {cid} — {c.get('descriptiveName')} (moeda={c.get('currencyCode')}, tz={c.get('timeZone')})")
    print("Google Ads API : ok. Tudo pronto.")


def cmd_accounts(_args):
    token = access_token()
    for cid in list_accessible(token):
        print(cid)


def money(micros_val) -> float:
    return int(micros_val or 0) / 1e6


def print_report(rows, key_fn, label_hdr):
    agg = {}
    for r in rows:
        m = r.get("metrics", {})
        label = key_fn(r)
        a = agg.setdefault(label, [0.0, 0, 0, 0.0])
        a[0] += money(m.get("costMicros"))
        a[1] += int(m.get("impressions", 0))
        a[2] += int(m.get("clicks", 0))
        a[3] += float(m.get("conversions", 0.0))
    print(f"{label_hdr:<42} {'custo':>10} {'impr':>8} {'cliques':>8} {'conv':>7} {'CPI/CPA':>8}")
    tc = ti = tk = tv = 0.0
    for label, (cost, impr, clicks, conv) in sorted(agg.items(), key=lambda x: -x[1][0]):
        cpi = cost / conv if conv else 0.0
        tc, ti, tk, tv = tc + cost, ti + impr, tk + clicks, tv + conv
        print(f"{str(label)[:42]:<42} {cost:>10.2f} {impr:>8d} {clicks:>8d} {conv:>7.1f} {cpi:>8.2f}")
    if not agg:
        print("(sem dados no período)")
    else:
        cpi = tc / tv if tv else 0.0
        print(f"{'TOTAL':<42} {tc:>10.2f} {int(ti):>8d} {int(tk):>8d} {tv:>7.1f} {cpi:>8.2f}")
    print("(custo/CPI na moeda da conta; conversões conforme configuradas — p/ campanha de app = instalações)")


def date_clause(days: int) -> str:
    end = dt.date.today()
    start = end - dt.timedelta(days=days - 1)
    return f"segments.date BETWEEN '{start.isoformat()}' AND '{end.isoformat()}'"


def cmd_campaigns(args):
    token = access_token()
    rows = gaql(token, f"""
        SELECT campaign.name, campaign.status, campaign_budget.amount_micros,
               metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions
        FROM campaign WHERE {date_clause(args.days)}""".strip())
    if rows:
        seen = {}
        for r in rows:
            c = r["campaign"]
            seen[c["name"]] = (c.get("status"), money(r.get("campaignBudget", {}).get("amountMicros")))
        for name, (status, budget) in seen.items():
            print(f"[{status}] {name} — orçamento {budget:.2f}/dia")
        print()
    print_report(rows, lambda r: r["campaign"]["name"], "CAMPANHA")


def cmd_groups(args):
    token = access_token()
    rows = gaql(token, f"""
        SELECT ad_group.name, campaign.name,
               metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions
        FROM ad_group WHERE {date_clause(args.days)}""".strip())
    print_report(rows, lambda r: r["adGroup"]["name"], "GRUPO DE ANÚNCIOS")


def cmd_daily(args):
    token = access_token()
    rows = gaql(token, f"""
        SELECT segments.date,
               metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions
        FROM customer WHERE {date_clause(args.days)}""".strip())
    print_report(rows, lambda r: r["segments"]["date"], "DIA")


def cmd_search(args):
    token = access_token()
    rows = gaql(token, args.gaql)
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    sub.add_parser("doctor")
    sub.add_parser("accounts")

    sc = sub.add_parser("set-config")
    sc.add_argument("--developer-token")
    sc.add_argument("--customer-id")
    sc.add_argument("--login-customer-id")

    for name in ("campaigns", "groups", "daily"):
        sp = sub.add_parser(name)
        sp.add_argument("--days", type=int, default=7 if name != "daily" else 14)

    se = sub.add_parser("search")
    se.add_argument("--gaql", required=True)

    args = p.parse_args()
    {
        "auth": cmd_auth,
        "set-config": cmd_set_config,
        "doctor": cmd_doctor,
        "accounts": cmd_accounts,
        "campaigns": cmd_campaigns,
        "groups": cmd_groups,
        "daily": cmd_daily,
        "search": cmd_search,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
