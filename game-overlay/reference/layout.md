# Layout padrão do overlay e de onde vem cada número

Este é o layout que o PC de referência usa e que a skill replica em qualquer máquina,
adaptando só o que o hardware obriga (nome da CPU/GPU, totais, discos, limites de
potência). A definição executável está em `scripts/layout-padrao.json`; este arquivo
explica o porquê de cada decisão para quem for revisar o `layout.json` gerado.

## As duas peças

- **HWiNFO** lê os sensores (CPU, GPU, RAM, disco, temperaturas, watts) e embute o
  PresentMon da Intel (é de lá que vêm FPS médio, 1% Low, CPU Busy e GPU Busy).
- **RTSS** (RivaTuner Statistics Server) desenha o overlay dentro do jogo e conta os
  quadros (FPS atual e Frametime).

O HWiNFO manda os valores para o RTSS por memória compartilhada. Toda linha do overlay é
**uma leitura do HWiNFO** com `RtssInclude=1`, `RtssLine=<n>`, `RtssColumn=1` na chave
`HKCU\Software\HWiNFO64\Sensors\<IDgrupo>_<instância>\<Tipo><índice>`. O OSD não aceita
texto livre, então o nome da peça vai no rótulo do primeiro item de cada bloco, e linha
sem sensor fica em branco (é assim que os blocos se separam).

## As linhas

```
Linha  Rótulo            Leitura original do HWiNFO (grupo > item)          Observação
  1    FPS               RTSS > Framerate                                    instantâneo, do RTSS
  2    FPS medio         PresentMon > Framerate Presented (avg)
  3    1% Low            PresentMon > Framerate Presented (1% low)
  4    Frametime         RTSS > Frame Time                                   com gráfico embutido
  5    (vazia)
  6    CPU Busy          PresentMon > CPU Busy (avg)
  7    GPU Busy          PresentMon > GPU Busy (avg)
  8    (vazia)
  9    <CPU curta>       CPU > Total CPU Usage                               ex.: "i5-14600K"
 10    Thread max        CPU > Max CPU/Thread Usage
 11    Clock             CPU > Average Effective Clock
 12    Temp              CPU (DTS) > CPU Package   (AMD: CPU (Tctl/Tdie))
 13    Watts             CPU (Enhanced) > CPU Package Power                  unidade "W / <PL1> W"
 14    (vazia)
 15    <GPU curta>       GPU dedicada > GPU Core Load                        ex.: "RTX 3060 Ti"
 16    Clock             GPU > GPU Clock
 17    Watts             GPU > GPU Power                                     unidade "W / <limite nominal> W"
 18    Temp              GPU > GPU Temperature
 19    VRAM              GPU > GPU Memory Allocated (ou D3D Memory Dedicated) unidade "MB / <VRAM total> MB"
 20    VRAM clock        GPU > GPU Memory Clock                              sem multiplicador
 21    (vazia)
 22    RAM <n> GB        System > Physical Memory Used                       unidade "MB / <total visível> MB"
 23    Uso               System > Physical Memory Load
 24    Freq              Memory Timings > Memory Clock                       ValueMult = 2
 25    (vazia)
 26..  Disco <letra> <tipo>  Drive: <modelo> [<letra>:] > Total Activity     uma por disco físico, ex. "Disco C NVMe"
       (vazia)
 últ.  PC total          Custom > PC total est.                              unidade "W est." (ver abaixo)
```

Os rótulos são sempre ASCII, sem acento: etiqueta com acento quebra a fórmula do sensor
customizado quando o script é lido como ANSI.

### Como o mapeador acha cada leitura

A memória compartilhada do HWiNFO (`Global\HWiNFO_SENS_SM2`) expõe, para cada leitura, o
**rótulo original em inglês** (`szLabelOrig`, ex.: `CPU Package Power`) separado do rótulo
exibido (`szLabelUser`, que vem localizado, ex.: `Potência total da CPU`, ou renomeado). O
`layout-padrao.json` casa pelo original em inglês, então funciona com a interface em qualquer
idioma. O `idHint` é o índice da leitura visto em máquinas já configuradas e só desempata.

Os nomes dos grupos, ao contrário, vêm localizados (`Sistema: ASUS`, `Tempos da memória`),
por isso os seletores de grupo têm padrões em inglês e português e, se nenhum nome casar,
caem no ID de grupo conhecido (`F00F5000` RTSS, `F0000FF0` PresentMon, `E0002000` GPU
NVIDIA, `F0000301` System/Memory Timings, `F0000101` Drive).

