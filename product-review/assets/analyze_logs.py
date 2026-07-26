#!/usr/bin/env python3
"""Analisa os access logs do nginx (formato log_geo) separando humano vs bot."""
import re, sys, collections, json

import sys
LOG = sys.argv[1] if len(sys.argv) > 1 else "/tmp/geo14d.log"

# host ip [date +0000] "METHOD path proto" status bytes "referer" "ua" CC Country
LINE = re.compile(
    r'^(?P<host>\S+) (?P<ip>\S+) \[(?P<ts>[^\]]+)\] "(?P<req>[^"]*)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+) "(?P<ref>[^"]*)" "(?P<ua>[^"]*)" '
    r'(?P<cc>\S+) (?P<cname>.*)$'
)

BOT_RE = re.compile(
    r'bot|crawl|spider|slurp|scan|curl|wget|python-requests|go-http|libwww|'
    r'headless|semrush|ahrefs|mj12|dotbot|petal|bingpreview|facebookexternal|'
    r'zgrab|masscan|nmap|censys|expanse|internet-?measurement|paloalto|'
    r'httpx|nuclei|zoominfo|dataprovider|netcraft|monitor|uptime|检查|okhttp',
    re.I)

ATTACK_RE = re.compile(
    r'wp-|wordpress|/\.env|/\.git|phpmyadmin|/vendor/|xmlrpc|/shell|/cgi-bin|'
    r'/config\.|/backup|/admin/|eval-stdin|think/|/boaform|/HNAP|\.php',
    re.I)

hosts = collections.defaultdict(lambda: {
    "total": 0, "human": 0, "bot": 0, "attack": 0,
    "ips_h": set(), "ips_all": set(), "status": collections.Counter(),
    "paths_h": collections.Counter(), "cc_h": collections.Counter(),
    "ua_h": collections.Counter(), "ref_h": collections.Counter(),
    "days": collections.Counter(), "bytes": 0,
})

bad = 0
with open(LOG, errors="replace") as f:
    for line in f:
        m = LINE.match(line)
        if not m:
            bad += 1
            continue
        d = m.groupdict()
        host = d["host"].lower()
        if host.startswith("www."):
            host = host[4:]
        h = hosts[host]
        ua = d["ua"]
        req = d["req"]
        path = req.split(" ")[1] if len(req.split(" ")) > 1 else req
        is_bot = bool(BOT_RE.search(ua)) or ua in ("-", "")
        is_attack = bool(ATTACK_RE.search(path))
        h["total"] += 1
        h["ips_all"].add(d["ip"])
        h["status"][d["status"]] += 1
        h["bytes"] += int(d["bytes"])
        day = d["ts"][:11]
        if is_attack:
            h["attack"] += 1
        elif is_bot:
            h["bot"] += 1
        else:
            h["human"] += 1
            h["ips_h"].add(d["ip"])
            h["paths_h"][path.split("?")[0][:70]] += 1
            h["cc_h"][d["cname"]] += 1
            h["ua_h"][ua[:60]] += 1
            h["days"][day] += 1
            ref = d["ref"]
            if ref and ref != "-" and "bobagi" not in ref:
                h["ref_h"][ref[:70]] += 1

print(f"linhas nao parseadas: {bad}\n")
rows = sorted(hosts.items(), key=lambda kv: -kv[1]["human"])
print(f"{'HOST':<32} {'TOTAL':>7} {'HUMANO':>7} {'BOT':>7} {'ATAQUE':>7} {'IPs-H':>6} {'DIAS':>5}")
for host, h in rows:
    print(f"{host:<32} {h['total']:>7} {h['human']:>7} {h['bot']:>7} "
          f"{h['attack']:>7} {len(h['ips_h']):>6} {len(h['days']):>5}")

print("\n\n======== DETALHE POR HOST (só tráfego humano) ========")
for host, h in rows:
    if h["human"] < 5:
        continue
    print(f"\n### {host}  - {h['human']} reqs humanos / {len(h['ips_h'])} IPs únicos")
    print("  status:", dict(h["status"].most_common(6)))
    print("  paises:", dict(h["cc_h"].most_common(6)))
    print("  top paths:")
    for p, c in h["paths_h"].most_common(10):
        print(f"     {c:>5}  {p}")
    if h["ref_h"]:
        print("  referrers externos:")
        for r, c in h["ref_h"].most_common(5):
            print(f"     {c:>5}  {r}")
    print("  por dia:", dict(sorted(h["days"].items())))
