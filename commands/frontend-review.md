# frontend-review

Avalia o front-end/UX de uma página ou app rodando, de forma agnóstica ao projeto.

`$ARGUMENTS` = URL alvo (ou caminho do projeto / "este projeto"). Se vazio, pergunte a URL.

Execute a skill **`frontend-review`** (`../frontend-review/SKILL.md`): três pilares —
(1) screenshots em vários viewports + crítica de padding/espaçamento/responsividade/alinhamento via
`scripts/capture.mjs`; (2) review do código do front (tokens, breakpoints, estados, i18n); (3) UX/a11y/
consistência. Aplique sempre a `rubric.md` e, ao final, rode o passo de **auto-aprimoramento** (atualiza
a rubric e dá commit/push automático no repo da skill).

Resumo das etapas:
1. Resolva alvo (URL rodando ou suba o dev server) e localize o código do front.
2. Se houver área logada, pergunte como autenticar (cookie/login de teste, signup, ou só público). Nunca ecoe/comite segredos.
3. Rode `scripts/capture.mjs` (viewports mobile/tablet/desktop/wide) e **leia os PNGs** para criticar.
4. Review de código + auditoria de a11y/consistência mapeada a `arquivo:linha`.
5. Gere o relatório em `<projeto>/.claude/frontend-review/<timestamp>/report.md`; mostre resumo + top correções no chat.
6. Atualize `rubric.md` (Learnings log) e `git add -A && git commit && git push` na pasta da skill.
