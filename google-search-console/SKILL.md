---
name: google-search-console
description: Gerencia o Google Search Console via API — verifica a posse de um domínio sozinho (token DNS + TXT criado no Cloudflare), adiciona a propriedade, submete sitemap e lê o desempenho de busca (cliques, impressões, CTR, posição média, top queries e páginas). Use quando o usuário pedir para cadastrar/registrar um site no Google, submeter sitemap, "fazer o Google indexar", "por quais buscas meu site aparece", "quantos cliques o site teve", ou quiser relatório de SEO/Search Console.
---

# Google Search Console

Cadastra e monitora sites no Search Console **sem o operador abrir o navegador**.
A verificação de posse é por **TXT no DNS**, e como a skill `cloudflare` tem
escrita de DNS na zona `bobagi.space`, o ciclo inteiro é automático.

## Ferramenta

```bash
GSC=/root/.claude/skills/google-search-console/scripts/gsc.py

python3 $GSC doctor                          # credenciais + APIs + o que já está verificado
python3 $GSC setup <dominio> [sitemap-url]   # verify + add + submit (o caminho normal)
python3 $GSC sites                           # propriedades da conta
python3 $GSC sitemaps <dominio>              # sitemaps + URLs aceitas / avisos / erros
python3 $GSC sitemap-submit <dom> <url>      # ressubmeter (ex.: depois de mudar URLs)
python3 $GSC report <dominio> [dias]         # cliques/impressões/CTR/posição + top 25 queries
python3 $GSC pages <dominio> [dias]          # páginas com mais cliques
```

`setup` assume `https://<dominio>/sitemap.xml` se você não passar a URL.

## Como a verificação funciona (por que não precisa do operador)

1. `siteVerification/v1/token` devolve um valor `google-site-verification=…`
2. `cf-dns.sh txt <dominio> <valor>` cria o TXT na zona (comando **TXT** foi
   adicionado ao script justamente para isto — ele não toca no registro A e
   substitui um token antigo em vez de acumular duplicatas)
3. espera a propagação conferindo em `1.1.1.1`, depois `webResource` verifica
4. `sites.PUT` adiciona como `sc-domain:` (propriedade de domínio, cobre
   http/https e todos os caminhos) e o sitemap é submetido

**Não remova o TXT** — o Google revalida periodicamente e a propriedade cai se
o registro sumir. Cuidado com `cf-dns.sh delete <sub>`: ele apaga **todos** os
tipos do nome, TXT incluso. Para mexer só no TXT use `txt-del`.

## Credenciais

Reusa a **service account do google-play**:
`/root/.config/bobagi-google/play-service-account.json` (chmod 600)
→ `claude-play-publisher@bobagi-apps-automation.iam.gserviceaccount.com`.

Escopos usados: `siteverification` + `webmasters`. Zero pip — JWT assinado com
`openssl`, HTTP com `urllib` (mesmo padrão do `gplay.py`/`admob.py`).
Sobrescrever a conta: env `GSC_SERVICE_ACCOUNT=/caminho.json`.

## Interpretar o resultado (não prometa demais)

- **Sitemap aceito ≠ indexado.** "URLs: 4406 · erros: 0" só diz que o Google
  leu a lista. Indexar leva dias/semanas e ele escolhe o que vale a pena.
- **`report` fica vazio no começo** — propriedade nova não tem histórico, e os
  dados do Search Console têm **~2 dias de atraso** (o script já compensa isso
  na janela de datas).
- **Posição média** só existe para consultas onde o site apareceu; site novo
  sem backlinks costuma aparecer primeiro em cauda longa muito específica.

## Limites (o que a API NÃO faz)

- **Não força indexação.** A Indexing API oficial só vale para `JobPosting` e
  `BroadcastEvent`; usá-la para páginas comuns é contra a política do Google.
  O caminho legítimo é sitemap + links internos + esperar.
- **Não remove URL** do índice (isso é a ferramenta de remoções, só na UI).
- **Não mexe em robots.txt.** Se um crawler estiver bloqueado, a causa está no
  servidor/CDN — ver a nota de Cloudflare em `/opt/CLAUDE.md`.
- Propriedade criada pela service account aparece na UI só se o operador for
  adicionado como usuário (`sites.permissionLevel`); a gestão via API não
  depende disso.

## Estado atual

- `sc-domain:warframe.bobagi.space` — verificada e com sitemap submetido em
  2026-07-19 (4406 URLs, 0 erros). Ver `/opt/CLAUDE.md`.
