# Armadilhas conhecidas (cada uma custou horas no PC de referência)

Leia antes de mexer em qualquer coisa. Acrescente aqui o que aprender numa máquina nova,
com data, em vez de guardar só na cabeça.

## Ordem e inicialização

1. **RTSS antes do HWiNFO, sempre.** O HWiNFO enumera os grupos de sensores uma única vez,
   ao iniciar. O grupo `[RTSS]` (FPS atual e Frametime) só existe se o RTSS já estiver no ar
   naquele instante. Se o HWiNFO nascer antes, o overlay mostra tudo **menos** `FPS` e
   `Frametime` (o resto funciona porque escrever no RTSS não depende do grupo). Correção:
   reiniciar só o HWiNFO com o RTSS rodando. É o motivo de `iniciar-monitoramento.ps1` existir.
2. **RTSS no `Run` do usuário pede UAC todo logon** e só sobe quando alguém clica. No PC isso
   o atrasou quase 6 minutos num dia e derrubou as linhas de FPS. Só pela tarefa agendada
   elevada (ele herda o token e não pede nada). O instalador do RTSS liga `StartWithWindows`;
   a skill desliga e remove a entrada do Run (backup em `_Config\run-rtss-removido.txt`).
3. **`cmd /c start "" app | Out-Null` trava o script.** O `cmd` sai, mas o PowerShell fica
   preso no pipeline até todo mundo que herdou o handle de saída fechar, e quem herdou foi o
   RTSS. Apareceu no log como 29 minutos entre "RTSS lancado" e o passo seguinte. Sempre
   `Start-Process`.
4. **Tarefa agendada em notebook precisa de `AllowStartIfOnBatteries` e
   `DontStopIfGoingOnBatteries`**, senão não sobe na bateria.
5. Depois de `Start-ScheduledTask` a memória compartilhada do RTSS pode levar até 25 s para
   aparecer no primeiro logon (visto no PC); os scripts esperam 90 s.

## Escrever configuração

6. **HWiNFO e RTSS reescrevem os próprios arquivos e o registro ao sair.** Escreva com os dois
   fechados, ou perde. "Fechar" a janela de sensores do HWiNFO só minimiza
   (`MinimalizeSensorsClose=1`): mate o processo depois de ter salvo o que queria.
7. **Nunca `New-Item -Force` em chave de registro que já existe**: recria a chave e apaga os
   valores. Foi assim que o `ValueMult` da RAM sumiu no meio da configuração do PC. Para
   alterar, `Set-ItemProperty` / `New-ItemProperty -Force` (o `-Force` no valor é seguro).
8. **Etiqueta com acento quebra a fórmula** do sensor customizado quando o `.ps1` é lido como
   ANSI (PowerShell 5.1 sem BOM). ASCII em rótulo, unidade, fórmula e comentário de script.
9. **O HWiNFO só enumera sensor customizado novo e o grupo `[RTSS]` ao iniciar.** Alterou a
   fórmula ou criou `Custom\...`: reinicie o HWiNFO.
10. A fórmula do sensor customizado referencia **pela etiqueta exibida** (a renomeada, não a
    original) e avalia **da esquerda para a direita, sem precedência**.
11. O instalador NSIS do RTSS: `/S /D=<pasta>` com o `/D` **por último e sem aspas**. O do
    HWiNFO é Inno Setup: `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR="<pasta>"`.
    Os dois abrem o programa no fim; mate `RTSS`, `RTSSHooksLoader64`, `EncoderServer64`,
    `HWiNFO64` antes de escrever configuração.
12. Não instale o HWiNFO por winget/Store para o layout: cai em Program Files. (O `winget
    download` serve para **baixar** o instalador; o manifesto dele já apontou para arquivo
    inexistente, 404 em 2026-09, por isso a skill lê a página oficial primeiro.) A página
    `hwinfo.com/download` responde 403 para `curl` sem User-Agent de browser.

## Taxa de atualização e gráfico

