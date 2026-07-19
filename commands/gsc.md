# Google Search Console

Invoque a skill **google-search-console** (em `~/.claude/skills/google-search-console/`)
e siga o `SKILL.md` dela. Ela cadastra e monitora sites no Google via API, sem
o operador abrir o navegador (`scripts/gsc.py`).

- Sem argumentos: rode `gsc.py sites` e, para cada propriedade, `gsc.py sitemaps`
  + `gsc.py report` — apresente cliques/impressões/posição e as buscas que mais
  trazem gente, destacando erro de sitemap ou queda de posição.
- Com argumentos (`$ARGUMENTS`): interprete a intenção — "cadastre o site X"
  ⇒ `setup <dominio>` (verifica posse por TXT no DNS, adiciona e submete o
  sitemap); "ressubmeta o sitemap" ⇒ `sitemap-submit`; "por quais buscas
  aparece" / "como está o SEO" ⇒ `report`/`pages`.
- Ao cadastrar um domínio novo, a verificação cria um **TXT** via skill
  `cloudflare`. **Nunca remova esse TXT** (o Google revalida) e evite
  `cf-dns.sh delete <sub>`, que apaga todos os tipos do nome — use `txt-del`.
- Seja honesto no relatório: sitemap aceito **não** é indexação, e propriedade
  nova leva dias para ter dado (o Search Console atrasa ~2 dias). Não prometa
  ranking — a API não força indexação.
- Se mexer em algo estrutural, atualize `/opt/CLAUDE.md` na mesma sessão.
