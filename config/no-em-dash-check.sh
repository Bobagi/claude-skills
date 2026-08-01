#!/usr/bin/env bash
# PostToolUse (Write|Edit): barra travessão em arquivo que a IA acabou de escrever.
#
# Por que existe: a regra "nunca use travessão" no CLAUDE.md é texto, e texto é
# sugestão. Isto é execução: sai com código 2, que devolve o stderr ao modelo
# como feedback e o obriga a corrigir antes de seguir.
#
# Cobre em dash (U+2014) e en dash (U+2013). Só olha o arquivo tocado, nunca o
# repo inteiro, então arquivo legado com travessão não vira ruído.
set -uo pipefail

payload=$(cat)
file=$(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
i = d.get("tool_input") or {}
print(i.get("file_path") or i.get("notebook_path") or "")
' 2>/dev/null)

[ -n "$file" ] && [ -f "$file" ] || exit 0

# binário/imagem não interessa
case "$file" in
  *.png|*.jpg|*.jpeg|*.gif|*.webp|*.woff|*.woff2|*.ttf|*.otf|*.ico|*.pdf|*.zip|*.gz|*.aab|*.apk|*.jar|*.keystore|*.p12) exit 0 ;;
esac

hits=$(grep -nP "[\x{2013}\x{2014}]" "$file" 2>/dev/null | head -5) || true
[ -n "$hits" ] || exit 0

{
  echo "TRAVESSÃO PROIBIDO em $file (regra dura do ~/.claude/CLAUDE.md, vale para todo projeto)."
  echo "Linhas:"
  echo "$hits"
  echo
  echo "Troque por vírgula, dois-pontos, parênteses, ponto final, ou reescreva."
  echo "Se precisar mesmo de traço, use hífen simples '-'; em título, use '·'."
  echo "Confira com: grep -nP \"[\\x{2013}\\x{2014}]\" \"$file\""
} >&2
exit 2
