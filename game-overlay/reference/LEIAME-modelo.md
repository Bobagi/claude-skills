# Monitoramento de performance · {RAIZ}

Gerado pela skill `game-overlay` em {DATA} na máquina {MAQUINA}. Versões: {VERSOES}.
Tudo instalado em `{RAIZ}`; nada em Program Files, nada no menu Iniciar.

{NOTA_NOTEBOOK}

## Como funciona

São duas peças que trabalham juntas:

- **HWiNFO** lê os sensores (CPU, GPU, RAM, disco, temperaturas, watts) e embute o
  PresentMon da Intel (FPS médio, 1% Low, CPU Busy, GPU Busy).
- **RTSS** (RivaTuner Statistics Server) desenha o overlay dentro do jogo e conta os
  quadros (FPS atual e Frametime).

O HWiNFO manda os valores pro RTSS por memória compartilhada. Os dois precisam estar
rodando, e **nesta ordem: RTSS primeiro, HWiNFO depois** (o porquê está em "A ordem
importa"). Quem garante isso é a tarefa agendada `HWiNFO64 (monitoramento)`, que roda
elevada no logon (15 s depois) e chama `_Config\iniciar-monitoramento.ps1`. O script sobe o
RTSS, espera a memória compartilhada dele existir, sobe o HWiNFO, confere que a linha
`FPS` apareceu no OSD e, se não apareceu em 60 s, reinicia o HWiNFO uma vez. Cada execução
fica em `_Config\inicio.log`.

O RTSS **não fica** no `Run` do usuário: ele exige administrador e lá pediria UAC todo
logon. Nascendo da tarefa, herda o token elevado e não pede nada.

## A ordem importa

O HWiNFO enumera os grupos de sensores **uma única vez, ao iniciar**. O grupo `[RTSS]`,
de onde vem o FPS atual e o Frametime, só existe se o RTSS já estiver no ar naquele
instante. Se o HWiNFO nascer antes, o overlay mostra tudo menos `FPS` e `Frametime`.
Correção manual: reiniciar só o HWiNFO com o RTSS já rodando, ou rodar a tarefa agendada.

## Se o overlay não aparecer

Feche o jogo, confira que o RTSS está na bandeja, e abra o jogo de novo: injetar no
nascimento do processo é o caminho mais confiável. Anti-cheat agressivo pode bloquear.
Para testar sem jogo: `CapFrameX\3d-test-app\vkcube.exe`.

## Atalho

`Ctrl + Alt + O` liga e desliga o overlay durante o jogo.

## O que está sendo exibido

Máquina: CPU {CPU} · GPU {GPU} ({VRAM_MB} MB de VRAM) · RAM {RAM_GB} GB ({RAM_MB} MB
visíveis) · discos: {DISCOS}.

```
{TABELA_LINHAS}
```

O nome da peça vai no primeiro item de cada bloco porque o OSD do HWiNFO via RTSS não
aceita linha de texto livre: toda linha precisa ser um sensor. Linha sem sensor fica em
branco e é assim que os blocos se separam. O mapeamento completo (chave de registro de
cada linha) está em `_Config\layout.json`; a lista de todos os sensores da máquina, em
`_Config\sensores.txt`.

### O gráfico de frametime

A linha `Frametime` tem um gráfico embutido. A janela é `largura × período`: 60 px a
1000 ms = 60 segundos. O eixo Y é fixo em 0 a 40 ms de propósito: a 60 FPS a linha fica em
16,7 ms e qualquer pico acima de 33 ms encosta no topo. Ajustes em
`HKCU\Software\HWiNFO64\Sensors\<grupo RTSS>\Other3` (`RtssGraphShow`, `RtssGraphWidth`,
`RtssGraphHeight`, `RtssGraphMargin`, `RtssGraphMinY`, `RtssGraphMaxY`). Não use o gráfico
nativo do RTSS: ele se esconde quando o cliente de OSD mostra FPS/frametime.

### Consumo de energia

`Watts` da CPU é a potência do pacote sobre o limite {CPU_LIMITE_W} W; `Watts` da GPU é a
potência da placa sobre o limite nominal {GPU_LIMITE_W} W. Esta máquina não tem sensor de
consumo na tomada, então `PC total` é um **sensor customizado com fórmula**, ordem de
grandeza e não medição:

```
{FORMULA_PC_TOTAL}
```

Chave: `HKCU\Software\HWiNFO64\Sensors\Custom\Energia\Power0` (`Name` e `Value` como
texto). A fórmula referencia sensor pela etiqueta exibida, entre aspas; as leituras que
alimentam a conta têm etiquetas ASCII próprias e `RtssInclude=0`. O parser avalia da
esquerda para a direita, sem precedência. O HWiNFO só enumera sensor customizado novo ao
iniciar.

### Sobre os totais e a frequência

`VRAM`, `RAM` e `Watts` mostram valor sobre total. O HWiNFO não tem campo de "máximo" no
OSD, então o total entrou como texto fixo dentro da unidade. `Freq` tem multiplicador 2:
o HWiNFO lê o clock real e DDR transfere dois dados por ciclo. `VRAM clock` fica sem
multiplicador (o comercial da GDDR é ×8 ou ×16).

## Com que frequência os números atualizam

**1000 ms nos dois lados**: `SensorInterval=1000` no `HWiNFO\HWiNFO64.INI` e
`RefreshPeriod=1000` no `RTSS\Profiles\Global`. Não baixe o `RefreshPeriod`: abaixo de
1000 ms o FPS e o Frametime zeram dentro do jogo.

## Como ler o gargalo

- **GPU Busy ≈ Frametime**: a GPU é o gargalo. Baixar resolução/qualidade aumenta o FPS.
- **CPU Busy > GPU Busy**: a CPU é o gargalo. Mexer em gráficos não adianta.
- **Nenhum dos dois perto do frametime**: limite de FPS, VSync ou espera de disco.
- `Thread max` alto com CPU total baixa: gargalo de thread única.
- `VRAM` encostando no total: engasgo (picos no gráfico), não queda de média.

## Limitações reais

- HWiNFO grátis desliga a memória compartilhada em 12 h de sessão (o overlay via RTSS não
  depende dela; o launcher religa a cada logon).
- Anti-cheat agressivo pode bloquear o overlay do RTSS.

## As outras ferramentas

- **CapFrameX** (`CapFrameX (benchmark).lnk`) grava uma sessão e analisa depois
  (distribuição de frametime, 1 % e 0,2 % low). Traz o `vkcube.exe` para testar o overlay.
- **Intel PresentMon**: opcional; o HWiNFO já embute o PresentMon (é de lá que vêm CPU Busy
  e GPU Busy).

## Mexer na configuração

Overlay: HWiNFO na bandeja, botão **Config.**, aba **OSD (RTSS)**. Ou direto no registro,
sob `HKCU\Software\HWiNFO64\Sensors\<grupo>\<Tipo><n>`, com duas regras: **o HWiNFO
reescreve essas chaves ao sair** (escreva com ele fechado) e **nunca `New-Item -Force` em
chave existente** (apaga os valores). Para refazer o layout: skill `game-overlay`,
`overlay.ps1 enumerar`, `mapear`, editar `_Config\layout.json`, `aplicar`.

Capturas de tela do teste ficam em `_Capturas\`. Backups de registro e de layout, em
`_Config\backup\`.

## Bugs e ajustes desta máquina

(preencha aqui o que só esta máquina tem: sensores que não casaram, grupos híbridos de
GPU, Embedded Controller desligado, limites de potência tirados da ficha do fabricante.)
