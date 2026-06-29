#!/usr/bin/env bash
# sync.sh — padroniza a config do Claude Code a partir do repo Bobagi/claude-skills.
#
# Idempotente. Pode rodar de duas formas:
#   1) Numa maquina nova (bootstrap), sem ter o repo ainda:
#        curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | bash
#   2) Com o repo ja clonado:
#        bash <repo>/sync.sh        (ou o slash-command /sync-claude)
#
# O que faz: clona/atualiza o repo -> symlinks ~/.claude/{skills,commands} -> copia
# CLAUDE.md / settings.json / skill-first-reminder.txt (com backup) -> adiciona o
# marketplace e instala todos os plugins de config/plugins.txt.
#
# NAO toca em ~/.claude/settings.local.json (permissoes por maquina) nem em segredos.
set -euo pipefail

REPO_URL="https://github.com/Bobagi/claude-skills.git"
CLAUDE_HOME="$HOME/.claude"
BACKUP_DIR="$CLAUDE_HOME/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '    \033[1;32m✓\033[0m %s\n' "$*"; }
warn() { printf '    \033[1;33m!\033[0m %s\n' "$*"; }

# ---------------------------------------------------------------------------
# 1) Descobrir / clonar o repo
# ---------------------------------------------------------------------------
SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR=""
if [ -f "$SELF" ]; then
  # pwd -P resolves symlinks to the PHYSICAL path. Without it, running this via the
  # ~/.claude/skills symlink (the path the sync-claude skill recommends first) makes
  # REPO_DIR the symlink itself, and the link() step below then recreates ~/.claude/skills
  # pointing at itself (a self-referential loop that breaks skills + config). See link() guard.
  SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd -P)"
fi

if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/.git" ]; then
  REPO_DIR="$SCRIPT_DIR"
elif [ -d /opt/claude-skills/.git ]; then
  REPO_DIR="/opt/claude-skills"
elif [ -d "$CLAUDE_HOME/claude-skills/.git" ]; then
  REPO_DIR="$CLAUDE_HOME/claude-skills"
else
  REPO_DIR="${CLAUDE_SKILLS_DIR:-$CLAUDE_HOME/claude-skills}"
  say "Clonando $REPO_URL -> $REPO_DIR"
  git clone --depth 1 "$REPO_URL" "$REPO_DIR"
  ok "clonado"
fi

say "Repo: $REPO_DIR"
if git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$REPO_DIR" pull --ff-only 2>/dev/null && ok "atualizado (git pull)" \
    || warn "pull pulado (sem upstream/offline/commits locais) — seguindo com o conteudo atual"
fi

mkdir -p "$CLAUDE_HOME" "$BACKUP_DIR"

# ---------------------------------------------------------------------------
# 2) Symlinks de skills e commands
# ---------------------------------------------------------------------------
link() {  # <target> <linkpath>
  local target="$1" link="$2"
  # Never create a self-referential symlink (link path == target path → infinite loop that
  # breaks skills/commands/config resolution). Defends against a mis-resolved REPO_DIR
  # (e.g. invoked via the symlink path). Literal compare on purpose: when the link merely
  # already RESOLVES to target (the legit "already ok" case) the paths differ and we proceed.
  if [ "$target" = "$link" ]; then
    warn "ignorado symlink auto-referencial: $link -> $target (REPO_DIR resolveu para o proprio link?)"
    return
  fi
  if [ -L "$link" ]; then
    [ "$(readlink "$link")" = "$target" ] && { ok "symlink ja ok: $link"; return; }
    rm -f "$link"
  elif [ -e "$link" ]; then
    mv "$link" "$BACKUP_DIR/$(basename "$link").bak-$STAMP"
    warn "movido $link existente -> backup"
  fi
  ln -s "$target" "$link"
  ok "symlink: $link -> $target"
}

say "Symlinks"
link "$REPO_DIR" "$CLAUDE_HOME/skills"
link "$REPO_DIR/commands" "$CLAUDE_HOME/commands"

# ---------------------------------------------------------------------------
# 3) Arquivos de config (com backup se diferente)
# ---------------------------------------------------------------------------
copy_config() {  # <src> <dst>
  local src="$1" dst="$2"
  if [ ! -f "$src" ]; then warn "fonte ausente: $src (pulado)"; return; fi
  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then ok "$(basename "$dst") ja igual"; return; fi
  if [ -f "$dst" ]; then
    cp "$dst" "$BACKUP_DIR/$(basename "$dst").bak-$STAMP"
    warn "backup do $(basename "$dst") anterior -> $BACKUP_DIR"
  fi
  cp "$src" "$dst"
  ok "instalado: $dst"
}

say "Config (CLAUDE.md, settings.json, hook skill-first)"
copy_config "$REPO_DIR/config/CLAUDE.md"                "$CLAUDE_HOME/CLAUDE.md"
copy_config "$REPO_DIR/config/skill-first-reminder.txt" "$CLAUDE_HOME/skill-first-reminder.txt"
copy_config "$REPO_DIR/config/settings.json"            "$CLAUDE_HOME/settings.json"
warn "settings.local.json NAO e tocado (permissoes especificas da maquina)"

# ---------------------------------------------------------------------------
# 4) Marketplace + plugins
# ---------------------------------------------------------------------------
say "Plugins (marketplace claude-plugins-official)"
if [ -n "${SYNC_SKIP_PLUGINS:-}" ]; then
  warn "SYNC_SKIP_PLUGINS setado — pulando marketplace/plugins (instale com 'claude plugin install ...' depois)."
elif command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add anthropics/claude-plugins-official >/dev/null 2>&1 \
    && ok "marketplace adicionado" \
    || ok "marketplace ja presente"
  if [ -f "$REPO_DIR/config/plugins.txt" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%%#*}"; line="$(printf '%s' "$line" | tr -d '[:space:]')"
      [ -z "$line" ] && continue
      case "$line" in
        *@*)
          if claude plugin install "$line" --scope user >/dev/null 2>&1; then
            ok "plugin: $line"
          else
            warn "falhou instalar: $line (rode 'claude plugin install $line' manualmente)"
          fi ;;
      esac
    done < "$REPO_DIR/config/plugins.txt"
  fi
else
  warn "CLI 'claude' nao encontrada no PATH — pulei a instalacao de plugins."
  warn "Instale o Claude Code e rode este script de novo, ou instale os plugins de config/plugins.txt na mao."
fi

# ---------------------------------------------------------------------------
# 5) Fim
# ---------------------------------------------------------------------------
say "Pronto."
echo "    • Skills:   $(ls -1d "$REPO_DIR"/*/ 2>/dev/null | xargs -n1 basename 2>/dev/null | grep -v '^commands$\|^config$\|^scripts$' | tr '\n' ' ')"
echo "    • Plugins:  ver 'claude plugin list'"
echo "    • MCP:      Gmail/Drive vem do login claude.ai; chrome-devtools vem do plugin (ver config/mcp.md)"
echo
warn "Reinicie o Claude Code (um 'claude' novo) para carregar plugins e hooks recem-instalados."
