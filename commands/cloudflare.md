# Cloudflare (DNS bobagi.space)

Invoque a skill **cloudflare** (em `~/.claude/skills/cloudflare/`) e siga o
`SKILL.md` dela. Ela gerencia os registros DNS da zona `bobagi.space` no
Cloudflare via API (`scripts/cf-dns.sh`; no VPS, `/usr/local/sbin/cf-dns.sh`).

- Sem argumentos: rode `cf-dns.sh list` e apresente os registros da zona,
  destacando qualquer coisa fora do padrão (registro não-proxied de site web,
  subdomínio de 2 níveis proxied, IP diferente de 46.202.144.75).
- Com argumentos (`$ARGUMENTS`): interprete a intenção (ex.: "crie o subdomínio
  X", "deixe Y DNS-only", "remova Z") e use `add`/`delete` conforme o SKILL.md
  — respeitando as regras (vhost web ⇒ proxied; 2 níveis ⇒ DNS-only; site
  principal `bobagi.space` só com aprovação explícita).
- Fora do VPS (credenciais ausentes), execute via skill `vps` (SSH).
- Depois de mudar DNS estrutural, atualize `/opt/CLAUDE.md` e `/root/CLAUDE.md`.