Em notebook com gráficos híbridos o seletor `gpu` descarta iGPU (`UHD`, `Iris`,
`Radeon(TM) Graphics`, `Vega`) e prefere o grupo que começa com `dGPU`.

## O gráfico de frametime

Na leitura `Frametime` do grupo RTSS: `RtssGraphShow=1`, `RtssGraphWidth=60`,
`RtssGraphHeight=44`, `RtssGraphMargin=2`, `RtssGraphMinY="0.000000"`, `RtssGraphMaxY="40.000000"`.

- O gráfico embutido guarda **uma amostra por pixel de largura**, então a janela é
  `largura × SensorInterval`: 60 px a 1000 ms = 60 segundos. Um gráfico de frametime de
  verdade quer 10 s, mas a 1000 ms isso seriam 10 px. Se um dia a janela curta importar
  mais, mexa nos dois juntos (`SensorInterval=250` com `RtssGraphWidth=40` dá 10 s, ao
  custo de os números piscarem quatro vezes por segundo).
- Eixo Y fixo em 0 a 40 ms de propósito: a 60 FPS a linha fica em 16,7 ms (pouco abaixo do
  meio) e qualquer pico acima de 33 ms encosta no topo. Autoescala esconderia isso.
- **O gráfico nativo do RTSS não serve** (`EnableFrametimeHistory`): ele se esconde quando o
  cliente de OSD exibe FPS ou frametime, que é exatamente o que o HWiNFO faz. Testado.

## Totais dentro da unidade e multiplicador

O HWiNFO não tem campo de "máximo" no OSD, então o total entra como texto fixo na unidade
(valor `Unit` no registro; na interface é Customizar, coluna "Unidade"):

- VRAM: `MB / <VRAM total em MB> MB`. `Win32_VideoController.AdapterRAM` estoura em 4 GB; o
  valor certo é `HardwareInformation.qwMemorySize` no registro da classe de vídeo (ou
  `nvidia-smi --query-gpu=memory.total`).
- RAM: `MB / <TotalVisibleMemorySize em MB> MB` (o que o Windows enxerga, não o físico).
- Watts da CPU: `W / <PL1 Power Limit (Static)> W` (Intel) ou PPT Limit (AMD), lido do
  próprio HWiNFO. Se a leitura não existir, a unidade fica só `W`.
- Watts da GPU: `W / <GPU Power Limit (rated)> W`, ou `nvidia-smi power.default_limit`.

`Freq` da RAM leva `ValueMult="2.000000"`: o HWiNFO lê o clock real e DDR transfere dois
dados por ciclo, então o número comercial é o dobro (1330 × 2 = DDR4-2666). `VRAM clock`
fica **sem** multiplicador: o comercial da GDDR é ×8 ou ×16 e confundiria.

## PC total (sensor customizado com fórmula)

A maioria das máquinas não tem sensor de consumo na tomada. `PC total` é uma **estimativa**:

- Chave `HKCU\Software\HWiNFO64\Sensors\Custom\Energia\Power0` com `Name="PC total est."` e
  `Value=<fórmula>` (os dois como texto). O grupo aparece nos sensores como `Energia`, ID
  `F000CCCC_0`, e a leitura `Power0` desse grupo entra no overlay com `Label="PC total"`
  e `Unit="W est."`.
- Fórmula do PC: `"CPUCores" + "CPUSysAgent" + "CPUResto" + "GPU8pin" + "GPUPCIe" + 45 / 0.87`.
  Os cinco termos são leituras reais (`IA Cores Power`, `System Agent Power`,
  `Rest-of-Chip Power`, `GPU 8-pin #1 Input Power`, `GPU PCIe +12V Input Power`), `45` é a
  estimativa fixa do resto (placa-mãe, RAM, discos, ventoinhas) e `0.87` a eficiência da
  fonte, que converte consumo em corrente contínua em consumo na tomada. Em notebook a
  skill usa `15` e `0.90`, e a fórmula só vale na tomada (na bateria a taxa de descarga que
  o HWiNFO expõe é o consumo real).
- **Regras que mordem:** a fórmula referencia sensor **pela etiqueta exibida, entre aspas**.
  Por isso as leituras auxiliares ganham apelidos ASCII únicos (`CPUCores`, `GPU8pin`, ...)
  e ficam com `RtssInclude=0` (existem só para a conta). `Watts` seria ambíguo, já que CPU
  e GPU têm as duas esse rótulo. O parser avalia **da esquerda para a direita, sem
  precedência** (`10 + x * 2` dá `(10 + x) * 2`), por isso a divisão pela eficiência fica no
  fim. E o HWiNFO **só enumera sensor customizado novo ao iniciar**: alterar a fórmula exige
  reiniciar o HWiNFO.
