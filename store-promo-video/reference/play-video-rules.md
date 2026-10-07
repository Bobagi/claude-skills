# Regras e técnicas do vídeo da ficha (pesquisa de 2026-10-07)

Fonte principal: ajuda oficial da Play, https://support.google.com/googleplay/android-developer/answer/9866151
Números de anúncio/conversão vêm de fornecedores (marcados). [heurística] = sem número com fonte, ponto de partida.

## 1. Regras duras da Play (o vídeo é reprovado ou some sem elas)
- **Link**: URL de VÍDEO do YouTube (não playlist, não canal, sem `?t=`). Público ou **não listado**, incorporável,
  **sem restrição de idade**, **monetização desligada**. Música com direitos pode gerar anúncio via Content ID,
  então use CC0 ou própria.
- **Duração**: só os **primeiros 30 s** tocam sozinhos e **sem som** (cabeçalho da ficha, home, busca). Alvo 25 a 30 s.
- **Orientação**: retrato e paisagem são aceitos; use a do app; **nunca barras pretas** em vídeo retrato.
- **Conteúdo**: **jogo/app real nos primeiros 10 s** e **pelo menos 80% de uso real**. Mínimo de logo/título/cutscene.
  **Sem dedos/mãos** na tela.
- **Texto proibido**: CTA de instalar ("Baixe agora", "Jogue agora", "Instale"), ranking, prêmios (exceto os da
  própria Play), depoimentos, preço/promoção, "#1", "Melhor", "Grátis", "Milhões de downloads"
  (https://www.applaunchflow.com/blog/google-play-promo-video-requirements-2026). Frase de convite ao uso dentro
  do jogo ("Limpe o tabuleiro!") não é CTA de download.
- **Localização**: um vídeo por ficha/idioma, com a interface e os textos traduzidos.
- **Efeitos**: zoom, corte, câmera lenta, legenda são edição (ok). **Efeito que o app não tem** (partícula falsa,
  tela que não existe, IA mostrando "gameplay") é conteúdo enganoso: proibido.

## 2. Estrutura que prende (28 s)
| Tempo | O quê |
|---|---|
| 0 a 2 s | **Gancho**: já no meio da ação, o momento mais satisfatório do app (no jogo: a maior explosão), com legenda curta |
| 2 a 6 s | Ritmo: sequência de recompensas (combos, contador subindo) |
| 6 a 10 s | **Tensão e alívio**: quase-derrota/espera curta, depois o grande pagamento em câmera lenta |
| 10 a 22 s | Variedade: 3 ou 4 recursos, um por corte, uma legenda cada |
| 22 a 25 s | O maior "clímax" de novo (tabuleiro zerado, nível completo) |
| 25 a 28 s | Fecho curto: ícone + nome + slogan. **Sem CTA.** |

## 3. Edição
- Cortes a cada 1 a 2 s, **no tempo forte da música** (tolerância ~100 ms); nada parado mais de 3 a 4 s.
- Zoom de impacto 5 a 8% em 3 a 5 quadros; tremor 2 a 6 quadros; flash branco 30 a 40% por 2 quadros.
- Câmera lenta 0,3 a 0,5x só no clímax (1 ou 2 vezes no vídeo).
- Cada cena entra com um leve zoom (1,05 para 1,0 em ~8 quadros), dá sensação de corte "vivo".
- Legenda: 3 a 5 palavras, uma por cena, na tela 1,5 s ou mais, letra grande com contorno, entra com "pop".
  Fora das bordas (seguro: 14% de cima, 20% de baixo, 6% dos lados), longe de onde a ação acontece.
- Retrato com o app num "cartão" de cantos arredondados (86% da tela) sobre um fundo com as cores do próprio app
  borradas: libera a faixa de cima para a legenda e evita barra preta.

## 4. Áudio
- Funciona mudo primeiro (legendas). Com som: música 120 a 140 BPM [heurística] com um **drop**; o maior momento
  do vídeo cai no drop.
- Efeitos do próprio app, sincronizados ao quadro (clique ao encaixar, tons subindo no combo, impacto grave).
- Mixagem final em **-14 LUFS** (padrão do YouTube), pico -1,5 dB; fade de saída 1 a 1,5 s.

## 5. Impacto (dados de fornecedores, não verificados no original)
StoreMaven cita +20 a 35% de conversão; SplitMetrics viu vídeo vencer capturas em 78% dos testes (mediana +22%).
Vídeo fraco pode converter **menos** que boas capturas: rode um **experimento da ficha** (com x sem vídeo).

## 6. Anúncios pagos (não é a ficha)
Pode ter CTA final, ganchos de "falha" e desafios ("só 1% consegue"), gameplay em 2 a 3 s. Nunca gameplay falsa.
Liftoff (2021): hyper-casual rende mais com ~37 s + end card. Fontes: segwise.ai, gamedeveloper.com, docs.unity.com.
