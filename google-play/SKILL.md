---
name: google-play
description: Gerencia apps na Google Play via Play Developer API com service account — subir/lançar AAB em qualquer track (internal/beta/production), promover release, rollout gradual, ver/responder avaliações, ler/editar a ficha da loja (listing) e checar status de versões. Use quando o usuário pedir para lançar/subir/publicar uma versão na Play Store, promover ou pausar um rollout, responder reviews, mexer no texto/título da loja, ou ver em que estado está uma release. App padrão - Tic Tac Verse (com.bobagi.tictacverse).
allowed-tools: Bash, Read
---

# Google Play (Play Developer API)

Automatiza o ciclo de release na Play Store via service account. Tudo roda pelo
script **`scripts/gplay.py`** (python3 + openssl + curl, sem pip).

## Credenciais

- **Arquivo:** `~/.config/bobagi-google/play-service-account.json` (chmod 600,
  NUNCA no repo, NUNCA imprimir o conteúdo).
- Se o arquivo não existir, o setup único do operador ainda não foi feito →
  mostre a ele o passo a passo de `SETUP.md` e pare.
- Comece qualquer sessão de release com `gplay.py doctor` (valida credencial,
  permissão no app e binários).

## Comandos

```bash
S=~/.claude/skills/google-play/scripts/gplay.py   # symlink do repo claude-skills

python3 $S doctor                       # valida setup de ponta a ponta
python3 $S tracks                       # o que está em cada track (status/rollout)
python3 $S bundles                      # versionCodes já enviados
python3 $S upload --aab dist/app.aab --track internal --notes "Correções de bugs"
python3 $S promote --from-track internal --to-track production --rollout 0.2
python3 $S rollout --fraction 1.0 --track production
python3 $S reviews --limit 10
python3 $S reviews-reply --review-id XYZ --text "Obrigado! Corrigido na v1.0.5."
python3 $S listing                      # ficha da loja em todos os idiomas
python3 $S listing-set --lang pt-BR --title "Tic Tac Verse: Jogo da Velha"
```

Outro app: `--package com.exemplo.app` (padrão: `com.bobagi.tictacverse`).

## Regras de segurança (obrigatórias)

1. **Track `production` só com confirmação explícita do operador NA CONVERSA**
   (pergunta direta, resposta afirmativa). Só então exporte
   `GPLAY_CONFIRM_PROD=yes` no comando — o script bloqueia sem isso.
   Tracks de teste (`internal`, `alpha`, `beta`) não precisam de confirmação.
2. Primeira ida à produção de uma versão nova: prefira **rollout gradual**
   (`--rollout 0.2`) e complete depois com `rollout --fraction 1.0`.
3. `versionCode` deve ser maior que o último publicado (`bundles` mostra).
   Quem define é o `pubspec.yaml` (`version: X.Y.Z+CODE`) no build Flutter.
4. Nunca leia/imprima o JSON da service account; nunca o copie para dentro
   de repositório. Se vazar: revogar a chave no GCP e gerar outra.
5. Depois de publicar, lembre o operador de manter o `pubspec.yaml` do
   repositório em sincronia com o versionCode publicado.
6. O que a API **não** faz (continua manual na Play Console): declarações de
   app content / data safety, criação de app novo, e envio para revisão quando
   o commit responder `changesNotSentForReview` (o script avisa quando for o caso).

## Build do Tic Tac Verse nesta VPS (contexto)

Clone em `/opt/tictacverse`, Flutter em `/opt/flutter`. A VPS tem pouca RAM:
criar swap temporário antes de `flutter build appbundle --release` e remover
depois (procedimento documentado em `/opt/CLAUDE.md`, seção Tic Tac Verse).
