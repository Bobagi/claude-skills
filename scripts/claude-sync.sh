#!/usr/bin/env bash
# claude-sync.sh — automação do sync da config do Claude entre máquinas.
#
# Subcomandos:
#   pull   (hook SessionStart) -> git pull --ff-only no repo; aplica updates de
#          config que estavam EM SYNC (sem clobberar edição local) e avisa se
#          houver drift local não-salvo.
#   check  (hook SessionEnd)   -> só detecta drift local e avisa. NUNCA pusha.
#   save   (/sync-claude --save) -> copia a config viva (~/.claude/*) de volta
#          para config/, faz um scan de segredos e então commita + pusha.
#
# Os hooks são NÃO-BLOQUEANTES: pull/check sempre saem 0 e nunca interrompem a
# sessão. 'save' é invocado por você de propósito e pode abortar (ex.: segredo).
set -uo pipefail

CLAUDE_HOME="${HOME}/.claude"
BACKUP_DIR="$CLAUDE_HOME/backups"

# --- localizar o repo (mesma ordem do sync.sh) ------------------------------
find_repo() {
  local self_dir d
  self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
  for d in /opt/claude-skills "$CLAUDE_HOME/claude-skills" "$self_dir"; do
    if [ -n "${d:-}" ] && [ -d "$d/.git" ]; then printf '%s\n' "$d"; return 0; fi
  done
  return 1
}
REPO_DIR="$(find_repo)" || exit 0   # sem repo nesta máquina: nada a fazer

# Arquivos de config espelhados: "<rel-no-repo>:<caminho-vivo>"
CONFIG_PAIRS=(
  "config/CLAUDE.md:$CLAUDE_HOME/CLAUDE.md"
  "config/settings.json:$CLAUDE_HOME/settings.json"
  "config/skill-first-reminder.txt:$CLAUDE_HOME/skill-first-reminder.txt"
)

# --- helpers ----------------------------------------------------------------
# Compara dois arquivos. Arquivos .json são comparados por CONTEÚDO (normalizado
# com jq), não byte-a-byte: o próprio Claude Code reescreve o settings.json
# quando você muda tema/effort/modelo pela UI e reordena as chaves — isso é o
# MESMO conteúdo e não deve virar alerta de drift na abertura de toda sessão.
files_equal() {
  local a="$1" b="$2" na nb
  [ -f "$a" ] && [ -f "$b" ] || return 1
  cmp -s "$a" "$b" && return 0
  case "$a" in
    *.json)
      command -v jq >/dev/null 2>&1 || return 1
      na="$(jq -S -c . "$a" 2>/dev/null)" || return 1
      nb="$(jq -S -c . "$b" 2>/dev/null)" || return 1
      [ -n "$na" ] && [ "$na" = "$nb" ]
      ;;
    *) return 1 ;;
  esac
}

emit() {  # imprime {"systemMessage": "..."} (mostrado ao usuário na UI)
  local msg="$1"
  msg="${msg//\\/\\\\}"; msg="${msg//\"/\\\"}"; msg="${msg//$'\n'/\\n}"
  printf '{"systemMessage": "%s"}\n' "$msg"
}

drift_report() {  # ecoa os motivos de drift; vazio = sem drift
  local out="" pair repo_rel live src
  for pair in "${CONFIG_PAIRS[@]}"; do
    repo_rel="${pair%%:*}"; live="${pair#*:}"; src="$REPO_DIR/$repo_rel"
    [ -f "$src" ] || continue
    if ! files_equal "$src" "$live"; then
      out+="• $(basename "$live") difere do repo"$'\n'
    fi
  done
  if [ -n "$(git -C "$REPO_DIR" status --porcelain 2>/dev/null)" ]; then
    out+="• árvore do repo com mudanças não-commitadas"$'\n'
  fi
  if git -C "$REPO_DIR" rev-parse '@{u}' >/dev/null 2>&1 \
     && [ -n "$(git -C "$REPO_DIR" log '@{u}..HEAD' --oneline 2>/dev/null)" ]; then
    out+="• commits locais ainda não enviados (push)"$'\n'
  fi
  printf '%s' "$out"
}