13. **`RefreshPeriod` do RTSS abaixo de 1000 zera FPS e Frametime dentro do jogo** (testado
    com 100 ms + `MaximumFrametime=1`). HWiNFO `SensorInterval` e RTSS `RefreshPeriod` andam
    juntos em 1000 ms.
14. O gráfico embutido do HWiNFO guarda uma amostra por pixel de largura: janela =
    `RtssGraphWidth × SensorInterval`. O gráfico nativo do RTSS (`EnableFrametimeHistory`) se
    esconde quando o cliente de OSD mostra FPS/frametime; não adianta ligar.
15. `Disco SMART a cada` e `Emb. Controller a cada` são divisores próprios do período global e
    ficam no padrão (0); baixar o período global não multiplica acesso a disco.

## Memória compartilhada e diagnóstico

16. **A versão grátis do HWiNFO desliga o Shared Memory Support depois de 12 h** de sessão e
    regrava o INI sem a chave. O overlay via RTSS **não depende** disso; só o CapFrameX e o
    diagnóstico de fallback. O launcher reafirma `SensorsSM=1` no INI a cada logon (com o
    HWiNFO fechado), então cada sessão começa com 12 h de memória compartilhada.
17. O check certo de "o grupo [RTSS] existe" é ler o **slot de OSD do RTSS cujo dono é o
    HWiNFO64** (`RTSSSharedMemoryV2`) e procurar a linha `FPS:`. Checar pela memória do
    HWiNFO (`Global\HWiNFO_SENS_SM2`) falha quando o Shared Memory está desligado: no PC isso
    fez o script reiniciar o HWiNFO à toa todo logon, com o overlay inteiro.
18. Na memória compartilhada do HWiNFO, `szLabelOrig` (offset 12 da leitura) é o rótulo em
    **inglês** e `szLabelUser` (140) é o exibido (localizado ou renomeado). Os nomes de grupo
    vêm localizados nos dois campos. O valor fica em 284 (double). O mapeador casa pelo inglês.
19. `Win32_VideoController.AdapterRAM` é uint32 e estoura em 4 GB (uma 3060 Ti "tem" 4293918720).
    Use `HardwareInformation.qwMemorySize` no registro da classe de vídeo ou `nvidia-smi`.
20. A memória compartilhada do RTSS pode ser lida de um processo **sem** elevação (basta
    `OpenExisting("RTSSSharedMemoryV2", Read)`); a do HWiNFO também. Só **matar** o HWiNFO/RTSS
    (que rodam elevados) e registrar a tarefa exigem administrador.

## Overlay no jogo

21. O RTSS injeta o overlay nos processos 3D; no PC pegou até jogo já aberto. Se não aparecer:
    feche o jogo, confira o RTSS na bandeja, abra o jogo de novo (injetar no nascimento do
    processo é o caminho confiável). Anti-cheat agressivo pode bloquear.
22. `InjectionDelay=15000` no perfil Global: o RTSS espera 15 s após o processo nascer. O teste
    com o vkcube espera ~28 s antes de ler o FPS.
23. `Ctrl+Alt+O` liga e desliga o overlay (`RtssToggleHotKey=0x0003004F`).
24. Em alguns notebooks a leitura do Embedded Controller pelo HWiNFO causa stutter. Se aparecer
    engasgo só com o HWiNFO aberto, desligue "Suporte EC" em Config. > Segurança e anote no LEIAME.

## Dirigir a interface do HWiNFO por mensagens Win32

25. Funciona (`PostMessage`/`SendMessage` em `#32770`, `SysTabControl32`, `Button`,
    `SysListView32` com `LVM_GETITEMTEXT` via `WriteProcessMemory`) e foi assim que boa parte do
    PC foi configurada, mas escrever no registro/INI com o programa fechado é mais rápido e
    previsível. Os scripts antigos estão em `D:\Tools\Monitoring\_Config\job-*.ps1` no PC de
    referência, se um dia precisar (IDs úteis: botão Config. = 1436; aba OSD (RTSS) = 5;
    Fileira = 1455, Coluna = 1456; "Mostrar valor" = 2156; "Mostrar gráfico" = 2158;
    Etiqueta/Atual = 1440 + Renomear 1441; Unidade = 1442/1443; Multiplicar = 1444 + Definir 1446;
    hotkey = 2192/2191; Configurações principais = 2182, checkbox Shared Memory = 1162).

