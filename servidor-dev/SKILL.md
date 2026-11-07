---
name: servidor-dev
description: Desenvolve, testa, compila e publica aplicativos USANDO O SERVIDOR do Gustavo (Mac mini em casa com a VM Ubuntu "servidor", acessado via Tailscale + SSH), delegando a tarefa inteira ao Claude Code que roda la e recebendo so o resumo. Use quando o usuario disser "usa o servidor", "faz no servidor", "desenvolve X no servidor", "manda o servidor fazer", ou pedir mudanca/build/publicacao em projeto que vive no servidor (blockaboom, tictacverse, tictacverse-api, cartomania, porkfolio e os outros de /opt). Nao use se voce JA esta rodando no Mac mini ou dentro da VM (ai trabalhe direto).
---

# servidor-dev: desenvolver usando o servidor

O servidor e um **Mac mini na casa do Gustavo** (nao e VPS) rodando a VM Ubuntu `servidor`
(OrbStack). Os projetos ficam em `/opt/<projeto>` na VM, com chaves de assinatura, credenciais
da Play/AdMob/Cloudflare, `gh` logado e um **Claude Code proprio** com todas as skills. Build
Android/Flutter sai pelo `appbuild` (roda no macOS do Mac mini). Por isso a regra e:

> **Nao programe daqui por SSH arquivo por arquivo. Entregue a tarefa ao Claude do servidor
> com `srv` e traga so o resumo.** Isso gasta poucos tokens nesta maquina e usa o ambiente
> que ja tem tudo.

## 1. Conferir o acesso (uma vez por sessao, 1 comando)

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 macmini "/opt/homebrew/bin/orb -m servidor -u root srv status" | head -3
```

- Funcionou: siga.
- `Could not resolve hostname macmini`: falta o alias. Veja **Maquina nova** no fim.
- `Permission denied (publickey)`: a chave desta maquina nao esta autorizada no Mac. Peca ao
  Gustavo para autorizar (mostre a `.pub`); nunca digite senha do macOS.
- Timeout: Tailscale desligado aqui ou Mac offline (`tailscale status`, procurar `mac-mini-de-gustavo`).

Abreviacao usada abaixo (escreva o comando inteiro, nao dependa de variavel entre chamadas):
`SRV` = `ssh macmini /opt/homebrew/bin/orb -m servidor -u root srv`

## 2. Entregar a tarefa

Mande o texto pelo stdin (evita problema de aspas, inclusive no Windows/Git Bash):

```bash
ssh macmini "/opt/homebrew/bin/orb -m servidor -u root srv start -d /opt/blockaboom -" <<'EOF'
<pedido do usuario, com o contexto que ele deu, nas palavras dele>
EOF
```

- Imprime um **JOB** (ex.: `20261107-135239-18222`). Guarde-o.
- `-d` = pasta do projeto (`/opt/<nome>`). Projeto novo ou incerto: `-d /opt` e diga o nome
  desejado no texto (o servidor cria o repo no GitHub Bobagi sozinho, regra dele).
- Repasse o pedido fielmente. Nao adicione plano proprio nem leia codigo antes: o Claude do
  servidor le os CLAUDE.md dos projetos e decide.
- **Producao na Play so com autorizacao explicita do usuario.** Se ele pediu "publica",
  "lanca em producao" etc., escreva isso claramente no texto. Sem isso o servidor para no
  track de teste e avisa.

## 3. Esperar e trazer o resultado

```bash
ssh macmini "/opt/homebrew/bin/orb -m servidor -u root srv wait JOB 540"
```

Rode com o timeout maximo da ferramenta Bash (600000 ms). Se responder "ainda rodando",
chame `srv wait` de novo (sem ler log no meio: cada chamada gasta tokens). Tarefas de app
costumam levar de 5 a 40 min. Quando terminar, sai so o resumo final (ate ~15 linhas) e uma
linha `[srv] sessao=... turnos=... min=...`. **Repasse o resumo ao usuario** e pronto.

## 4. Seguir a mesma conversa

Ajustes, respostas a perguntas do servidor ou "agora publica":

```bash
ssh macmini "/opt/homebrew/bin/orb -m servidor -u root srv continue JOB -" <<'EOF'
<mensagem>
EOF
```

Gera um JOB novo com o mesmo contexto. Espere com `srv wait JOB_NOVO`. Use sempre o ultimo JOB.

## Outros comandos

| Comando | Para que |
|---|---|
| `srv status` | ultimos 10 jobs e estado (running/done/failed) |
| `srv log JOB 10` | ultimos passos, compacto: so quando algo parece travado ou falhou |
| `srv stop JOB` | interromper |

Pergunta rapida que nao precisa de IA (ver status de container, uma linha de arquivo):
comando direto, ex. `ssh macmini "/opt/homebrew/bin/orb -m servidor -u root sh -c 'cd /opt/x && git log -3 --oneline'"`.
Mais receitas de acesso (enviar/baixar arquivo): `~/.claude/skills/vps/SKILL.md`.

## Economia de tokens (regras)

1. Uma tarefa = um `srv start` + `srv wait` ate acabar. Nada de `cat`/`grep` de codigo pelo SSH.
2. Nao use `srv log` "para acompanhar"; so para diagnosticar falha ou travamento.
3. Nao repita no seu texto o que o resumo ja diz; repasse e pronto.
4. Se o job falhar (`failed`), leia `srv log JOB 10`, e mande um `srv continue` com a correcao
   em vez de comecar do zero (o contexto ja esta la).

## Maquina nova (uma vez)

1. Tailscale instalado e logado na conta do Gustavo; `tailscale ping mac-mini-de-gustavo`.
2. Chave: `ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519_macmini -C "<maquina>->mac-mini"`
   e pedir ao Gustavo para colocar a `.pub` no `~/.ssh/authorized_keys` do Mac (usuario `gustavo`).
3. No `~/.ssh/config` desta maquina:
   ```
   Host macmini mac-mini-de-gustavo
       HostName mac-mini-de-gustavo
       User gustavo
       IdentityFile ~/.ssh/id_ed25519_macmini
       IdentitiesOnly yes
       StrictHostKeyChecking accept-new
       ServerAliveInterval 30
   ```
   (Se a maquina ja usa outra chave autorizada, aponte `IdentityFile` para ela.)
4. Testar com o comando do passo 1.

## Como funciona por dentro (para depurar)

`srv` (`/usr/local/bin/srv` na VM, fonte em `servidor-dev/scripts/srv` deste repo) roda
`claude -p` dentro de `tmux` (sobrevive a queda do SSH), grava `/root/srv-jobs/<JOB>/`
(`stream.jsonl`, `prompt.txt`, `exit`) e acrescenta ao pedido as regras de trabalho remoto
(resumo curto, commit+push, producao so com autorizacao). `continue` usa `claude --resume`.
O Claude do servidor esta em `defaultMode: auto`; acao barrada pelo classificador aparece no
resumo como pendencia.
