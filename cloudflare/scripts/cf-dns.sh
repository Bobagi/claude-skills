#!/usr/bin/env bash
# cf-dns.sh — manage DNS records of the bobagi.space zone on Cloudflare.
# Token: /root/.config/cloudflare/api-token (chmod 600), scoped "Edit zone DNS" for bobagi.space.
# Usage:
#   cf-dns.sh list
#   cf-dns.sh add <subdomain> [ip] [proxied]   # defaults: ip=46.202.144.75, proxied=true (orange cloud)
#   cf-dns.sh delete <subdomain>
set -euo pipefail

ZONE_NAME="bobagi.space"
DEFAULT_IP="46.202.144.75"
TOKEN_FILE="/root/.config/cloudflare/api-token"
API="https://api.cloudflare.com/client/v4"

[ -r "$TOKEN_FILE" ] || { echo "ERRO: token não encontrado em $TOKEN_FILE" >&2; exit 1; }
TOKEN="$(tr -d ' \t\n\r' < "$TOKEN_FILE")"

cf() { # method path [json-body]
  local method="$1" path="$2" body="${3:-}"
  if [ -n "$body" ]; then
    curl -sS -X "$method" "$API$path" -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" --data "$body"
  else
    curl -sS -X "$method" "$API$path" -H "Authorization: Bearer $TOKEN"
  fi
}

die_on_error() { # json
  if [ "$(jq -r '.success' <<<"$1")" != "true" ]; then
    echo "ERRO da API Cloudflare:" >&2
    jq -r '.errors[] | "  [\(.code)] \(.message)"' <<<"$1" >&2
    exit 1
  fi
}

ZONE_ID_FILE="/root/.config/cloudflare/zone-id"

zone_id() {
  # Prefer the pinned zone id (works even when the token lacks Zone:Read and can't list zones)
  if [ -r "$ZONE_ID_FILE" ]; then
    tr -d ' \t\n\r' < "$ZONE_ID_FILE"
    return
  fi
  local res; res="$(cf GET "/zones?name=$ZONE_NAME")"
  die_on_error "$res"
  jq -re '.result[0].id' <<<"$res" || { echo "ERRO: zona $ZONE_NAME não visível com este token (ou grave o Zone ID em $ZONE_ID_FILE)" >&2; exit 1; }
}

fqdn() { # subdomain -> fqdn
  local sub="$1"
  case "$sub" in
    *.$ZONE_NAME|$ZONE_NAME) echo "$sub" ;;
    *) echo "$sub.$ZONE_NAME" ;;
  esac
}

cmd="${1:-}"
case "$cmd" in
  list)
    zid="$(zone_id)"
    res="$(cf GET "/zones/$zid/dns_records?per_page=100")"
    die_on_error "$res"
    jq -r '.result[] | [.type, .name, .content, (if .proxied then "proxied" else "dns-only" end)] | @tsv' <<<"$res" | column -t
    ;;
  add)
    sub="${2:?uso: cf-dns.sh add <subdominio> [ip] [proxied]}"
    ip="${3:-$DEFAULT_IP}"
    proxied="${4:-true}"
    name="$(fqdn "$sub")"
    zid="$(zone_id)"
    existing="$(cf GET "/zones/$zid/dns_records?type=A&name=$name")"
    die_on_error "$existing"
    rid="$(jq -r '.result[0].id // empty' <<<"$existing")"
    body="$(jq -n --arg name "$name" --arg ip "$ip" --argjson proxied "$proxied" \
      '{type:"A", name:$name, content:$ip, ttl:1, proxied:$proxied}')"
    if [ -n "$rid" ]; then
      res="$(cf PUT "/zones/$zid/dns_records/$rid" "$body")"
      die_on_error "$res"; echo "ATUALIZADO: A $name -> $ip (proxied=$proxied)"
    else
      res="$(cf POST "/zones/$zid/dns_records" "$body")"
      die_on_error "$res"; echo "CRIADO: A $name -> $ip (proxied=$proxied)"
    fi
    ;;
  delete)
    sub="${2:?uso: cf-dns.sh delete <subdominio>}"
    name="$(fqdn "$sub")"
    zid="$(zone_id)"
    existing="$(cf GET "/zones/$zid/dns_records?name=$name")"
    die_on_error "$existing"
    ids="$(jq -r '.result[].id' <<<"$existing")"
    [ -n "$ids" ] || { echo "Nenhum registro para $name"; exit 0; }
    for rid in $ids; do
      res="$(cf DELETE "/zones/$zid/dns_records/$rid")"
      die_on_error "$res"; echo "REMOVIDO: registro $rid de $name"
    done
    ;;
  *)
    echo "uso: cf-dns.sh {list | add <sub> [ip] [proxied] | delete <sub>}" >&2
    exit 1
    ;;
esac
