---
name: cloudflare
description: Gerencia o DNS da zona bobagi.space no Cloudflare via API — cria/altera/remove subdomínios (registros A/CNAME, proxied ou DNS-only). Use SEMPRE que um projeto precisar de subdomínio novo, apontar/alterar/remover DNS, "criar subdomínio", "registro DNS", "cloudflare", ou ao subir/derrubar um serviço web no VPS (a mudança de config do site deve refletir no Cloudflare). DNS é SÓ no Cloudflare — o painel da Hostinger está morto desde 2026-07-06 (nameservers movidos).
allowed-tools: Bash, Read
---

# Cloudflare — DNS da zona `bobagi.space`

Desde **2026-07-06** os nameservers de `bobagi.space` apontam pro Cloudflare
(zona inteira proxied, origem `46.202.144.75` escondida). **Todo registro DNS
vive só lá** — criar registro no painel da Hostinger não faz NADA.

## Ferramenta

Script canônico: **`scripts/cf-dns.sh`** (no VPS também acessível como
`/usr/local/sbin/cf-dns.sh`, que é symlink pra cá).

```bash
cf-dns.sh list                                # todos os registros da zona
cf-dns.sh add <sub> [ip] [proxied]            # upsert de registro A
cf-dns.sh delete <sub>                        # remove TODOS os registros do nome
```

Defaults do `add`: `ip=46.202.144.75`, `proxied=true` (nuvem laranja).
Ex.: `cf-dns.sh add warframe` → `A warframe.bobagi.space → 46.202.144.75` proxied.

## Credenciais (só existem no VPS)

`/root/.config/cloudflare/` (dir 700, arquivos 600):
- **`api-token`** — token com `Zone → DNS → Read+Edit`, escopado SÓ na zona
  `bobagi.space`. **Nunca ecoar/logar o token.**
- **`zone-id`** — Zone ID pinado (`fd58e78a…`). O token NÃO tem `Zone:Read`,
  então `GET /zones` volta vazio — o script fala com a zona direto pelo ID.
  Não remova este arquivo.

**Rodando de outra máquina** (PC do operador etc.): as credenciais não estão
lá — use a skill `vps` para executar o `cf-dns.sh` via SSH no servidor.

## Regras (não quebrar)

1. **Vhost web ⇒ proxied (nuvem laranja), sempre.** O ufw do VPS só aceita 443
   vindo dos ranges do Cloudflare + IP do operador — um registro DNS-only de
   site web fica INACESSÍVEL ao público, além de expor o IP de origem.
2. **Subdomínio de 2+ níveis (`a.b.bobagi.space`) NÃO pode ser proxied** — o
   Universal SSL grátis cobre só um nível (`*.bobagi.space`); proxied dá erro
   526. Deixe DNS-only (ex.: `studio.todo`, DNS-only desde 2026-07-16) ou evite
   o nome. DNS-only + lock do ufw ⇒ na prática só o IP do operador acessa o 443
   (aceitável p/ admin UI; errado p/ site público).
3. **Serviço novo binda `127.0.0.1`** e é servido via vhost nginx — nunca
   `0.0.0.0` (política do box; ver `/opt/CLAUDE.md`).
4. **Mudou algo estrutural?** Atualize `/opt/CLAUDE.md` (seção Cloudflare) e
   `/root/CLAUDE.md` na mesma sessão — regra da casa.
5. O site principal `bobagi.space` tem política de **não mexer sem aprovação
   por mudança** (memória `dont-touch-bobagi-space`) — DNS dele incluso.

## Fluxo completo: subir um subdomínio novo

1. `cf-dns.sh add <sub>` (proxied) e conferir com `dig A <sub>.bobagi.space +short @1.1.1.1`
   → deve responder IPs do Cloudflare (104.21.x / 172.67.x).
2. Vhost nginx em `/etc/nginx/sites-available/<sub>.bobagi.space` com
   `proxy_pass http://127.0.0.1:<porta>;` + symlink em `sites-enabled/`.
3. Certificado: `certbot --nginx -d <sub>.bobagi.space` (HTTP-01 funciona — a
   porta 80 fica aberta pro ACME).
4. `nginx -t && systemctl reload nginx` e testar
   `curl -I https://<sub>.bobagi.space` (esperar 200/301; **520 = DNS ok mas
   vhost/app faltando**).
5. Derrubar um serviço = caminho inverso (vhost fora, `cf-dns.sh delete <sub>`).

## Recriar o token (se expirar/rotacionar)

dash.cloudflare.com → My Profile → API Tokens → Create Token → template
**"Edit zone DNS"**:
- Permissions: `Zone / DNS / Edit` (+ `Zone / DNS / Read` se não vier).
- Zone Resources: **`Include`** → `Specific zone` → `bobagi.space`.
  ⚠️ Armadilha real: o dropdown em **Exclude** deixa o token cego pra própria
  conta (aconteceu em 2026-07-16).
- Conferir no summary que aparece `bobagi.space`; se não aparecer, o login está
  na conta Cloudflare errada.
- Gravar: `echo 'TOKEN' > /root/.config/cloudflare/api-token && chmod 600 ...`
  (de preferência via `!` no prompt, sem passar o token pelo chat).
- Testar: `cf-dns.sh list`.
