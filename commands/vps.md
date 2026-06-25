# VPS

Acessa e gerencia o VPS pessoal via SSH.

Todos os dados de conexao (host, usuario, host key e senha) ficam **fora do repositorio**,
no arquivo de memoria: `~/.claude/projects/<projeto>/memory/vps_bobagi.md`.
Leia esse arquivo para obter `HOST`, `USUARIO`, `HOSTKEY` e `SENHA` antes de conectar.

## Comando para executar no VPS

**Windows (PuTTY):**
```
"/c/Program Files/PuTTY/plink.exe" -pw "SENHA" -batch -hostkey "HOSTKEY" USUARIO@HOST "COMANDO"
```

**Linux/Mac:**
```
sshpass -p "SENHA" ssh -o StrictHostKeyChecking=no USUARIO@HOST "COMANDO"
```

**Upload de arquivo (Windows):**
```
"/c/Program Files/PuTTY/pscp.exe" -pw "SENHA" -batch -hostkey "HOSTKEY" ARQUIVO USUARIO@HOST:/DESTINO
```

## Instrucoes

1. Leia o arquivo de memoria para obter HOST, USUARIO, HOSTKEY e SENHA
2. Detecte o SO verificando se `/c/Program Files/PuTTY/plink.exe` existe
3. Use o comando correspondente ao SO atual
4. Se nenhum argumento foi passado, execute o diagnostico padrao abaixo
5. Se um argumento foi passado (`$ARGUMENTS`), execute esse comando no VPS

## Diagnostico padrao (sem argumentos)

Execute os comandos abaixo e apresente um resumo organizado:
- `uptime`
- `df -h /`
- `free -h`
- `systemctl is-active nginx`
- `ls /etc/nginx/sites-enabled/`
