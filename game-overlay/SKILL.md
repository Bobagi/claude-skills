---
name: game-overlay
description: Instala e configura em QUALQUER PC Windows o overlay de monitoramento para jogos (HWiNFO le os sensores + RTSS/RivaTuner desenha no jogo, CapFrameX para teste/benchmark, Intel PresentMon opcional), replicando o layout padrao do PC de referencia (FPS, FPS medio, 1% Low, frametime com grafico, CPU Busy/GPU Busy, blocos de CPU, GPU, RAM, discos e consumo estimado) e deixando tudo subindo sozinho no logon, elevado e na ordem certa. Use quando o usuario pedir "instale o RivaTuner/RTSS e o HWiNFO", "overlay de FPS/uso de CPU e GPU nos jogos", "replicar o overlay do PC no notebook", "o overlay sumiu/parou de mostrar FPS", "monitoramento durante jogos", ou qualquer setup/diagnostico de HWiNFO + RTSS.
allowed-tools: Bash, PowerShell, Read, Write, Edit
---

# game-overlay · HWiNFO + RTSS em qualquer máquina

Um único CLI faz tudo: `scripts/overlay.ps1`. Ele baixa, instala fora do Program Files,
configura os dois programas, descobre os sensores desta máquina pela memória
compartilhada, casa o layout padrão com eles, escreve o registro do HWiNFO, registra a
tarefa agendada elevada e verifica o resultado lendo o OSD real do RTSS. As decisões de
layout e as armadilhas que custaram horas no PC de referência estão em `reference/`.

Só Windows (10/11), PowerShell 5.1 nativo. Da shell do Claude (Git Bash ou PowerShell):

```bash
S="$HOME/.claude/skills/game-overlay/scripts/overlay.ps1"      # symlink do repo claude-skills
powershell -NoProfile -ExecutionPolicy Bypass -File "$S" status
powershell -NoProfile -ExecutionPolicy Bypass -File "$S" tudo           # instalacao completa (1 UAC)
powershell -NoProfile -ExecutionPolicy Bypass -File "$S" verificar -TesteCubo
```

## O que ele entrega