# --- subcomandos ------------------------------------------------------------
cmd_pull() {
  # snapshot pré-pull: quais config files estavam EM SYNC com o repo
  declare -A insync
  local pair repo_rel live src
  for pair in "${CONFIG_PAIRS[@]}"; do
    repo_rel="${pair%%:*}"; live="${pair#*:}"; src="$REPO_DIR/$repo_rel"
    if files_equal "$src" "$live"; then
      insync["$repo_rel"]=1
    else
      insync["$repo_rel"]=0
    fi
  done

  # fast-forward pull (silencioso; offline/sem-upstream não quebra a sessão)
  git -C "$REPO_DIR" pull --ff-only >/dev/null 2>&1 || true

  # aplicar updates de config que estavam em sync — nunca clobbera edição local
  mkdir -p "$BACKUP_DIR"
  for pair in "${CONFIG_PAIRS[@]}"; do
    repo_rel="${pair%%:*}"; live="${pair#*:}"; src="$REPO_DIR/$repo_rel"
    [ -f "$src" ] || continue
    if [ "${insync[$repo_rel]:-0}" = "1" ] && ! files_equal "$src" "$live"; then
      cp "$live" "$BACKUP_DIR/$(basename "$live").bak-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
      cp "$src" "$live" 2>/dev/null || true
    fi
  done

  local report; report="$(drift_report)"
  [ -n "$report" ] && emit "Config local do Claude difere do repo claude-skills:
${report}

Rode /sync-claude --save para versionar e propagar às outras máquinas (ou /sync-claude para puxar do repo)."
  return 0
}

cmd_check() {
  local report; report="$(drift_report)"
  [ -n "$report" ] && emit "Mudanças de config locais do Claude ainda não versionadas:
${report}

Rode /sync-claude --save para enviá-las ao repo claude-skills."
  return 0
}

cmd_save() {
  local pair repo_rel live src
  # 1) copiar config viva -> config/ do repo
  for pair in "${CONFIG_PAIRS[@]}"; do
    repo_rel="${pair%%:*}"; live="${pair#*:}"; src="$REPO_DIR/$repo_rel"
    [ -f "$live" ] || continue
    files_equal "$live" "$src" || cp "$live" "$src"
  done

  git -C "$REPO_DIR" add -A
  if git -C "$REPO_DIR" diff --cached --quiet; then
    echo "✓ Nada a salvar — repo já está em dia."
    return 0
  fi

  # 2) guard de segredos (repo é PÚBLICO): aborta se achar credencial óbvia
  local secret_re='(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN[A-Z ]*PRIVATE KEY-----|AIza[0-9A-Za-z_-]{30,})'
  local hits; hits="$(git -C "$REPO_DIR" diff --cached | grep -E "$secret_re" || true)"
  if [ -n "$hits" ]; then
    git -C "$REPO_DIR" reset -q
    echo "✗ ABORTADO: o diff parece conter um segredo — nada foi commitado/pushado."
    echo "  Padrões batidos (revise e remova antes de salvar):"
    printf '%s\n' "$hits" | sed -E 's/[A-Za-z0-9_-]{8,}/[REDACTED]/g' | head -n 20
    return 1
  fi

  # 3) commit + push
  git -C "$REPO_DIR" commit -q -m "sync: salvar config local ($(hostname)) via claude-sync save" || true
  if git -C "$REPO_DIR" push -q 2>/dev/null; then
    echo "✓ Config salva e pushada para claude-skills."
  else
    echo "! Commit feito, mas o push falhou (offline/sem auth). Rode 'git -C $REPO_DIR push' depois."
  fi
  return 0
}

case "${1:-}" in
  pull)            cmd_pull ;;
  check)           cmd_check ;;
  save|--save)     cmd_save ;;
  *) echo "uso: claude-sync.sh {pull|check|save}" >&2; exit 0 ;;
esac
