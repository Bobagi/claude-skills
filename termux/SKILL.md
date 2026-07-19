---
name: termux
description: Configura o ambiente Termux no Android para usar o Claude Code. Use quando o usuário quiser instalar, configurar ou atualizar o Claude Code no celular Android via Termux.
---

# Claude Code no Termux (Android)

> **Limitação importante:** o Claude Code não tem binário nativo para `linux-arm64-android`
> (libc Bionic do Android). `npm install -g @anthropic-ai/claude-code` instala mas falha ao rodar.
> Use uma das duas abordagens abaixo.

---

## Abordagem A — Rodar no VPS via SSH (mais simples)

Use o Termux só como terminal SSH. O Claude Code roda no VPS (Linux x64 = suportado).

```bash
# 1. Instalar sshpass para conexão com senha (ou use chave SSH)
pkg install -y openssh sshpass

# 2. Conectar ao VPS
ssh usuario@seu-vps

# 3. No VPS — instalar Node.js e Claude Code
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g @anthropic-ai/claude-code

# 4. Rodar (login com conta claude.ai — usa o plano Max, sem API key separada)
claude
```

---

## Abordagem B — proot-distro (roda no celular mesmo)

Instala um Ubuntu real dentro do Termux — aí o binário `linux-arm64-musl` funciona.

```bash
# 1. Instalar proot-distro
pkg install -y proot-distro

# 2. Instalar Ubuntu ARM
proot-distro install ubuntu

# 3. Entrar no Ubuntu
proot-distro login ubuntu

# === dentro do Ubuntu ===

# 4. Instalar Node.js (LTS)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs git

# 5. Instalar Claude Code
npm install -g @anthropic-ai/claude-code

# 6. Rodar (login com conta claude.ai)
claude
```

> Para voltar ao Ubuntu depois: `proot-distro login ubuntu` (o ambiente persiste).
> Para sessão persistente: instale `tmux` dentro do Ubuntu (`apt install tmux`).

---

## Autenticação — usar o plano Max (sem API key)

Ao rodar `claude` pela primeira vez, ele exibe uma URL. Abra no navegador do celular e
faça login com a conta claude.ai do plano Max. A autenticação fica salva localmente.

Não precisa de `ANTHROPIC_API_KEY` — essa variável é só para acesso direto à API (cobrado por token).

---

## Sincronizar as skills pessoais

Dentro do ambiente que funcionar (VPS ou proot Ubuntu):

```bash
curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | SYNC_SKIP_PLUGINS=1 bash
```

> `SYNC_SKIP_PLUGINS=1` pula plugins que dependem de Chromium headless.

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

**Teclado**: O app **Hacker's Keyboard** (F-Droid/Play Store) adiciona teclas Ctrl, Alt, Esc e `~` reais — muito útil no terminal.

**Acesso a arquivos do Android** (Downloads etc.):
```bash
termux-setup-storage   # pede permissão; depois ~/storage/ aponta pro Android
```

**Chave SSH para o VPS** (Termux tem seu próprio `~/.ssh/`):
```bash
ssh-keygen -t ed25519 -C "termux"
# copie ~/.ssh/id_ed25519.pub para ~/.ssh/authorized_keys no VPS
```
