# Game Overlay

Invoque a skill **game-overlay** (em `~/.claude/skills/game-overlay/`) e siga o
`SKILL.md` dela. Ela instala e configura o overlay de monitoramento para jogos
(HWiNFO + RTSS/RivaTuner, CapFrameX, PresentMon opcional) em qualquer PC Windows,
replicando o layout padrão do PC de referência, com tarefa agendada elevada que sobe
tudo no logon na ordem certa.

- Sem argumentos: rode `overlay.ps1 status` e apresente o estado (versões, processos,
  tarefa, texto atual do OSD, se a linha `FPS:` está lá). Se não houver instalação,
  proponha `tudo` e avise que vai aparecer um UAC.
- Com argumentos (`$ARGUMENTS`): interprete a intenção, por exemplo "instala tudo" →
  `tudo`; "sumiu o FPS do overlay" → `status` + `iniciar` (ou `enumerar`/`mapear`/`aplicar`
  se o layout estiver quebrado); "mostra a VRAM/troca um sensor" → editar
  `_Config\layout.json` e `aplicar`; "confere se está tudo certo" → `verificar -TesteCubo`;
  "remove" → `desinstalar`.
- Antes de qualquer mudança, leia `reference/armadilhas.md`. Feche toda intervenção com
  `verificar` sem FAIL e atualize o `LEIAME.md` da máquina.

Comando base:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME/.claude/skills/game-overlay/scripts/overlay.ps1" <acao> [-Raiz D:\Tools\Monitoring] [opcoes]
```