| Peça | Papel | Onde fica |
|---|---|---|
| HWiNFO64 | lê sensores; embute o PresentMon (FPS médio, 1% Low, CPU Busy, GPU Busy) | `<Raiz>\HWiNFO` |
| RTSS 7.3.x | desenha o overlay no jogo; conta FPS e frametime | `<Raiz>\RTSS` |
| CapFrameX portátil | benchmark gravado + `3d-test-app\vkcube.exe` para testar sem jogo | `<Raiz>\CapFrameX` |
| Intel PresentMon | opcional (`-ComPresentMon`, 157 MB); o HWiNFO já traz o dele | `<Raiz>\PresentMon` |
| Tarefa `HWiNFO64 (monitoramento)` | sobe RTSS e depois HWiNFO no logon, elevada, sem UAC | Agendador de Tarefas |
| `_Config\` | `overlay.json`, `sensores.{json,txt}`, `layout.json`, `iniciar-monitoramento.ps1`, `runner.ps1`, `inicio.log`, `backup\` | `<Raiz>\_Config` |
| `LEIAME.md` | documentação da máquina, gerada do modelo e completada por você | `<Raiz>` |

`<Raiz>` padrão: `D:\Tools\Monitoring` se D: for disco local com espaço, senão
`C:\Tools\Monitoring`. Passe `-Raiz` para mudar (sem espaço no caminho, por causa do
instalador NSIS do RTSS).

## Fluxo padrão (máquina nova)

1. **Antes de tudo:** `status`. Diz o que já existe (instalação anterior, tarefa, processos,
   texto atual do OSD). Se já houver overlay funcionando, não reinstale: vá direto ao que o
   usuário pediu (diagnóstico, layout, etc.).
2. **`tudo`** (uma chamada, um UAC). Sequência: `baixar > instalar > configurar > tarefa >
   enumerar > mapear > aplicar > verificar (com vkcube) > leiame`, apagando os instaladores
   no fim (`-ManterInstaladores` mantém). Rode com timeout generoso (10 min) ou em
   background: downloads (~60 MB), instaladores e ~2 min de esperas de memória compartilhada.
   Se o usuário não estiver na frente do PC, avise que um UAC vai aparecer.
3. **Leia a saída do `mapear`** (também em `_Config\layout.json`): cada linha mostra
   `rotulo <- grupo / leitura original (chave de registro) [confianca]`. Trate assim:
   - `[alta]`: ok.
   - `[media, N candidatos]`: abra `_Config\sensores.txt`, confira se a leitura escolhida é a
     certa (ex.: GPU dedicada vs integrada, `GPU Memory Allocated` vs `D3D Memory Dedicated`).
   - **linha NÃO mapeada**: procure em `sensores.txt` a leitura equivalente (rótulo em inglês
     na primeira coluna), edite a entrada em `layout.json` (`grupoId`, `inst`, `tipoNome`,
     `idx`, `label`, `unidade`) ou acrescente o padrão em `scripts/layout-padrao.json` (melhor:
     a próxima máquina já aproveita), e rode `aplicar` de novo.
   - `PC total NAO criado`: monte a fórmula à mão seguindo `reference/layout.md` (seção
     "PC total") com as leituras de potência que `sensores.txt` mostrar, preencha `pcTotal`
     no `layout.json` e rode `aplicar`. Se a máquina não expõe potência de CPU/GPU, documente
     no LEIAME e siga.
4. **`verificar -TesteCubo`** tem de fechar com todas as checagens PASS: RTSS antes do HWiNFO,
   tarefa elevada e que sobe na bateria, RTSS fora do Run, 1000 ms nos dois lados, hotkey,
   linha `FPS:` no OSD, todas as linhas do layout presentes e na ordem, vkcube enganchado com
   FPS > 0. Ele grava um screenshot da janela do vkcube em `_Capturas\`. Atenção: o vkcube
   prova a injeção e a contagem, não o desenho (no PC de referência o RTSS não desenha o OSD
   nele; o `[INFO] dwOSDFrame` diz se desenhou). A prova visual final é um jogo D3D com o
   overlay ligado. Se algo falhar, conserte e rode de novo; não entregue com FAIL.
5. **`LEIAME.md`**: o `leiame` gera a base com os valores reais; complete a seção "Bugs e
   ajustes desta máquina" com o que só ela tem (nunca copie número do PC de referência).
6. **Reinício real**: peça ao usuário para reiniciar o Windows (ou fazer logoff/logon) e rode
   `status`: `inicio.log` tem de terminar em "linha FPS presente no OSD" e a ordem tem de
   ser RTSS antes do HWiNFO. Em notebook, repita na bateria.
7. **Relatório final**, curto: raiz e versões; o que ficou diferente do padrão e por quê (só
   motivo de hardware vale); resultado de cada checagem do `verificar` com o texto do OSD e o
   caminho do screenshot; pendências reais, só o tecnicamente impossível nesta máquina.

### Ações soltas (manutenção / diagnóstico)

| Ação | Quando |
|---|---|
| `status` | sempre primeiro; mostra o OSD real e se a linha `FPS:` está lá |
| `iniciar` | overlay sem FPS/Frametime ou processos parados: dispara a tarefa (sem UAC) e espera o FPS |
| `enumerar` + `mapear` + `aplicar` | mudou hardware, quer ajustar o layout, ou alguma linha sumiu |
| `aplicar -DryRun` | ver o que seria escrito no registro sem tocar em nada (não pede UAC) |
| `configurar` | perfil do RTSS ou INI do HWiNFO foram mexidos na mão |
| `tarefa` | tarefa agendada sumiu ou RTSS voltou para o Run |
| `verificar [-TesteCubo]` | fechar qualquer intervenção |
| `desinstalar [-ApagarPasta] [-ApagarRegistro]` | remover tudo (faz backup `.reg` antes) |

## Elevação (UAC)

As ações `instalar configurar tarefa enumerar aplicar tudo desinstalar` precisam de
administrador. O `overlay.ps1` se auto-eleva: abre um PowerShell elevado escondido, espera,
e devolve a saída (também gravada em `%TEMP%\game-overlay-<acao>-<data>.log`). **Um UAC
por chamada.** Para uma sessão longa de ajustes (vários `aplicar`), inicie o runner uma vez:

```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "<Raiz>\_Config\runner.ps1"'
```

Enquanto `<Raiz>\_Config\jobs\_runner-vivo.txt` existir, o `overlay.ps1` enfileira as ações
elevadas nele (sem novo UAC). Ele morre sozinho em 60 min ou com um arquivo `jobs\STOP`.
`status`, `baixar`, `mapear`, `verificar`, `iniciar` e `aplicar -DryRun` não precisam de UAC.

## Regras duras (detalhes e mais 20 em `reference/armadilhas.md`)

- **RTSS antes do HWiNFO, sempre.** O HWiNFO enumera o grupo `[RTSS]` (FPS/Frametime) só ao
  iniciar. Overlay inteiro menos FPS e Frametime = HWiNFO subiu antes. Reinicie o HWiNFO.
- **RTSS nunca no `Run`** (pede UAC todo logon e atrasa tudo). Só pela tarefa elevada.
- **Escreva INI/registro com os programas fechados** (eles regravam ao sair) e **nunca
  `New-Item -Force` em chave existente** (apaga os valores). O `aplicar` já faz isso certo.
- **1000 ms nos dois lados** (`SensorInterval` e `RefreshPeriod`); abaixo disso o RTSS zera
  FPS/Frametime no jogo.
- **ASCII em rótulo, unidade, fórmula e script `.ps1`** (PowerShell 5.1 lê sem BOM como ANSI).
- **Sempre `Start-Process`** para lançar RTSS/HWiNFO; `cmd /c start | Out-Null` trava.
- **Não instale pelo winget/Store**: cai em Program Files. O `winget download` só serve para
  baixar o instalador (e o manifesto do HWiNFO já esteve quebrado).
- O check "está tudo certo?" é ler o **OSD do RTSS** (`RTSSSharedMemoryV2`, dono `HWiNFO64`)
  e achar a linha `FPS:`; não confie na memória compartilhada do HWiNFO (a versão grátis a
  desliga em 12 h).

## Adaptações por hardware (o que muda de máquina para máquina)

- **Nome da CPU/GPU no rótulo** (`i5-14600K`, `RTX 3060 Ti`): vem do WMI, encurtado.
- **Totais nas unidades**: VRAM (registro da classe de vídeo / nvidia-smi), RAM visível ao
  Windows, PL1 da CPU e limite nominal da GPU lidos do próprio HWiNFO.
- **Discos**: uma linha por disco físico, `Disco <letra> <NVMe|SSD|HDD>`, letra tirada do nome
  do grupo `Drive: ... [C:]`.
- **Notebook**: tarefa sobe na bateria; GPU dedicada preferida ao iGPU; `PC total` usa
  constante 15 W e eficiência 0.90 (e só vale na tomada). Se o HWiNFO causar stutter, desligue
  o suporte a Embedded Controller e anote no LEIAME.
- **AMD**: temperatura `CPU (Tctl/Tdie)`, potência `CPU Package Power (SMU)`/`CPU PPT`, GPU
  `GPU Chip Power`/`GPU ASIC Power`; os padrões já estão no `layout-padrao.json`, mas confira
  no `sensores.txt` e acrescente o que faltar.

## Manter a skill viva

- Aprendeu algo novo numa máquina (rótulo de sensor diferente, instalador mudou, armadilha
  nova)? Acrescente em `reference/armadilhas.md` (com data) e, se for padrão de leitura, em
  `scripts/layout-padrao.json`. Depois `git commit` + `push` no repo `claude-skills`.
- Fontes de download (setembro de 2026): HWiNFO pela página oficial `hwinfo.com/download`
  (precisa de User-Agent de browser; links `sac.sk/.../hwi_NNNx.exe` e `hwinfo.com/files/hwi_NNN.zip`),
  RTSS pelo `winget download --id Guru3D.RTSS` (zip com `RTSSSetupNNN.exe`, hash verificado)
  ou `ftp.nluug.nl/pub/games/PC/guru3d/afterburner/`, CapFrameX e PresentMon pela API de
  releases do GitHub (`CXWorld/CapFrameX` asset `*portable.zip`, `GameTechDev/PresentMon`
  asset `.msi`). Se tudo falhar, o script diz onde salvar o arquivo à mão e segue.
- O PC de referência (i5-14600K + RTX 3060 Ti) guarda os scripts históricos de configuração
  via GUI em `D:\Tools\Monitoring\_Config\job-*.ps1`, caso o registro não cubra algo um dia.
