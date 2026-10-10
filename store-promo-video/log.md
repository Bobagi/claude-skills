# store-promo-video: registro de usos

## 2026-10-07 · Blockaboom (Phaser 3 + Capacitor, web build)
- 3 vídeos (pt-BR, en-US, es-419), 27 s, 1080x1920 60 fps, -14,5 LUFS, ~16 MB cada.
- 7 cenas: hook (sq3 limpa 3 linhas + 3 colunas = 6), chain (bandeja inteira limpando), clutch (quádrupla em
  câmera lenta 0,35x), maps (autoplayer), daily, village ("Construir tudo" real), finale (tabuleiro zerado).
- Música: Cloud-10 "The Room - 1 Min. EDM Loop" (Freesound 634684, CC0), 129,2 BPM, drop em 28,21 s.
- Fecho: Wan 2.2 I2V no ícone, seed 777, saiu limpo de primeira (blocos flutuando, estrelas piscando).
- Gravação: ~15 s por cena por idioma; render final ~5 min por idioma.
- Lições: ver "Armadilhas já pagas" no SKILL.md.

## 2026-10-07 · Tic Tac Verse (Flutter web, build da VPS)
- 6 vídeos (pt, en, es, hi, bn, ne), 27 s, 1080x1920 60 fps, dentro da moldura REAL do Pixel 5 (padrão do
  dono para este app; tela 360x780 CSS a 3x = 1080x2340 casa com a moldura).
- Cenas: gancho = jogada que fecha o Super entre amigos (linha neon no tabuleiro grande, câmera lenta);
  desafio do dia vencido DE VERDADE contra a CPU (espelho das regras + busca alfa-beta + leitura da tela);
  Cinco em linha; modos; compra do Aurora; bônus diário; clímax = modal com +60, XP, nível novo, conquista.
- Música: "Happy Summer EDM Song", Seth_Makes_Sounds (Freesound 687014, CC0), 129,2 BPM, drop em 14,99 s
  (o grave sobe 10x de uma vez; achado medindo energia < 150 Hz por meio compasso).
- Fecho: Wan 2.2 seed 777 e 778 deformaram o X; seed 4242 com prompt "stay rigid and keep their exact shape,
  only bob slightly" saiu limpo. Fallback por código no compose.py (faixa de brilho + estrelas do ícone).
- Implementação: `D:\Projetos\tictacverse\tool\promo\` (README lá).
- Rodada 2 (mesmo dia, pedido do dono): (1) efeitos SAINDO da moldura do celular: `particles.py` desenha faisca + onda
  em cada peca, explosao na captura, chuva de confete na vitoria e moedas na recompensa POR CIMA da moldura, nascendo
  no ponto real da tela (o gravador marca `kind` + x,y em cada toque e na jogada lida da CPU); zerar particulas a cada
  corte; clarao em discos concentricos fracos (disco opaco tapa o jogo). (2) Musica: dono reprovou TODA eletronica/EDM;
  aprovou "Bubblegum Pop Song" (Freesound 686610, CC0, 114,75 BPM, refrao em 83,90 s). Mandar trechos numerados para
  ele ouvir ANTES de editar. (3) Upload no YouTube Studio pelo Claude in Chrome: `file_upload` aceita ate 10 MB, entao
  sai uma copia de envio em 2 passadas a 2,65 Mbps (~9,4 MB, SSIM 0,99); o resto por JS no dialogo
  (`VIDEO_MADE_FOR_KIDS_NOT_MFK`, `#next-button` x3, `UNLISTED`) e clique em Salvar. Servidor local (aviso de rede
  local do Chrome trava o fetch) e tunel/VPS foram barrados: nao insistir.
