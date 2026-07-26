---
name: product-review
description: Atua como Product Manager do portfolio inteiro do VPS bobagi.space. Levanta dados reais de todos os produtos (trafego do nginx, usuarios nos bancos, receita do Google Ads/AdMob, SEO do Search Console, trafego/estrelas do GitHub, consumo e saude do box), analisa o que tem valor, o que consome, o que e usado, e gera/atualiza um Artifact unico com o diagnostico e recomendacoes priorizadas. Use quando o operador pedir "revisao de produto", "analise dos produtos", "como estao os projetos", "relatorio de PM", "atualize o dashboard de produto", ou variacoes. Roda no VPS.
allowed-tools: Bash, Read, Edit, Write, Artifact, Skill
---

# Product Review (dashboard de PM do portfolio)

Faz a revisao de produto de TUDO que roda no VPS bobagi.space e publica um Artifact
que e sempre reatualizado no MESMO link. Papel: Product Manager, nao so coletor de
metricas, o valor esta na leitura (o que tem valor, o que consome, o que e usado, o
que fazer a seguir), nao so nos numeros.

## O que esta skill produz

Um Artifact HTML (tema claro/escuro, responsivo, com graficos) organizado em:
verdict + KPIs no topo, placar dos produtos, dinheiro (Ads/AdMob/Play), descoberta
(SEO/GitHub), risco operacional, e recomendacoes priorizadas P0/P1/P2. **URL fixa:**

    https://claude.ai/code/artifact/fec2cfdb-556c-40de-9af6-11f4b7d8639f

## Onde ela roda e o que precisa

Roda **no VPS** (precisa de `docker`, dos bancos Postgres, das skills google e do
`gh`). De outra maquina, execute via a skill `vps` (SSH). Diretorio de trabalho e de
saida: **`/opt/pm-dashboard/`** (o "documento vivo": cada rodada parte do estado da
rodada anterior e atualiza os numeros por cima, nao de um template em branco).

Assets versionados nesta skill (`assets/`): `collect.sh` (coletor), `analyze_logs.py`
(analisa o access log do nginx separando humano/robo/ataque), `build.py` (embute as
4 fontes woff2 como data URI porque a CSP do Artifact bloqueia CDN), `template.html`
(o HTML, com uma rodada real preenchida como exemplo), e `fonts/` (Sora 800, JetBrains
Mono, Inter 400/600). Numa maquina nova, `/opt/pm-dashboard/` e semeado a partir daqui.

## Procedimento (siga em ordem)

1. **Garanta o diretorio de trabalho.** Se `/opt/pm-dashboard/src.html` NAO existir,
   semeie a partir da skill:
   ```bash
   SK="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"; SK="${SK:-$HOME/.claude/skills/product-review}"
   mkdir -p /opt/pm-dashboard
   cp "$SK/assets/analyze_logs.py" "$SK/assets/build.py" /opt/pm-dashboard/
   cp "$SK/assets/collect.sh" /opt/pm-dashboard/
   cp -n "$SK/assets/template.html" /opt/pm-dashboard/src.html
   cp "$SK"/assets/fonts/*.woff2 /opt/pm-dashboard/
   ```
   Se `src.html` ja existir, NAO sobrescreva: e a ultima versao publicada, e o ponto
   de partida desta rodada.

2. **Colete os dados frescos** (so leitura, ~4 min):
   ```bash
   bash /opt/pm-dashboard/collect.sh   # escreve /opt/pm-dashboard/metrics-<data>.txt
   ```
   Leia o `metrics-<data>.txt` inteiro. Se algum bloco falhar (ex.: AdMob `401` =
   conta suspensa, esperado hoje; alguma skill google sem credencial), registre a
   lacuna, nao invente numero.

3. **Colha os sinais que o `collect.sh` nao pega direto** (rode so o que precisar):
   - Contagens de produto que faltarem (ex.: usuarios por app) direto no Postgres.
   - Conversao do portfolio: no `metrics`, ou com greps no access log agregado, cheque
     downloads de `/cv/`, visitas a `/p/` (case studies), `/clonador`, referrers reais.
   - Consumo atual: `docker stats --no-stream` para RAM/rede no momento.