## Scripts e elevação

26. **`Start-Process -Wait` espera também os DESCENDENTES.** O PowerShell elevado que a skill
    abre lança o HWiNFO e o RTSS; com `-Wait` o chamador nunca voltava (o HWiNFO fica aberto
    para sempre). Use `-PassThru` e `$p.WaitForExit()`, que espera só aquele processo.
27. Funções PowerShell **desenrolam** coleções ao retornar: lista vazia vira `$null`, lista de
    1 item vira o item. Quem chama usa `@(...)`, e quem retorna não usa `return ,$lista` se o
    chamador já embrulha com `@()` (senão vira array de array). Mordeu no `Read-Ini` (arquivo
    novo com 0 ou 1 seção) e no `Resolve-Apelidos` (fórmula do PC total com termos colados).
28. Rótulos originais reais (memória compartilhada, HWiNFO 8.52): RTSS = `Framerate`,
    `Framerate 1% Low`, `Framerate 0.1% Low`, **`Frame Time`** (com espaço); PresentMon =
    `Framerate Presented (avg)`, `Framerate Presented (1% low)` (minúsculo), `Framerate
    Displayed (...)`, `CPU Busy (avg)`, `GPU Busy (avg)`, `GPU Wait (avg)`. Regex sem
    `(?i)` e sem `?` no espaço não casa.
29. **O vkcube prova a injeção, não o desenho.** No PC de referência o RTSS engancha o vkcube
    (entra na lista de apps do `RTSSSharedMemoryV2`, conta ~144 FPS, o HWiNFO mostra `FPS:` > 0)
    mas `dwOSDFrame` (offset 332 da entrada do app) fica em 0: o OSD não é desenhado dentro dele,
    e a captura da janela sai sem overlay. Alternar o Ctrl+Alt+O não mudou isso. A prova visual
    do overlay é num jogo de verdade (D3D). O `verificar` reporta como [INFO], não como FAIL.
30. **AMSI do Defender bloqueia o `.ps1` inteiro** ("conteúdo mal-intencionado") quando o mesmo
    arquivo junta "ativar/localizar janela" (`AppActivate`, UI Automation, `SetForegroundWindow`)
    com captura de tela (`CopyFromScreen`). Só a captura passa. Por isso a captura vive em
    `captura.ps1`, separado, recebendo o retângulo por parâmetro, e não há P/Invoke em lugar
    nenhum da skill. Para bissectar: gere variantes do script e rode cada uma com `ajuda`.
31. `AppActivate` de um processo em segundo plano não traz a janela para frente (regra de
    foreground do Windows); `WindowPattern.SetWindowVisualState(Normal)` + `SetFocus()` via UI
    Automation conseguem (o `SetFocus` até lança exceção, mas o foco muda).
32. Nas versões novas do HWiNFO o elemento de grupo tem 520 bytes e o de leitura 588: depois
    dos campos ANSI vêm cópias UTF-8 (grupo em 264/392; leitura em 316/444/572). Os nomes de
    grupo UTF-8 originais vêm em **inglês** (`System: ASUS`, `Memory Timings`, `PresentMon`),
    ao contrário dos ANSI, que vêm localizados. A `Read-HwinfoSensores` prefere os UTF-8.

## Histórico de aprendizados por máquina

- 2026-08-27 a 2026-09-04, PC (i5-14600K + RTX 3060 Ti, Windows 11): itens 1 a 25.
- 2026-09-05: skill criada a partir do PC; o `SensorsSM=1` no INI substitui o clique na GUI.
  Validação no próprio PC: `enumerar` real (22 grupos, 502 leituras), `mapear` reproduziu
  chave por chave o registro existente (única diferença real: a linha RAM, porque o PC tem
  40 GB e o rótulo antigo dizia 48 GB), `verificar -TesteCubo` 21/22 (a falha é essa RAM).
  Itens 26 a 32.
