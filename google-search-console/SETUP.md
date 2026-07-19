# SETUP — google-search-console (passo único, já FEITO em 2026-07-19)

Guardado para reproduzir numa máquina/conta nova. Se `gsc.py doctor` responde
sem erro, não há nada a fazer aqui.

## O que precisa existir

1. **Service account** — reusa a do `google-play`
   (`claude-play-publisher@bobagi-apps-automation.iam.gserviceaccount.com`),
   com a chave em `/root/.config/bobagi-google/play-service-account.json`
   (chmod 600). Se ainda não existe, siga o `SETUP.md` da skill `google-play`.

2. **APIs ativadas** no projeto GCP `bobagi-apps-automation`
   (console.cloud.google.com → APIs e serviços → Ativar):
   - **Google Search Console API**
   - **Site Verification API**

3. **Escrita de DNS** na zona — skill `cloudflare` com
   `/root/.config/cloudflare/api-token` (Zone → DNS → Edit) e `zone-id`.
   É o que permite criar o TXT de verificação sozinho.

Confirme tudo com:

```bash
python3 /root/.claude/skills/google-search-console/scripts/gsc.py doctor
```

## Por que service account e NÃO login/senha

A service account **se auto-verifica** como proprietária via DNS TXT, então não
existe consent screen, refresh token que expira, nem senha do operador em lugar
nenhum. Se alguém sugerir "me passa sua senha do Google para eu logar", a
resposta é não: além de ser credencial pessoal (com acesso a e-mail, Play,
AdMob e faturamento), o 2FA quebraria o fluxo e a conta pode ser travada por
login automatizado. Este caminho é mais capaz *e* mais seguro.

## Domínio novo

```bash
python3 .../gsc.py setup <dominio>     # verifica, adiciona e submete o sitemap
```

Funciona para qualquer subdomínio de uma zona onde o `cf-dns.sh` escreve. Para
um domínio **fora** do Cloudflare, crie o TXT à mão no painel do registrador e
rode `verify` depois (o script avisa se o TXT não propagou).
