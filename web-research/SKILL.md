---
name: web-research
description: Pesquisa na internet ANTES de diagnosticar ou decidir. Use SEMPRE que houver um problema, erro, crash, travamento, comportamento estranho, mensagem de log, incompatibilidade de versão ou dúvida sobre ferramenta/biblioteca/serviço de terceiros (Unity, Unity Hub, Blender, Android, Play Console, npm, Docker, drivers, Windows, APIs, etc.), e também ao escolher biblioteca, versão, preço, limite ou API que pode ter mudado. Gatilhos - "não funciona", "trava", "crasha", "erro", "fica carregando", "por que acontece", "como resolver", "qual a melhor forma", "ainda é assim?". Roda em paralelo com a leitura dos logs locais, nunca depois de esgotar hipóteses locais.
---

# web-research: pesquisar primeiro, não depois

Regra do Gustavo (2026-10-23, depois de cobrar várias vezes): **todo problema de software de
terceiros e toda decisão que depende de informação que muda com o tempo começa com pesquisa na
internet.** Ler log local e chutar hipóteses (limpar cache, reinstalar, atualizar) sem checar se é
bug conhecido com solução documentada é o erro que esta skill existe para impedir.

## Quando

- Qualquer erro, crash, travamento, "fica carregando", log estranho, regressão após atualização.
- Qualquer ferramenta de terceiros: engine, editor, IDE, SDK, driver, loja, API, serviço web.
- Decisão que depende de estado atual: versão mais nova, preço, limite de API, política de loja,
  biblioteca recomendada, mudança de comportamento entre versões.
- Só pule quando o problema é 100% do código do próprio projeto e o stack trace já aponta a linha.
  Na dúvida, pesquise.

## Fluxo

1. **Na PRIMEIRA rodada de investigação**, no mesmo bloco de chamadas em que lê os logs locais,
   carregue `WebSearch`/`WebFetch` (`ToolSearch select:WebSearch,WebFetch` se estiverem diferidas)
   e dispare **2 a 4 buscas em paralelo**:
   - o sintoma exato + nome do produto + **versão exata** (ex.: `Unity Hub 3.22 stuck "loading templates"`);
   - a mensagem de erro literal entre aspas, sem caminhos/IDs da máquina;
   - `<produto> <versão> release notes` / `known issues` / issue tracker oficial;
   - em inglês sempre; em português também se o produto tiver comunidade BR forte.
   Use `mode: "extended"` para bug recente (últimos meses), nicho ou quando a `standard` vier rasa.
2. **Abra as fontes boas com `WebFetch`**: resposta de staff/mantenedor, issue tracker, release
   notes, GitHub issues. Fórum com "funcionou pra mim" sem causa é pista, não solução.
3. **Cruze com a evidência local**: a versão bate? o sintoma no log bate? Diga qual fonte casa
   e por quê.
4. **Aplique a correção documentada** (ou a mais provável) e verifique na máquina.
5. **Se a correção não resolver, pesquise de novo** com o que aprendeu (nova mensagem de log,
   nova versão), antes de cair para outra hipótese local.
6. **Cite as fontes** na resposta ao usuário (lista "Fontes:" com links markdown).

## Antipadrões (o que irritou o dono)

- Passar 5+ chamadas lendo log/limpando cache/reinstalando sem uma única busca.
- Pesquisar só quando o usuário manda.
- Concluir "deve ser bug da versão X" sem procurar se é bug conhecido e se já tem fix.
- Ignorar que a ferramenta tem atualização pendente/lançada recentemente: confira release notes.

## Registro

Ao fechar um caso, se a pesquisa achou a causa/correção de algo que pode voltar, anote em
`log.md` desta skill (data, produto+versão, sintoma, fonte que resolveu) para a próxima vez.
