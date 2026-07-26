#!/usr/bin/env bash
# Recoleta TODAS as metricas que alimentam a Revisao de Produto (o artifact).
# Roda NO VPS (precisa de docker, dos bancos, das skills google e do gh).
# So le, nao altera nada no box.
#
# Uso:  bash collect.sh
# Saida: $PM_OUT_DIR/metrics-<data>.txt  (PM_OUT_DIR padrao = /opt/pm-dashboard)
set -uo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="${CLAUDE_SKILLS_DIR:-/opt/claude-skills}"
OUT_DIR="${PM_OUT_DIR:-/opt/pm-dashboard}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/metrics-$(date +%Y%m%d).txt"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

sec() { printf '\n\n========== %s ==========\n' "$1"; }

{
echo "Revisao de Produto: coleta de $(date -u '+%F %T UTC')"

sec "INFRA"
uptime; echo; free -h; echo; df -h /; echo
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo; echo "-- restart policies (tudo deve ser unless-stopped/always) --"
docker ps -a --format '{{.Names}}' | while read -r n; do
  docker inspect "$n" --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}'
done
echo; pm2 list 2>/dev/null
echo; docker system df

sec "CONSUMO (docker stats)"
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}'

sec "HEALTHCHECK"
/usr/local/sbin/bobagi-healthcheck.sh --quiet || echo "(falhas acima; exit=$?)"

sec "TRAFEGO NGINX: 14 dias, por host"
cd /var/log/nginx || exit 1
zcat -f access.log access.log.1 access.log.[0-9].gz access.log.1[0-9].gz 2>/dev/null \
  | grep -E '^[a-z0-9.-]+\.space ' > "$TMP/geo.log"
echo "linhas: $(wc -l < "$TMP/geo.log")"
python3 "$SELF_DIR/analyze_logs.py" "$TMP/geo.log" 2>&1 | head -40

sec "BANCOS: contagem de usuarios e uso"
echo "-- coin_hub --"
docker exec coin-hub-db-1 psql -U coin_hub -d coin_hub -t -A -F'|' -c "
SELECT 'users',count(*) FROM users
UNION ALL SELECT 'ativos_7d',count(DISTINCT user_id) FROM user_sessions WHERE created_at>now()-interval '7 days'
UNION ALL SELECT 'binance_creds',count(*) FROM binance_credentials
UNION ALL SELECT 'trading_ops',count(*) FROM trading_operations
UNION ALL SELECT 'execucoes',count(*) FROM trading_operation_executions;" 2>&1
echo "-- cartomania --"
docker exec cartomania-db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -t -A -F"|" -c "SELECT (SELECT count(*) FROM \"Player\"), (SELECT count(*) FROM \"Game\"), (SELECT max(\"createdAt\") FROM \"Player\")"' 2>&1 | tail -2
echo "   ^ jogadores | partidas | ultimo cadastro"
echo "-- todo --"
docker exec todo-db-1 sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB -t -A -F"|" -c "SELECT (SELECT count(*) FROM users),(SELECT count(*) FROM tasks),(SELECT count(*) FROM payments)"' 2>&1 | tail -2
echo "   ^ usuarios | tarefas | pagamentos"
echo "-- umami (eventos por site, 30d) --"
docker exec umami-db psql -U umami -d umami -t -A -F'|' -c "
SELECT w.name, w.domain,
 (SELECT count(*) FROM website_event e WHERE e.website_id=w.website_id AND e.created_at>now()-interval '30 days'),
 (SELECT count(DISTINCT session_id) FROM website_event e WHERE e.website_id=w.website_id AND e.created_at>now()-interval '30 days')
FROM website w ORDER BY 3 DESC;" 2>&1

sec "GOOGLE ADS (30 dias)"
python3 "$SKILLS/google-ads/scripts/gads.py" campaigns --days 30 2>&1 | tail -8
python3 "$SKILLS/google-ads/scripts/gads.py" groups    --days 30 2>&1 | tail -8
python3 "$SKILLS/google-ads/scripts/gads.py" daily     --days 21 2>&1 | tail -25
echo "-- instalacoes por pais --"
python3 "$SKILLS/google-ads/scripts/gads.py" search --gaql \
  "SELECT geographic_view.country_criterion_id, metrics.cost_micros, metrics.conversions FROM geographic_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.conversions DESC LIMIT 15" 2>&1 | tail -60

sec "ADMOB (401 = ainda suspenso)"
python3 "$SKILLS/admob/scripts/admob.py" report 2>&1 | tail -6

sec "GOOGLE PLAY"
python3 "$SKILLS/google-play/scripts/gplay.py" tracks  2>&1 | tail -12
python3 "$SKILLS/google-play/scripts/gplay.py" reviews 2>&1 | tail -20

sec "SEARCH CONSOLE"
GSC="$SKILLS/google-search-console/scripts/gsc.py"
for s in warframe.bobagi.space bobagi.space terraria.bobagi.space cartomania.bobagi.space; do
  echo "--- $s ---"; python3 "$GSC" report "$s" 2>&1 | head -14
done
echo "--- sitemaps (guarda-chuva do dominio) ---"
python3 "$GSC" sitemaps bobagi.space 2>&1 | head -25

sec "GITHUB: trafego dos repos que importam"
for r in Project-Zomboid-Ubuntu-Server Terraria-tModLoader-Ubuntu-Server warframe-farm-helper Bobagi-Website tictacverse clonador; do
  v=$(gh api "repos/Bobagi/$r/traffic/views" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(f\"views={d['count']} uniq={d['uniques']}\")" 2>/dev/null || echo "n/a")
  s=$(gh api "repos/Bobagi/$r" --jq '.stargazers_count' 2>/dev/null || echo "?")
  echo "$r :: $v estrelas=$s"
  gh api "repos/Bobagi/$r/traffic/popular/referrers" 2>/dev/null \
    | python3 -c "import json,sys;d=json.load(sys.stdin);print('   referrers:', ', '.join(f\"{x['referrer']}({x['count']})\" for x in d[:5])) if d else None" 2>/dev/null
done

sec "SEGURANCA E BACKUP"
fail2ban-client status 2>/dev/null | head -3
for j in nginx-botsearch nginx-limit-req nginx-http-auth recidive sshd; do
  printf '  %-18s ' "$j"; fail2ban-client status "$j" 2>/dev/null | grep -E 'Currently banned|Total banned' | tr -d '\n' | sed 's/\s\+/ /g'; echo
done
echo; echo "-- backups --"
ls -la /root/coinhub-db-backups/ 2>/dev/null | tail -4
echo "   ATENCAO: cartomania/todo/umami seguem sem rotina de backup? verifique /etc/cron.d/"
ls -1 /etc/cron.d/
echo; echo "-- certificados --"
certbot certificates 2>/dev/null | grep -E 'Certificate Name|Expiry' | paste - - | sed 's/\s\+/ /g'

echo; echo "FIM: $(date -u '+%F %T UTC')"
} > "$OUT" 2>&1

echo "escrito: $OUT ($(wc -l < "$OUT") linhas)"
