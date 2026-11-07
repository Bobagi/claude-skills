# VPS (servidor bobagi.space no Mac mini)

Desde 2026-11-04 o "VPS" e a VM Ubuntu **`servidor`** rodando no **OrbStack do Mac mini**.
Os caminhos sao os mesmos da VPS Hostinger antiga (`/opt`, `/var/www`, `/etc/nginx`, `/root`).
A VPS Hostinger (46.202.144.75) foi **apagada**: nao tente conectar nela. Doc da arquitetura:
`~/server/CLAUDE.md` no Mac e `/opt/CLAUDE.md` dentro da VM.

## Como chegar la

```
esta maquina --(Tailscale + SSH, usuario do macOS)--> Mac mini --(orb, root)--> VM servidor
```

- **Rodando no proprio Mac mini:** `orb -m servidor -u root <cmd>` direto.
- **De outra maquina (Windows, notebook):** precisa estar na mesma rede Tailscale do Mac
  (`tailscale status` deve listar `mac-mini-de-gustavo`). O alias SSH `macmini` (no
  `~/.ssh/config` da maquina) usa uma chave dedicada, autorizada no `~/.ssh/authorized_keys`
  do Mac. Detalhes da maquina atual (alias, chave) ficam na memoria
  `~/.claude/projects/<projeto>/memory/vps_bobagi.md` (fora do repo).
- **No SSH nao interativo o `orb` NAO esta no PATH** do macOS: use o caminho completo
  `/opt/homebrew/bin/orb`.

## Comandos

Executar um comando na VM (de outra maquina):
```bash
ssh macmini "/opt/homebrew/bin/orb -m servidor -u root sh -c 'COMANDO'"
```
Para comando com aspas/variaveis, mande um script pelo stdin (evita aninhar aspas):
```bash
ssh macmini "/opt/homebrew/bin/orb -m servidor -u root bash -s" <<'EOF'
cd /opt/meu-projeto && docker compose ps
EOF
```
Enviar arquivo para a VM:
```bash
cat ARQUIVO | ssh macmini "/opt/homebrew/bin/orb -m servidor -u root sh -c 'cat > /DESTINO'"
```
Baixar arquivo da VM:
```bash
ssh macmini "/opt/homebrew/bin/orb -m servidor -u root cat /ORIGEM" > ARQUIVO
```

## Configurar uma maquina nova (uma vez)

1. Instalar o Tailscale e logar na mesma conta (`tailscale up`); conferir com
   `tailscale ping mac-mini-de-gustavo`.
2. `ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519_macmini -C "<maquina>->mac-mini"`.
3. Pedir ao operador para adicionar a `.pub` no `~/.ssh/authorized_keys` do Mac (usuario
   `gustavo`). Nao digite senha do macOS por ele.
4. Adicionar no `~/.ssh/config`:
   ```
   Host macmini mac-mini-de-gustavo
       HostName mac-mini-de-gustavo
       User gustavo
       IdentityFile ~/.ssh/id_ed25519_macmini
       IdentitiesOnly yes
       StrictHostKeyChecking accept-new
       ServerAliveInterval 30
   ```
5. Testar: `ssh macmini "/opt/homebrew/bin/orb -m servidor -u root uptime"` e anotar na
   memoria `vps_bobagi.md` da maquina.

## Problemas comuns

- `Permission denied (publickey,...)`: a chave desta maquina nao esta no `authorized_keys` do Mac.
- Timeout / host nao resolve: o Tailscale desta maquina esta desligado ou o Mac esta offline
  (`tailscale status`).
- `orb: command not found`: use `/opt/homebrew/bin/orb`.

## Instrucoes de execucao

1. Se estiver no Mac mini, use `orb` direto; senao, confira o alias `macmini` (memoria
   `vps_bobagi.md`) e o Tailscale.
2. Se $ARGUMENTS estiver vazio, execute o diagnostico padrao.
3. Se $ARGUMENTS tiver conteudo, execute esse comando na VM `servidor`.

## Diagnostico padrao (sem argumentos)

Execute dentro da VM e apresente um resumo organizado:
- uptime
- df -h /
- free -h
- systemctl is-active nginx
- ls /etc/nginx/sites-enabled/
