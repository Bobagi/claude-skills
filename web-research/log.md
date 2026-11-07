# web-research: casos resolvidos

Formato: data · produto + versão · sintoma · causa · o que resolveu (fonte).

## 2026-11-07 · Comfy Desktop 1.0.47 (Windows) · "Update process failed with exit code 2"
- Sintoma: botão Update do ComfyUI falha com `python.exe: can't open file '...\Programs\ComfyUI\Comfy Desktop\resources\lib\update_comfyui.py': [Errno 2]`.
- Causa: a 1.0.47 estava num caminho aninhado fora do padrão e o pacote veio sem `resources\lib`
  (o `logs\app.log` também avisava "bootstrap-python/<platform>/ is missing"). Caso parecido no
  Linux: caminho de pacote errado no AUR `comfy-desktop` (https://aur.archlinux.org/packages/comfy-desktop).
- Resolveu: rodar o instalador já baixado em `%LOCALAPPDATA%\comfyui-desktop-2-updater\pending`
  (assinatura "Drip Artificial Inc" válida, `/S` silencioso). A 1.1.9 foi para
  `%LOCALAPPDATA%\Programs\Comfy Desktop` com o `lib\update_comfyui.py`; depois, Update pelo app.

## 2026-11-07 · SillyTavern 1.19 + KoboldCpp (Qwen3.6) · prompt de imagem sai como roleplay
- Causa: o pedido de tags vai como `role: system` no fim da conversa e o template Jinja do Qwen o
  descarta. Resolveu: Prompt Post-Processing "Semi-strict" (`custom_prompt_post_processing: "semi"`),
  que converte system no meio da conversa em user (relatos no r/SillyTavernAI).
- O tool calling do Qwen3.6 não chama a ferramenta de imagem: ele narra "envia a foto". Usar gatilho
  determinístico (extensão) em vez de `function_tool`.
