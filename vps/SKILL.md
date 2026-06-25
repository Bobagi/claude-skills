---
name: vps
description: Acessa e gerencia o VPS pessoal via SSH. Use quando o usuario pedir qualquer operacao no servidor (Nginx, arquivos, servicos, etc).
disable-model-invocation: true
allowed-tools: Bash, Read
---

# VPS (acesso via SSH)

## Credenciais e conexao

Todos os dados de conexao (host, usuario, host key fingerprint e senha) ficam
**fora do repositorio**, no arquivo de memoria do projeto:

`~/.claude/projects/<projeto>/memory/vps_bobagi.md`

Leia esse arquivo para obter `HOST`, `USUARIO`, `HOSTKEY` e `SENHA` antes de conectar.
A lista de sites habilitados no Nginx tambem esta nesse arquivo.

## Como executar comandos

Windows (requer PuTTY - instalar com: winget install PuTTY.PuTTY):
  "/c/Program Files/PuTTY/plink.exe" -pw "SENHA" -batch -hostkey "HOSTKEY" USUARIO@HOST "COMANDO"

Linux/Mac (requer sshpass - apt install sshpass ou brew install sshpass):
  sshpass -p "SENHA" ssh -o StrictHostKeyChecking=no USUARIO@HOST "COMANDO"

Upload de arquivo (Windows):
  "/c/Program Files/PuTTY/pscp.exe" -pw "SENHA" -batch -hostkey "HOSTKEY" ARQUIVO USUARIO@HOST:/DESTINO

## Instrucoes de execucao

1. Leia o arquivo de memoria para obter HOST, USUARIO, HOSTKEY e SENHA
2. Detecte o SO verificando se /c/Program Files/PuTTY/plink.exe existe
3. Use o comando correspondente ao SO atual
4. Se $ARGUMENTS estiver vazio, execute o diagnostico padrao
5. Se $ARGUMENTS tiver conteudo, execute esse comando no VPS

## Diagnostico padrao (sem argumentos)

Execute e apresente resumo organizado:
- uptime
- df -h /
- free -h
- systemctl is-active nginx
- ls /etc/nginx/sites-enabled/
