# Aparecer para recrutador — o que move o ponteiro

Ordenado por impacto. Cada regra tem uma checagem correspondente em `li.mjs audit`.

## Como a busca funciona (o mecanismo, não o mito)

Recrutador não navega perfis: ele roda uma busca booleana no LinkedIn Recruiter e olha a
primeira página. Você aparecer depende de três coisas, nessa ordem:

1. **Casar as palavras-chave** que ele digitou. O match vem de headline, cargo, Sobre,
   descrições de experiência e **competências** — não de "esforço" nem de foto bonita.
2. **Grau de conexão.** Resultado 1º/2º grau sobe; 3º grau afunda. Rede pequena é teto
   de alcance, por mais completo que o perfil esteja.
3. **Filtros duros.** Localização, anos de experiência, idioma, e o booleano
   **"Disponível para" (Open to Work)**. Não bater um filtro = não existir na lista,
   independente de relevância.

Só depois disso é que o conteúdo do perfil converte a impressão em contato.

## O que fazer

**Headline (peso máximo).** É o campo mais pesado da busca e a única linha que aparece no
resultado, junto com o nome. 220 caracteres — use ~200. Formato que funciona:
`Cargo-alvo | Domínio | Stack separada por ·`. Comece pelo **cargo que você quer**, não
pelo que você tem hoje e não pela empresa. Inclua sinônimos que o recrutador digitaria
("Backend", "Node.js", "Kubernetes"), porque a busca casa termo, não conceito.
Evite "Estudante", "Em busca de oportunidades", emoji e frase de efeito: ocupa o espaço
mais caro do perfil sem casar nenhuma busca.

**Competências (peso alto, subestimado).** Recrutador filtra por skill como se fosse
checkbox. Limite de 100; mire 40+. Só as **3 fixadas** aparecem no perfil, então fixe as
3 que você quer ser procurado — mas as outras 97 continuam valendo na busca. Adicione as
variantes que existem como termo separado no LinkedIn (`Node.js` e `JavaScript`,
`REST APIs` e `Microservices`). `add-skill` aceita lote.

**Cargo padrão nas experiências.** Use o título que o mercado busca, não o interno da
empresa. "Analista Desenvolvedor" não é buscado; "Software Engineer" / "Desenvolvedor
Backend" é. Dá para ajustar o título sem mentir sobre a função (`set-exp-title`).

**Descrição de experiência com número.** 2.000 caracteres cada. O que separa um perfil de
um currículo genérico é métrica: latência, volume, throughput, % de redução, tamanho do
time, escala de usuários. Recrutador técnico lê a primeira linha e o primeiro número.
Descrição vazia ou de 2 linhas é a falha mais comum — `audit` marca como "magra".

**Open to Work.** É filtro booleano no Recruiter, não enfeite. A opção "somente
recrutadores" não põe a moldura pública `#OpenToWork` no avatar — dá o alcance sem o
custo de sinalizar para o empregador atual. **Não automatizado**: ligue à mão.

**Rede.** Aumentar conexões relevantes (recrutadores da sua stack, gente das empresas-alvo)
muda a posição em toda busca futura, porque converte 3º grau em 2º. É a alavanca de maior
efeito e a mais lenta. 500+ é o patamar onde o alcance para de ser o gargalo.

**Sobre.** 2.600 caracteres. Só as **~3 primeiras linhas** aparecem antes do "ver mais" —
trate como lead: quem você é, o que constrói, com o quê. O resto pode ser denso em
palavra-chave, porque ainda conta para a busca mesmo colapsado.

**Em destaque + Projetos.** É a prova de trabalho acima da dobra: CV em PDF, repositório,
app publicado. Não move a busca, mas move a conversão de quem já abriu o perfil.

**Recomendações.** O sinal de credibilidade mais caro de falsificar e o mais ignorado.
2+ recebidas já diferencia. Não dá para automatizar pedido — é mensagem humana.

**Localização e idioma.** Localização é filtro duro: use a região metropolitana que você
quer receber vaga. Se o alvo é vaga internacional, o perfil **principal** precisa dos
termos em inglês, porque é ele que o ATS e o recrutador leem — o perfil secundário em
outro idioma quase nunca é consultado.

**Certificações e idiomas.** Baratos e entram em filtro. Inglês listado é pré-requisito
de busca de vaga internacional.

## O que não move

- Foto e banner bonitos aumentam conversão de quem já viu, **não** o alcance de busca.
  (Os números de "21x mais visualizações" são marketing do próprio LinkedIn, não medida
  independente — trate como direcional.)
- Endossos de competência de desconhecidos.
- Postar todo dia sem que o conteúdo case com a stack que você quer ser procurado.
- Trocar palavra por sinônimo criativo: a busca é literal, sinônimo criativo só remove
  você do match.

## Medir

`li.mjs stats` antes e depois de qualquer mudança grande. Os três números que importam:

- **aparições em resultados de pesquisa** — sobe quando headline/competências melhoram.
- **visualizações do perfil** — sobe quando aparição + headline convertem.
- **conexões** — o teto de tudo.

O efeito não é instantâneo: a janela de comparação é de semanas, não de horas. Anote o
baseline antes de editar (`.out/stats.json` guarda o último).
