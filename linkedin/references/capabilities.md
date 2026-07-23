# O que a skill faz, o que não faz

## Faz

| Operação | Comando | Estado |
|---|---|---|
| Checar Chrome/login | `doctor` | validado |
| Métricas (views, aparições em busca, conexões) | `stats` | validado |
| Ler uma seção | `get <seção>` | validado |
| Ler várias seções para arquivo | `read --sections a,b` | validado |
| Listar lápis de edição (alvos de `--match`) | `pencils <seção>` | validado |
| Auditar o perfil (15 checagens) | `audit` | validado |
| Headline | `set-text headline` | commit provado |
| Sobre | `set-text about` | commit provado |
| Descrição de experiência | `set-exp-desc` | commit provado |
| Cargo de experiência | `set-exp-title` | commit provado |
| Diploma / área da formação | `set-edu` | commit provado |
| Adicionar competências (em lote) | `add-skill` | commit provado |
| Adicionar idioma | `add-language` | commit provado |
| Adicionar link em Em destaque | `add-featured` | commit provado, **fetcher instável** |
| Adicionar projeto com link | `add-project` | commit provado |
| Site em Dados de contato | `set-site` | commit provado |

"commit provado" = já salvou e verificou em sessão anterior com os mesmos seletores.
Após o refactor para o CLI único, o caminho de escrita foi revalidado em modo preview
(abrir → hidratar → limpar → digitar); só o clique final em Salvar não foi reexecutado,
porque isso alteraria o perfil real sem o usuário pedir.

Seções lidas por `read`/`get`: main, experience, education, skills, projects, featured,
languages, certifications, courses, honors, volunteering, recommendations, publications, contact.

## Não faz (e por quê)

- **Open to Work** (`Disponível para`) — o menu só abre com clique por coordenada e
  mesmo assim é intermitente (~1 em 6). Envolve escolher visibilidade (badge público
  `#OpenToWork` vs só recrutadores), então errar tem custo real. **Faça à mão.**
- **Foto, banner, nome, pronomes** — não automatizado.
- **Remover** qualquer coisa (competência, experiência, projeto). Só adiciona e edita.
  Exclusão é irreversível e não vale o risco de um seletor errado.
- **Publicar posts, comentar, enviar convite/mensagem** — fora de escopo por opção:
  é exatamente o tipo de automação que o anti-bot do LinkedIn caça.
- **Reordenar competências / fixar as 3 do topo** — só na UI.
- **Perfil em segundo idioma** — o modal de experiência tem abas
  "Portuguese (Perfil principal)" / "English". A skill escreve **sempre no principal**
  (é o que ATS e recrutador leem). Decisão do usuário, mantida.
- **Ler perfis de terceiros** — só `/in/me/`. Raspar outros perfis é onde o ToS pega
  pesado de verdade.
- **Contar competências com exatidão sem scroll** — a página é virtualizada; o CLI
  resolve rolando e acumulando, mas o número é sempre "o que consegui renderizar".

## Riscos

O ToS do LinkedIn desencoraja automação. Uso leve, no próprio perfil, risco baixo mas
não-zero. Não paralelize, não faça rajadas: os comandos já esperam entre passos de
propósito. Se aparecer captcha/checkpoint, **pare** e peça para o usuário resolver na
janela do Chrome.
