#!/usr/bin/env bash
# PostToolUse (Write|Edit|NotebookEdit): when the file just written is a visible part of a game
# (scene, shader, material, model, prefab, scene builder, menu/UI code, Godot scene) or a voice-line
# source, feed the model a reminder to run game-visual-review (captures + rubric) or the game-audio
# voice pipeline before calling the work done. Fires once per session per category to stay quiet.
#
# Why: on 2026-10-23 a game menu was declared finished without anyone looking at the rendered
# screen; the owner found it "very bad". The rule in CLAUDE.md is text; this is execution.
set -uo pipefail

payload=$(cat)
read -r file session < <(printf '%s' "$payload" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("", ""); sys.exit(0)
i = d.get("tool_input") or {}
print((i.get("file_path") or i.get("notebook_path") or "").replace(" ", "%20"), d.get("session_id") or "nosession")
' 2>/dev/null)
file=${file//%20/ }
[ -n "$file" ] || exit 0

lower=$(printf '%s' "$file" | tr 'A-Z' 'a-z')
category=""
case "$lower" in
  *.unity|*.shader|*.shadergraph|*.mat|*.fbx|*.blend|*.obj|*.glb|*.gltf|*.prefab|*.tscn|*.tres|*.uasset|*.umap) category="visual" ;;
  *scenebuilder*|*menu*|*gameui*|*hud*|*/ui/*|*lighting*|*postprocess*|*skybox*|*beacon*|*camera*) category="visual" ;;
  *lines.json|*tts*|*voice*|*dialogue*|*radio.cs) category="voice" ;;
esac
# only inside something that looks like a game project
case "$lower" in
  */assets/*|*unity*|*godot*|*unreal*|*/game/*|*game*) ;;
  *) [ "$category" = "voice" ] || exit 0 ;;
esac
[ -n "$category" ] || exit 0

marker="${TMPDIR:-/tmp}/game-review-reminder-${session}-${category}"
[ -f "$marker" ] && exit 0
: > "$marker" 2>/dev/null || true

if [ "$category" = "visual" ]; then
  msg="REVISAO VISUAL DE JOGO OBRIGATORIA: voce acabou de gravar um arquivo visivel de jogo ($file). Antes de dizer que ficou pronto, rode a skill game-visual-review: capture a tela REAL de cada estado (Unity: ScreenCapture via MCP, web: Chrome), monte a folha de contato com scripts/contact_sheet.py (com --ref se houver referencia do usuario), pontue a rubric.md e corrija tudo que ficar em 2 ou menos. Nota primeiro, 'ficou pronto' depois."
else
  msg="VOZ DE JOGO: voce acabou de mexer em falas ($file). Vozes de personagem NAO saem do SAPI/Microsoft David: use o pipeline neural da skill game-audio (scripts/tts_voice.py, Chatterbox ou equivalente, com direcao de emocao por fala), aplique o filtro de radio depois e confira com analyze.py."
fi
python3 - "$msg" <<'PY'
import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": sys.argv[1]}}))
PY
exit 0
