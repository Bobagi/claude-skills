# Product Review (dashboard de PM)

Invoque a skill **product-review** (em `~/.claude/skills/product-review/`) e siga o
`SKILL.md` dela. Ela atua como Product Manager do portfolio inteiro do VPS: coleta
dados reais de todos os produtos (trafego do nginx, usuarios nos bancos, receita do
Google Ads/AdMob, SEO do Search Console, trafego/estrelas do GitHub, consumo e saude
do box), analisa o que tem valor / consome / e usado, e gera ou atualiza um Artifact
unico com o diagnostico e recomendacoes priorizadas P0/P1/P2.

- Roda no VPS (precisa de docker, dos bancos, das skills google e do gh). De outra
  maquina, execute via a skill `vps` (SSH).
- Diretorio de trabalho e saida: `/opt/pm-dashboard/`. O Artifact e sempre republicado
  no MESMO link (`url=` na ferramenta Artifact), favicon estavel.
- Com `$ARGUMENTS`: se o operador pedir foco (ex.: "so o Tic Tac Verse", "so SEO"),
  colete tudo mesmo assim mas destaque a secao pedida no resumo.
- Ao terminar, resuma o que mudou desde a ultima rodada e as acoes P0/P1 mais urgentes.
