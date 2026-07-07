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
python3 $S details                      # contato da ficha (site do dev, e-mail)
python3 $S details-set --website https://bobagi.space
python3 $S images-list --lang pt-BR              # URLs das imagens atuais da ficha
python3 $S images-upload --lang pt-BR --files s1.png,s2.png   # screenshots da ficha (ordem)
python3 $S images-upload --lang pt-BR --image-type featureGraphic --files feature.png
```

> `contactWebsite` (em `details`) é **onde o rastreador do AdMob procura o
> app-ads.txt** — precisa apontar p/ um domínio que sirva o arquivo na raiz.

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

## Limites — o que a API NÃO cobre (explicar ao operador, não tentar contornar)

Ficam **manuais na Play Console, feitos pelo operador** (guie com passo a passo
e peça prints em `/root/prints` se precisar diagnosticar):
- Criar app novo; declarações de **App content / Data safety**; formulários de
  privacidade; classificação etária.
- ~~Imagens da ficha~~ **IMPLEMENTADO (2026-07-05):** `images-upload --lang pt-BR
  --files a.png,b.png` (phoneScreenshots, ordem preservada, substitui os antigos) e
  `--image-type featureGraphic`. Screenshots 1080x1920, feature 1024x500, PNG.
- Conta do desenvolvedor: pagamentos/payout, identidade, configurações da conta.
- **Keystore/assinatura**: a upload key fica na máquina; nunca sai dela.
- Envio p/ revisão quando o commit responder `changesNotSentForReview`
  (managed publishing) — o script avisa; o operador clica em "Send for review".

## Automação de navegador (Playwright etc.) — política

**NÃO automatizar login/navegação na conta Google a partir da VPS.** Motivos:
anti-bot/2FA do Google quebram o fluxo, viola ToS, e o risco real é **travar a
conta Google que é dona do Play Console + AdMob** (catastrófico e sem suporte).
A API oficial já cobre o ciclo recorrente (release/relatórios/listing). Para o
resto (raro e pontual): 1º guiar o operador com passo a passo; último recurso =
**chrome-devtools-mcp na máquina DO OPERADOR**, com ele logado e presente.
Nunca armazenar cookies/sessão Google na VPS.

## Build do Tic Tac Verse nesta VPS (contexto)

Clone em `/opt/tictacverse`, Flutter em `/opt/flutter`. A VPS tem pouca RAM:
criar swap temporário antes de `flutter build appbundle --release` e remover
depois (procedimento documentado em `/opt/CLAUDE.md`, seção Tic Tac Verse).