4. **Interprete como PM (esta e a parte que nao e mecanica).** Para cada produto
   responda: tem usuario/uso real? gera ou poderia gerar receita? esta descoberto
   (SEO/organico) ou so voce acessa? qual o risco? Cuide das **armadilhas de leitura**
   do access log (a pagina ja documenta, mantenha o aviso):
   - `analytics`: milhares de reqs com UA de navegador sao scanners de HK/SG varrendo
     `/h5`,`/wap`,`/api/stock/one`, nao gente.
   - `coin`: a maior parte e o proprio dashboard fazendo polling de `/api/v1/system/status`.
   - `warframe`: boa parte dos acessos "humanos" e o proprio IP do operador.
   HTTP 200 no vhost nao prova que a app esta boa (o front pode subir sem backend).

5. **Atualize o `src.html`.** Os dados sao arrays JS no fim do arquivo, com nomes
   claros: `RAM`, `NET`, `TRAF`, `SCORE`, `WF` (ou a serie do produto em foco),
   `SPEND`, `GEO`, `GROUPS`, `GH`. Atualize esses arrays E os KPIs do topo E o texto
   das secoes/recomendacoes (senao a pagina conta duas historias). Atualize os
   carimbos de data (eyebrow do topo e rodape). **Nao use em dash (-) nem en dash em
   nada** (regra global do operador): use hifen, virgula, dois-pontos ou parenteses.

6. **Gere o HTML final:**
   ```bash
   cd /opt/pm-dashboard && python3 build.py   # src.html + fontes -> index.html
   ```

7. **Verifique antes de publicar** (o build nao pega erro visual). Renderize em 390px
   e 1280px (claro e escuro) com o Chromium do box e cheque: `scrollWidth == clientWidth`
   (sem rolagem horizontal), 0 erro de console, as 3 fontes carregando
   (`document.fonts.check`), e olhe os graficos. Se mexeu na UI, a regra de front manda
   rodar a skill `frontend-review`. Chromium e puppeteer-core existem no box (ver o
   README de `/opt/pm-dashboard`).

8. **Publique no MESMO link** com a ferramenta Artifact, passando `url=` (senao nasce
   um link novo). Mantenha o favicon estavel:
   ```
   Artifact(file_path="/opt/pm-dashboard/index.html",
            url="https://claude.ai/code/artifact/fec2cfdb-556c-40de-9af6-11f4b7d8639f",
            favicon="grafico", label="<o que mudou nesta rodada>")
   ```
   (use o emoji de grafico de barras no favicon; mantenha-o igual entre rodadas.)

9. **Resuma para o operador** o que mudou desde a ultima rodada e as 2-3 acoes P0/P1
   mais urgentes. Se alguma recomendacao depende dele (ex.: segmentar a campanha do
   Ads na UI, escolher destino de backup), pergunte de forma acionavel.

## Escopo e limites honestos

- A skill NAO altera nada nos produtos nem publica sozinha por cron: ela le, analisa e
  publica o Artifact. Mudancas (backup, segmentar Ads, WAF) sao recomendacoes; execute
  so se o operador pedir, e ai sim com a skill certa (`google-ads` e read-only, entao
  segmentar campanha e o operador na UI).
- O que a API nao entrega fica fora e deve ser dito na pagina: retencao D1/D7 do app
  (so no Play Console), receita do AdMob enquanto a conta estiver suspensa, sessoes em
  produtos sem Umami (ex.: warframe/terraria).
- Numeros que enganam (ver passo 4) devem sempre vir com a ressalva, nunca crus.

## Automacao ja existente no VPS

Um cron de sistema (`/etc/cron.d/pm-dashboard-collect`, segundas 05:41 UTC) roda o
`collect.sh` sozinho e deixa `metrics-<data>.txt` fresco em `/opt/pm-dashboard/`, para
qualquer sessao achar dados recentes sem esperar os ~4 min. O cron **so coleta**; quem
publica o Artifact e o Claude, numa sessao (a ferramenta Artifact nao roda em cron).

## Manter a skill

Se mudar o conjunto de produtos do box, ajuste as listas em `assets/collect.sh`
(hosts, repos do GitHub, bancos) e os arrays de exemplo em `assets/template.html`.
Ao editar qualquer arquivo, mantenha-o sem em dash. Documentacao operacional detalhada
(onde fica cada numero, decisoes de paleta ja validadas, o cron) vive em
`/opt/pm-dashboard/README.md`.
