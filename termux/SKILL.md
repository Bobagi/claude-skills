---
name: termux
description: Configura o ambiente Termux no Android para usar o Claude Code. Use quando o usuário quiser instalar, configurar ou atualizar o Claude Code no celular Android via Termux.
---

# Claude Code no Termux (Android)

Sim, é possível rodar o Claude Code diretamente no Android via Termux!

## Passo 1 — Instalar o Termux

Recomenda-se instalar pelo **F-Droid** (mais atualizado) em vez da Play Store:
- F-Droid: https://f-droid.org → buscar "Termux"
- Ou baixar o APK direto em: https://github.com/termux/termux-app/releases

## Passo 2 — Atualizar pacotes e instalar dependências

```bash
pkg update && pkg upgrade -y
pkg install -y nodejs git python
```

> `python` é necessário para skills que usam scripts Python (`resume`, `admob`, `gplay`, `gads`, `gsc`).

## Passo 3 — Instalar o Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Confirme:

```bash
claude --version
```

## Passo 4 — Configurar a API Key

Obtenha sua chave em https://console.anthropic.com/ e adicione ao `.bashrc` para persistir entre sessões:

```bash
echo 'export ANTHROPIC_API_KEY="sua_chave_aqui"' >> ~/.bashrc
source ~/.bashrc
```

## Passo 5 — Sincronizar as skills pessoais

```bash
curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | SYNC_SKIP_PLUGINS=1 bash
```

> `SYNC_SKIP_PLUGINS=1` pula plugins do marketplace (dependem de GUI/Chromium, não rodam no Android ARM).
> Skills e slash-commands funcionam normalmente.

## Passo 6 — Iniciar

```bash
claude
```

---

## O que funciona no Android

| Skill / recurso | Funciona? | Observação |
|-----------------|-----------|------------|
| `vps` | Sim | Usa `sshpass` — instale com `pkg install sshpass` |
| `resume` | Sim | Requer `pip install youtube-transcript-api` |
| `gplay`, `admob`, `gads`, `gsc`, `cloudflare` | Sim | Scripts Python puros |
| `security-sweep`, `code-standards`, `test-forge` | Sim | Análise de código local |
| `app-essentials`, `code-review`, `simplify` | Sim | Sem dependências externas |
| `frontend-review` | Parcial | Screenshots (Puppeteer/Chromium) não funcionam; análise de código sim |
| Plugins (`frontend-design`, `chrome-devtools-mcp`, etc.) | Não | Dependem de Chromium headless |

---

## Dicas extras

**Acesso a arquivos do Android** (Downloads, fotos etc.):
```bash
termux-setup-storage   # pede permissão de armazenamento
# depois ~/storage/ aponta para os diretórios do Android
```

**Chave SSH para o VPS** (o Termux tem seu próprio `~/.ssh/`):
```bash
ssh-keygen -t ed25519 -C "termux"
# copie ~/.ssh/id_ed25519.pub para o VPS (~/.ssh/authorized_keys)
```

**Teclado**: Para digitar `~`, `|`, `` ` `` e outros no celular, o app **Hacker's Keyboard** (F-Droid/Play Store) ajuda bastante — tem teclas Ctrl, Alt e Esc reais.

**Sessão persistente sem manter o app aberto**:
```bash
pkg install tmux
tmux new -s claude   # inicia sessão nomeada
# para reabrir depois: tmux attach -t claude
```