- A skill só cria o `PC total` quando acha um conjunto de leituras auxiliares sem
  ambiguidade (Intel: núcleos + system agent + resto; AMD: core + SoC; GPU NVIDIA: rails
  8-pin/16-pin + PCIe). Senão deixa `pcTotal: null` com o motivo no `layout.json`, e quem
  revisa monta a fórmula à mão com as leituras que `sensores.txt` mostrar (o `aplicar` cria
  a chave `Custom` a partir do que estiver em `pcTotal`).

## Com que frequência os números atualizam

**1000 ms nos dois lados**: `SensorInterval=1000` no `HWiNFO64.INI` e `RefreshPeriod=1000`
no perfil `Global` do RTSS. É a taxa padrão de overlay de benchmark: número parado o
suficiente para ler. O RTSS conta quadros nessa janela, e é ela que alimenta `FPS` e
`Frametime`. **Não baixe o `RefreshPeriod` do RTSS**: com 100 ms o FPS e o Frametime marcam
**0 o tempo todo dentro do jogo** (a janela de contagem fica curta demais e o HWiNFO pega
janelas sem quadro fechado). O FPS mostrado é a contagem do último segundo, não uma média
longa.

## Como ler o gargalo

- **GPU Busy ≈ Frametime**: a GPU é o gargalo. Baixar resolução ou qualidade aumenta o FPS.
- **CPU Busy > GPU Busy**: a CPU é o gargalo. Olhe draw distance, densidade de NPCs, física.
- **Nenhum dos dois perto do frametime**: limite de FPS, VSync, ou espera de disco.
- `Thread max` perto de 100 % com CPU total baixa: gargalo de thread única (jogo antigo).
- `VRAM` encostando no total: engasgo (picos no gráfico de frametime), não queda de média.
- Disco mecânico ativo durante stutter: o jogo está no HD; mover para NVMe resolve.

## Configuração base fora do layout

- HWiNFO `HWiNFO64.INI` `[Settings]`: `SensorsOnly=1 Theme=1 MinimalizeMainWnd=1
  MinimalizeSensors=1 MinimalizeSensorsClose=1 ShowWelcomeAndProgress=0 SensorInterval=1000
  AutoUpdateBetaDisable=1 SensorsSM=1` (`SensorsSM` liga o Shared Memory Support; a versão
  grátis desliga depois de 12 h e o launcher reafirma a cada logon).
- HWiNFO registro `HKCU\Software\HWiNFO64\Sensors`: `RtssToggleHotKey=0x0003004F`
  (Ctrl+Alt+O liga/desliga o overlay), `OrderLocked=1`, `OsdEnabled=0` (o OSD próprio do
  HWiNFO fica desligado; só o RTSS desenha).
- RTSS `Profiles\Global`: `[OSD] EnableOSD=1 EnableBgnd=1 EnableFill=0 EnableStat=0
  BaseColor=00FF8000 BgndColor=00000000 FillColor=80000000 PositionX=1 PositionY=1
  ZoomRatio=2 CoordinateSpace=0 RefreshPeriod=1000 IntegerFramerate=1 MaximumFrametime=0
  EnableFrametimeHistory=0 ScaleToFit=0`, `[Statistics] FramerateAveragingInterval=1000`,
  `[Framerate] Limit=0 PassiveWait=1`, `[Hooking] EnableHooking=1 InjectionDelay=15000`,
  `[Font] Height=-9 Weight=400 Face=Unispace`, `Implementation=2` em todos os `[Renderer*]`.
- RTSS `Profiles\Config` `[Settings]`: `StartMinimized=1 StartWithWindows=0
  HidePreCreatedProfiles=1 EnableEncoderServer=1 Enable64Bit=1 ShowTooltips=1`.
- Tarefa agendada `HWiNFO64 (monitoramento)`: logon do usuário, atraso 15 s, `RunLevel
  Highest`, `LogonType Interactive`, sobe na bateria, sem limite de tempo,
  `MultipleInstances IgnoreNew`, reinicia 2× a cada 1 min se falhar. Ação:
  `powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File <Raiz>\_Config\iniciar-monitoramento.ps1`.
