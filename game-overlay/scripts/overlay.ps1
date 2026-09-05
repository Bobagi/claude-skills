# overlay.ps1 - CLI da skill game-overlay: instala e configura o overlay de jogos
# (HWiNFO le os sensores, RTSS desenha no jogo; CapFrameX para benchmark e teste;
# Intel PresentMon opcional). Replica o layout padrao do PC de referencia em
# qualquer maquina Windows, adaptando so o que o hardware obriga.
#
# Uso:  powershell -NoProfile -ExecutionPolicy Bypass -File overlay.ps1 <acao> [opcoes]
# Acoes que exigem administrador se auto-elevam (um UAC por chamada) ou, se o
# runner elevado estiver vivo (<Raiz>\_Config\jobs\_runner-vivo.txt), enfileiram nele.
#
# ASCII puro (PowerShell 5.1 le .ps1 sem BOM como ANSI). Sem em dash em lugar nenhum.
[CmdletBinding()]
param(
  [Parameter(Position = 0)]
  [ValidateSet('ajuda','status','baixar','instalar','configurar','tarefa','enumerar','mapear','aplicar','iniciar','verificar','leiame','tudo','desinstalar')]
  [string]$Acao = 'ajuda',
  [string]$Raiz,                # raiz da instalacao (padrao: D:\Tools\Monitoring se D: for disco local com espaco, senao C:\Tools\Monitoring)
  [switch]$ComPresentMon,       # instala tambem o Intel PresentMon (157 MB; o HWiNFO ja embute o dele, entao e opcional)
  [switch]$SemCapFrameX,        # nao instala o CapFrameX (perde o vkcube, usado no teste do overlay)
  [switch]$Forcar,              # rebaixa/reinstala/regrava mesmo que ja exista
  [switch]$DryRun,              # aplicar: so mostra o que escreveria no registro
  [switch]$TesteCubo,           # verificar: abre o vkcube e confere FPS > 0 e a injecao do RTSS
  [switch]$SemCubo,             # tudo: pula o teste com o vkcube
  [switch]$ManterInstaladores,  # tudo: nao apaga _Config\installers no fim
  [switch]$ApagarPasta,         # desinstalar: remove a raiz inteira
  [switch]$ApagarRegistro,      # desinstalar: remove HKCU\Software\HWiNFO64 (com backup .reg antes)
  [string]$LogArquivo,          # interno: arquivo onde a instancia elevada escreve a saida
  [switch]$SemElevar            # interno: nao tentar auto-elevar (ja esta elevado ou rodando via runner)
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
. (Join-Path $PSScriptRoot 'lib.ps1')

if ($LogArquivo) { $script:GO_LOG = $LogArquivo }
if (-not $Raiz) { $Raiz = Get-RaizPadrao }
$Raiz = $Raiz.TrimEnd('\')
$c = Get-Caminhos $Raiz
$acoesElevadas = @('instalar','configurar','tarefa','enumerar','aplicar','tudo','desinstalar')
$scriptParams = $PSBoundParameters

# ------------------------------------------------------------------ auto-elevacao
function Get-ArgsRepassados {
  $lista = @($Acao)
  foreach ($k in $scriptParams.Keys) {
    if ($k -in @('Acao','LogArquivo','SemElevar','Raiz')) { continue }
    $v = $scriptParams[$k]
    if ($v -is [switch]) { if ($v.IsPresent) { $lista += "-$k" } }
    else { $lista += "-$k"; $lista += ('"' + [string]$v + '"') }
  }
  $lista += '-Raiz'; $lista += ('"' + $Raiz + '"')
  return ($lista -join ' ')
}
$precisaAdmin = ($acoesElevadas -contains $Acao) -and -not ($Acao -eq 'aplicar' -and $DryRun)
if ($precisaAdmin -and -not (Test-Admin) -and -not $SemElevar) {
  $vivo = Join-Path $c.Jobs '_runner-vivo.txt'
  if (Test-Path $vivo) {
    # runner elevado vivo: enfileira e espera a saida
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $job = Join-Path $c.Jobs "job-$stamp-$Acao.ps1"
    $out = [IO.Path]::ChangeExtension($job, '.out')
    $cmd = '& "{0}" {1} -SemElevar' -f $PSCommandPath, (Get-ArgsRepassados)
    Set-Content -Path $job -Value $cmd -Encoding Ascii
    Write-Host "runner elevado ativo: job enfileirado ($job), esperando..."
    $t = Get-Date
    while (-not (Test-Path $out) -and ((Get-Date) - $t).TotalMinutes -lt 40) { Start-Sleep -Seconds 1 }
    Start-Sleep -Seconds 1
    if (Test-Path $out) { Get-Content $out -Encoding UTF8 | ForEach-Object { Write-Host $_ }; exit 0 }
    Write-Host "ERRO: o runner nao respondeu em 40 minutos"; exit 1
  }
  $log = Join-Path $env:TEMP ("game-overlay-{0}-{1}.log" -f $Acao, (Get-Date -Format 'yyyyMMdd-HHmmss'))
  $argStr = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" {1} -SemElevar -LogArquivo "{2}"' -f $PSCommandPath, (Get-ArgsRepassados), $log
  Write-Host "A acao '$Acao' precisa de administrador: abrindo um PowerShell elevado (confirme o UAC na tela)..."
  Write-Host "saida completa tambem em: $log"
  # Sem -Wait: ele esperaria tambem os DESCENDENTES (o HWiNFO/RTSS que a acao deixa abertos) e nunca voltaria.
  try { $p = Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argStr -PassThru }
  catch { Write-Host "ERRO: elevacao recusada ou falhou ($($_.Exception.Message))"; exit 2 }
  $p.WaitForExit()
  if (Test-Path $log) { Get-Content $log -Encoding UTF8 | ForEach-Object { Write-Host $_ } }
  exit $p.ExitCode
}

# ------------------------------------------------------------------ util local
function Ensure-Dirs {
  foreach ($d in @($c.Raiz, $c.Config, $c.Installers, $c.Jobs, $c.Backup, $c.Capturas)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
  }
}
function Get-ViaWinget([string]$Id, [string]$Dir) {
  if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Warn "winget nao disponivel"; return $null }
  if (Test-Path $Dir) { Remove-Item $Dir -Recurse -Force -ErrorAction SilentlyContinue }
  New-Item -ItemType Directory -Path $Dir -Force | Out-Null
  Say "winget download --id $Id"
  $saida = @()
  try { $saida = & winget download --id $Id -d $Dir --accept-source-agreements --accept-package-agreements 2>&1 } catch { $saida = @([string]$_.Exception.Message) }
  $f = Get-ChildItem $Dir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @('.exe','.zip','.msi') } | Sort-Object Length -Descending | Select-Object -First 1
  if ($f) { Unblock-File $f.FullName -ErrorAction SilentlyContinue; Say "winget baixou $($f.Name)"; return $f.FullName }
  Warn ("winget nao baixou {0}: {1}" -f $Id, ((@($saida) | Select-Object -Last 2) -join ' '))
  return $null
}
function Write-Modelo([string]$Origem, [string]$Destino) {
  $txt = Get-Content (Join-Path $PSScriptRoot $Origem) -Raw -Encoding Ascii
  $txt = $txt.Replace('__RAIZ__', $c.Raiz)
  Set-Content -Path $Destino -Value $txt -Encoding Ascii
  Say "escrito: $Destino"
}
function Load-Json([string]$Path) { return (Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json) }
function Save-Json($obj, [string]$Path) { ($obj | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }
function Save-Screenshot([string]$Path, [int]$ProcId) {
  # Traz a janela principal do processo para frente, descobre o retangulo dela por UI Automation
  # e delega a captura ao captura.ps1 (processo filho). A captura fica em arquivo separado
  # porque o AMSI do Defender bloqueia o script inteiro quando "ativar janela" e "capturar
  # tela" aparecem juntos no mesmo arquivo. Sem P/Invoke em lugar nenhum, pelo mesmo motivo.
  try {
    $x = 0; $y = 0; $w = 0; $h = 0
    if ($ProcId -gt 0) {
      Add-Type -AssemblyName Microsoft.VisualBasic, UIAutomationClient, UIAutomationTypes, WindowsBase
      $pr = Get-Process -Id $ProcId -ErrorAction SilentlyContinue
      if ($pr -and $pr.MainWindowHandle -ne [IntPtr]::Zero) {
        $el = [System.Windows.Automation.AutomationElement]::FromHandle($pr.MainWindowHandle)
        # AppActivate de um processo em segundo plano nao rouba o foco; o WindowPattern (UI Automation) consegue.
        try { [Microsoft.VisualBasic.Interaction]::AppActivate($ProcId) } catch { }
        try { $wp = $el.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern); $wp.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Normal) } catch { }
        try { $el.SetFocus() } catch { }
        Start-Sleep -Milliseconds 1500
        $r = $el.Current.BoundingRectangle
        if (-not $r.IsEmpty -and $r.Width -gt 0) { $x = [int]$r.X; $y = [int]$r.Y; $w = [int]$r.Width; $h = [int]$r.Height }
      }
    }
    $cap = Join-Path $PSScriptRoot 'captura.ps1'
    $saida = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cap -X $x -Y $y -W $w -H $h -Path $Path 2>&1
    if (Test-Path $Path) { return $true }
    Warn ("screenshot falhou: " + ((@($saida) | Select-Object -Last 2) -join ' '))
    return $false
  } catch { Warn "screenshot falhou: $($_.Exception.Message)"; return $false }
}
function Show-Osd([string]$Texto) {
  if (-not $Texto) { Say "(OSD do HWiNFO ausente no RTSS)"; return }
  Say "--- OSD que o HWiNFO escreve no RTSS ---"
  foreach ($l in (Get-LinhasOsd $Texto)) { Say ("   | " + $l) }
  Say "----------------------------------------"
}
function Wait-Fps([int]$Seg) {
  $t = Get-Date
  while (((Get-Date) - $t).TotalSeconds -lt $Seg) { if (Test-OsdTemFps) { return $true }; Start-Sleep -Seconds 2 }
  return $false
}

# ------------------------------------------------------------------ acoes
function Acao-Ajuda {
  @"
game-overlay / overlay.ps1  (raiz atual: $Raiz)

  status        estado geral: versoes, processos, tarefa, memoria compartilhada, texto do OSD
  baixar        baixa HWiNFO, RTSS, CapFrameX (e PresentMon com -ComPresentMon) para _Config\installers
  instalar      instala tudo em <Raiz>\{HWiNFO,RTSS,CapFrameX,PresentMon} sem tocar em Program Files  [admin]
  configurar    INI do HWiNFO, perfil Global do RTSS, hotkey Ctrl+Alt+O, launcher e runner       [admin]
  tarefa        registra a tarefa agendada elevada 'HWiNFO64 (monitoramento)' (logon +15 s)       [admin]
  enumerar      sobe RTSS+HWiNFO, le a memoria compartilhada e grava _Config\sensores.{json,txt}   [admin]
  mapear        casa o layout padrao com os sensores desta maquina -> _Config\layout.json
  aplicar       escreve o layout no registro do HWiNFO e reinicia na ordem certa (-DryRun so mostra) [admin]
  iniciar       dispara a tarefa (ou o launcher) e espera a linha FPS aparecer no OSD
  verificar     checklist completo; -TesteCubo abre o vkcube e confere FPS > 0 + screenshot
  leiame        gera <Raiz>\LEIAME.md a partir do modelo com os valores desta maquina
  tudo          baixar > instalar > configurar > tarefa > enumerar > mapear > aplicar > verificar > leiame [admin]
  desinstalar   remove tarefa, programas (-ApagarPasta, -ApagarRegistro)                            [admin]

Opcoes: -Raiz <pasta> -ComPresentMon -SemCapFrameX -Forcar -DryRun -TesteCubo -SemCubo -ManterInstaladores
"@ | ForEach-Object { Write-Host $_ }
}

function Acao-Status {
  Titulo "STATUS ($Raiz)"
  Say ("admin: {0}   maquina: {1}   usuario: {2}" -f (Test-Admin), $env:COMPUTERNAME, "$env:USERDOMAIN\$env:USERNAME")
  foreach ($x in @(@('HWiNFO', $c.HwinfoExe), @('RTSS', $c.RtssExe), @('CapFrameX', $c.CapExe), @('PresentMon', (Join-Path $c.PmDir 'PresentMonApplication\PresentMonUI.exe')))) {
    if (Test-Path $x[1]) { Say ("{0,-10} v{1}  {2}" -f $x[0], (Get-VersaoExe $x[1]), $x[1]) } else { Say ("{0,-10} ausente ({1})" -f $x[0], $x[1]) }
  }
  $pr = Get-Process -Name RTSS -ErrorAction SilentlyContinue | Select-Object -First 1
  $ph = Get-Process -Name HWiNFO64 -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($pr) { Say ("RTSS      rodando pid={0} desde {1}" -f $pr.Id, $pr.StartTime.ToString('dd/MM HH:mm:ss')) } else { Say "RTSS      parado" }
  if ($ph) { Say ("HWiNFO64  rodando pid={0} desde {1}" -f $ph.Id, $ph.StartTime.ToString('dd/MM HH:mm:ss')) } else { Say "HWiNFO64  parado" }
  if ($pr -and $ph) { if ($pr.StartTime -lt $ph.StartTime) { Say "ordem: RTSS antes do HWiNFO (certo)" } else { Warn "ordem: HWiNFO subiu ANTES do RTSS (FPS/Frametime somem; reinicie o HWiNFO)" } }
  try {
    $t = Get-ScheduledTask -TaskName $script:GO_TAREFA -ErrorAction Stop
    $ti = Get-ScheduledTaskInfo -TaskName $script:GO_TAREFA -ErrorAction SilentlyContinue
    Say ("tarefa    '{0}': {1}, RunLevel={2}, ultima execucao {3} resultado {4}" -f $script:GO_TAREFA, $t.State, $t.Principal.RunLevel, $ti.LastRunTime, $ti.LastTaskResult)
  } catch { Warn "tarefa '$($script:GO_TAREFA)' nao existe" }
  foreach ($hive in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run')) {
    $v = (Get-ItemProperty $hive -Name RTSS -ErrorAction SilentlyContinue).RTSS
    if ($v) { Warn "RTSS esta no Run de $hive ($v): pede UAC todo logon; remova (acao tarefa)" }
  }
  if (Test-Path $c.HwinfoIni) { Say ("INI HWiNFO: SensorInterval={0} SensorsSM={1} SensorsOnly={2}" -f (Get-IniValue $c.HwinfoIni 'Settings' 'SensorInterval'), (Get-IniValue $c.HwinfoIni 'Settings' 'SensorsSM'), (Get-IniValue $c.HwinfoIni 'Settings' 'SensorsOnly')) }
  if (Test-Path $c.RtssGlobal) { Say ("RTSS Global: EnableOSD={0} RefreshPeriod={1} StartWithWindows={2}" -f (Get-IniValue $c.RtssGlobal 'OSD' 'EnableOSD'), (Get-IniValue $c.RtssGlobal 'OSD' 'RefreshPeriod'), (Get-IniValue $c.RtssConfig 'Settings' 'StartWithWindows')) }
  $sens = Read-HwinfoSensores
  if ($sens) { Say ("SM HWiNFO: {0} grupos, {1} leituras, polling {2} ms, grupo [RTSS] presente={3}" -f $sens.grupos.Count, $sens.leituras.Count, $sens.polling, (Test-GrupoRtss $sens)) }
  else { Say "SM HWiNFO: indisponivel (SensorsSM desligado, HWiNFO parado, ou limite de 12 h da versao gratis)" }
  $osd = Get-OsdHwinfo
  if ($null -ne $osd) { Say ("OSD: linha FPS presente={0}" -f (Test-OsdTemFps)); Show-Osd $osd } else { Say "OSD: RTSS sem slot do HWiNFO (RTSS parado ou HWiNFO sem OSD)" }
  $apps = @(Read-RtssApps)
  if ($apps.Count -gt 0) { foreach ($a in $apps) { Say ("app enganchado: pid={0} {1} ({2} FPS)" -f $a.Pid, $a.Exe, $a.Fps) } } else { Say "apps enganchados no RTSS: nenhum" }
  if (Test-Path $c.Layout) { $lay = Load-Json $c.Layout; Say ("layout.json: {0} linhas, {1} nao mapeadas, PC total={2} (gerado {3})" -f $lay.linhas.Count, $lay.naoMapeado.Count, [bool]$lay.pcTotal, $lay.geradoEm) } else { Say "layout.json: ausente (rode enumerar + mapear)" }
  if (Test-Path $c.InicioLog) { Say "inicio.log (ultimas linhas):"; Get-Content $c.InicioLog -Tail 8 | ForEach-Object { Say ("   " + $_) } }
}

function Acao-Baixar {
  Titulo "BAIXAR"
  Ensure-Dirs
  $cfg = Get-Cfg $Raiz
  $arq = [ordered]@{}
  # ---- HWiNFO: pagina oficial (precisa de UA de browser) -> espelho do instalador; fallback zip portatil; fallback winget
  $hwExe = Join-Path $c.Installers 'hwinfo-setup.exe'; $hwZip = Join-Path $c.Installers 'hwinfo-portable.zip'
  if (-not $Forcar -and (Test-Path $hwExe)) { Say "HWiNFO: instalador ja baixado ($hwExe)"; $arq['hwinfo'] = $hwExe }
  elseif (-not $Forcar -and (Test-Path $hwZip)) { Say "HWiNFO: zip portatil ja baixado ($hwZip)"; $arq['hwinfo'] = $hwZip }
  else {
    $html = Get-PaginaTexto $script:GO_HWINFO_PAGINA
    $inst = @(); $port = @(); $verTxt = $null
    if ($html) {
      foreach ($m in [regex]::Matches($html, 'https?://[^"''\s<>]+/hwi_\d{3,4}x\.exe')) { $inst += $m.Value }
      foreach ($m in [regex]::Matches($html, 'https?://[^"''\s<>]+/hwi64_\d{3,4}\.exe')) { $inst += $m.Value }
      foreach ($m in [regex]::Matches($html, 'https?://[^"''\s<>]+/hwi_\d{3,4}\.zip')) { $port += $m.Value }
      if ($html -match 'Version\s+(\d+\.\d+)') { $verTxt = $Matches[1] }
      Say ("HWiNFO: pagina diz versao {0}; {1} link(s) de instalador, {2} de portatil" -f $verTxt, $inst.Count, $port.Count)
    }
    $ok = $false
    foreach ($u in @($inst | Select-Object -Unique)) { if (Get-Arquivo $u $hwExe 'exe') { $ok = $true; $arq['hwinfo'] = $hwExe; break } }
    if (-not $ok) {
      $ordem = @($port | Select-Object -Unique | Sort-Object { if ($_ -like '*hwinfo.com*') { 0 } else { 1 } })
      foreach ($u in $ordem) { if (Get-Arquivo $u $hwZip 'zip') { $ok = $true; $arq['hwinfo'] = $hwZip; break } }
    }
    if (-not $ok) {
      $esp = Find-HwinfoNoEspelho
      if ($esp -and (Get-Arquivo $esp.Url $hwExe 'exe')) { $ok = $true; $arq['hwinfo'] = $hwExe; if (-not $verTxt) { $verTxt = ('{0}.{1}' -f ([string]$esp.Versao).Substring(0, 1), ([string]$esp.Versao).Substring(1)) } }
    }
    if (-not $ok) {
      $w = Get-ViaWinget 'REALiX.HWiNFO' (Join-Path $c.Installers 'winget-hwinfo')
      if ($w -and $w -like '*.exe') { Move-Item $w $hwExe -Force; $ok = $true; $arq['hwinfo'] = $hwExe }
      Remove-Item (Join-Path $c.Installers 'winget-hwinfo') -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (-not $ok) { Fail "HWiNFO: nao consegui baixar. Baixe o pacote 'Installer' em https://www.hwinfo.com/download/ e salve como $hwExe (ou o 'Portable' como $hwZip) e rode de novo." }
    if ($verTxt) { Set-CfgProp $cfg 'hwinfoVersaoBaixada' $verTxt }
  }
  # ---- RTSS: winget (hash verificado) -> zip direto do espelho -> manual
  $rtssExe = Join-Path $c.Installers 'rtss-setup.exe'
  if (-not $Forcar -and (Test-Path $rtssExe)) { Say "RTSS: instalador ja baixado ($rtssExe)" }
  else {
    $z = Get-ViaWinget 'Guru3D.RTSS' (Join-Path $c.Installers 'winget-rtss')
    if (-not $z) { $z = Join-Path $c.Installers 'rtss.zip'; if (-not (Get-Arquivo $script:GO_RTSS_ZIP_DIRETO $z 'zip')) { $z = $null } }
    if ($z -and $z -like '*.zip') {
      $dir = Join-Path $c.Installers 'rtss-zip'
      Expand-Archive -Path $z -DestinationPath $dir -Force
      $setup = Get-ChildItem $dir -Filter 'RTSSSetup*.exe' -Recurse | Select-Object -First 1
      if ($setup) { Move-Item $setup.FullName $rtssExe -Force }
      Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
    } elseif ($z -and $z -like '*.exe') { Move-Item $z $rtssExe -Force }
    Remove-Item (Join-Path $c.Installers 'winget-rtss') -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $c.Installers 'rtss.zip') -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $rtssExe)) { Fail "RTSS: nao consegui baixar. Baixe em https://www.guru3d.com/download/rtss-rivatuner-statistics-server-download/ e salve o RTSSSetupNNN.exe como $rtssExe e rode de novo." }
    Unblock-File $rtssExe -ErrorAction SilentlyContinue
  }
  $arq['rtss'] = $rtssExe
  # ---- CapFrameX portatil (traz o vkcube, app Vulkan minusculo para testar o overlay sem jogo)
  if (-not $SemCapFrameX) {
    $capZip = Join-Path $c.Installers 'capframex-portable.zip'
    if (-not $Forcar -and (Test-Path $capZip)) { Say "CapFrameX: zip ja baixado" }
    else {
      $a = Get-GithubUltimoAsset 'CXWorld/CapFrameX' 'portable\.zip$'
      $url = $null
      if ($a -and $a.Url) { $url = $a.Url } elseif ($a -and $a.Tag) { $url = "https://github.com/CXWorld/CapFrameX/releases/download/$($a.Tag)/release_$($a.Tag.TrimStart('v'))_portable.zip" }
      if (-not $url -or -not (Get-Arquivo $url $capZip 'zip')) { Warn "CapFrameX: nao baixou (seguindo sem ele; o teste com vkcube fica indisponivel)" }
      elseif ($a) { Set-CfgProp $cfg 'capframexVersaoBaixada' $a.Tag }
    }
    if (Test-Path $capZip) { $arq['capframex'] = $capZip }
  }
  # ---- Intel PresentMon (opcional: o HWiNFO embute o PresentMon dele, CPU Busy / GPU Busy vem de la)
  if ($ComPresentMon) {
    $pm = Join-Path $c.Installers 'presentmon.msi'
    if (-not $Forcar -and (Test-Path $pm)) { Say "PresentMon: msi ja baixado" }
    else {
      $a = Get-GithubUltimoAsset 'GameTechDev/PresentMon' '\.msi$'
      $url = $null
      if ($a -and $a.Url) { $url = $a.Url } elseif ($a -and $a.Tag) { $url = "https://github.com/GameTechDev/PresentMon/releases/download/$($a.Tag)/PresentMon-$($a.Tag).msi" }
      if (-not $url -or -not (Get-Arquivo $url $pm 'msi')) { Warn "PresentMon: nao baixou (seguindo sem ele)" }
      elseif ($a) { Set-CfgProp $cfg 'presentmonVersaoBaixada' $a.Tag }
    }
    if (Test-Path $pm) { $arq['presentmon'] = $pm }
  }
  Set-CfgProp $cfg 'arquivos' ([pscustomobject]$arq)
  Set-CfgProp $cfg 'comPresentMon' ([bool]$ComPresentMon -or [bool]$cfg.comPresentMon)
  Set-CfgProp $cfg 'semCapFrameX' ([bool]$SemCapFrameX)
  Save-Cfg $Raiz $cfg
  Say "downloads prontos em $($c.Installers)"
}

function Acao-Instalar {
  Titulo "INSTALAR"
  Ensure-Dirs
  $cfg = Get-Cfg $Raiz
  if (-not $cfg.arquivos) { Say "sem downloads registrados: rodando 'baixar' antes"; Acao-Baixar; $cfg = Get-Cfg $Raiz }
  $arq = $cfg.arquivos
  if ($c.Raiz -match '\s') { Warn "a raiz tem espaco no caminho; o instalador NSIS do RTSS (/D=) costuma aceitar, mas prefira D:\Tools\Monitoring" }
  Stop-Monitoramento
  # HWiNFO (Inno Setup: /DIR aceita aspas) ou zip portatil
  if ((Test-Path $c.HwinfoExe) -and -not $Forcar) { Say "HWiNFO ja instalado em $($c.HwinfoDir) (v$(Get-VersaoExe $c.HwinfoExe))" }
  elseif ($arq.hwinfo -and (Test-Path $arq.hwinfo)) {
    if ($arq.hwinfo -like '*.zip') {
      Say "HWiNFO: extraindo zip portatil em $($c.HwinfoDir)"
      Expand-Archive -Path $arq.hwinfo -DestinationPath $c.HwinfoDir -Force
    } else {
      Say "HWiNFO: instalador silencioso em $($c.HwinfoDir)"
      $p = Start-Process -FilePath $arq.hwinfo -ArgumentList ('/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /NOICONS /MERGETASKS="!desktopicon" /DIR="{0}"' -f $c.HwinfoDir) -Wait -PassThru
      Say "HWiNFO: instalador saiu com codigo $($p.ExitCode)"
    }
    if (-not (Test-Path $c.HwinfoExe)) { Fail "HWiNFO64.EXE nao apareceu em $($c.HwinfoDir)" }
  } else { Fail "instalador do HWiNFO nao encontrado; rode 'baixar'" }
  # RTSS (NSIS: /S e /D=<pasta> por ULTIMO e SEM aspas)
  if ((Test-Path $c.RtssExe) -and -not $Forcar) { Say "RTSS ja instalado em $($c.RtssDir) (v$(Get-VersaoExe $c.RtssExe))" }
  elseif ($arq.rtss -and (Test-Path $arq.rtss)) {
    Say "RTSS: instalador silencioso em $($c.RtssDir)"
    $p = Start-Process -FilePath $arq.rtss -ArgumentList ('/S /D={0}' -f $c.RtssDir) -Wait -PassThru
    Say "RTSS: instalador saiu com codigo $($p.ExitCode)"
    if (-not (Test-Path $c.RtssExe)) { Fail "RTSS.exe nao apareceu em $($c.RtssDir)" }
  } else { Fail "instalador do RTSS nao encontrado; rode 'baixar'" }
  # CapFrameX portatil
  if ($arq.capframex -and (Test-Path $arq.capframex)) {
    if ((Test-Path $c.CapExe) -and -not $Forcar) { Say "CapFrameX ja presente" }
    else { Say "CapFrameX: extraindo em $($c.CapDir)"; Expand-Archive -Path $arq.capframex -DestinationPath $c.CapDir -Force }
  }
  # Intel PresentMon (MSI WiX). O servico dele vai obrigatoriamente para C:\Program Files\Intel (5 MB).
  if ($arq.presentmon -and (Test-Path $arq.presentmon)) {
    $pmUi = Join-Path $c.PmDir 'PresentMonApplication\PresentMonUI.exe'
    if ((Test-Path $pmUi) -and -not $Forcar) { Say "PresentMon ja instalado" }
    else {
      Say "PresentMon: msiexec silencioso em $($c.PmDir)"
      $logMsi = Join-Path $c.Config 'presentmon-msi.log'
      $p = Start-Process -FilePath msiexec.exe -ArgumentList ('/i "{0}" /qn /norestart APPLICATIONFOLDER="{1}" /l*v "{2}"' -f $arq.presentmon, $c.PmDir, $logMsi) -Wait -PassThru
      Say "PresentMon: msiexec saiu com codigo $($p.ExitCode)"
    }
  }
  # os instaladores abrem os programas sozinhos no fim; fecha tudo para poder escrever a configuracao
  Start-Sleep -Seconds 3
  Stop-Monitoramento
  Remove-RtssDoRun $c
  New-Atalho (Join-Path $c.Raiz 'HWiNFO (sensores).lnk') $c.HwinfoExe $c.HwinfoDir
  New-Atalho (Join-Path $c.Raiz 'RTSS (overlay).lnk') $c.RtssExe $c.RtssDir
  New-Atalho (Join-Path $c.Raiz 'CapFrameX (benchmark).lnk') $c.CapExe $c.CapDir
  New-Atalho (Join-Path $c.Raiz 'Intel PresentMon.lnk') (Join-Path $c.PmDir 'PresentMonApplication\PresentMonUI.exe') (Join-Path $c.PmDir 'PresentMonApplication')
  Set-CfgProp $cfg 'versoes' ([pscustomobject]@{ hwinfo = (Get-VersaoExe $c.HwinfoExe); rtss = (Get-VersaoExe $c.RtssExe); capframex = (Get-VersaoExe $c.CapExe)
                                                presentmon = (Get-VersaoExe (Join-Path $c.PmDir 'PresentMonApplication\PresentMonUI.exe')) })
  Set-CfgProp $cfg 'instaladoEm' (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
  Save-Cfg $Raiz $cfg
  Say ("instalado: HWiNFO v{0}, RTSS v{1}, CapFrameX v{2}" -f $cfg.versoes.hwinfo, $cfg.versoes.rtss, $cfg.versoes.capframex)
}

function Acao-Configurar {
  Titulo "CONFIGURAR"
  Ensure-Dirs
  if (-not (Test-Path $c.HwinfoExe) -or -not (Test-Path $c.RtssExe)) { Fail "HWiNFO ou RTSS nao instalados em $Raiz; rode 'instalar'" }
  Stop-Monitoramento   # os dois reescrevem os proprios arquivos ao sair: so escreva com eles fechados
  # HWiNFO: INI (configuracoes portaveis). SensorsSM=1 liga o Shared Memory Support (12 h na versao gratis).
  Set-IniKeys $c.HwinfoIni 'Settings' ([ordered]@{ SensorsOnly = 1; Theme = 1; MinimalizeMainWnd = 1; MinimalizeSensors = 1; MinimalizeSensorsClose = 1
                                                   ShowWelcomeAndProgress = 0; SensorInterval = 1000; AutoUpdateBetaDisable = 1; SensorsSM = 1 })
  Say "HWiNFO64.INI escrito (somente sensores, minimizado, 1000 ms, Shared Memory ligado)"
  # HWiNFO: registro (hotkey Ctrl+Alt+O, ordem fixa, OSD proprio desligado: quem desenha e o RTSS)
  Set-RegValues 'HKCU:\Software\HWiNFO64\Sensors' ([ordered]@{ RtssToggleHotKey = 0x0003004F; OrderLocked = 1; OsdEnabled = 0 })
  Say "registro do HWiNFO: hotkey Ctrl+Alt+O, OrderLocked=1, OsdEnabled=0"
  # RTSS: perfil Global. RefreshPeriod=1000 casa com o SensorInterval do HWiNFO (abaixo disso FPS e Frametime zeram no jogo).
  Set-IniKeys $c.RtssGlobal 'OSD' ([ordered]@{ EnableOSD = 1; EnableBgnd = 1; EnableFill = 0; EnableStat = 0; BaseColor = '00FF8000'; BgndColor = '00000000'; FillColor = '80000000'
                                               PositionX = 1; PositionY = 1; ZoomRatio = 2; CoordinateSpace = 0; RefreshPeriod = 1000; IntegerFramerate = 1; MaximumFrametime = 0
                                               EnableFrametimeHistory = 0; FrametimeHistoryWidth = -32; FrametimeHistoryHeight = -4; ScaleToFit = 0 })
  Set-IniKeys $c.RtssGlobal 'Statistics' ([ordered]@{ FramerateAveragingInterval = 1000 })
  Set-IniKeys $c.RtssGlobal 'Framerate'  ([ordered]@{ Limit = 0; PassiveWait = 1 })
  Set-IniKeys $c.RtssGlobal 'Hooking'    ([ordered]@{ EnableHooking = 1; InjectionDelay = 15000 })
  Set-IniKeys $c.RtssGlobal 'Font'       ([ordered]@{ Height = -9; Weight = 400; Face = 'Unispace' })
  foreach ($r in @('Direct3D8','Direct3D9','Direct3D10','Direct3D11','Direct3D12','OpenGL','Vulkan')) { Set-IniKeys $c.RtssGlobal "Renderer$r" ([ordered]@{ Implementation = 2 }) }
  Set-IniKeys $c.RtssConfig 'Settings' ([ordered]@{ StartMinimized = 1; StartWithWindows = 0; HidePreCreatedProfiles = 1; EnableEncoderServer = 1; Enable64Bit = 1; ShowTooltips = 1; FirstRun = 0 })
  Say "RTSS: Profiles\Global e Profiles\Config escritos (OSD laranja canto superior esquerdo, 1000 ms, sem autostart proprio)"
  Remove-RtssDoRun $c
  Write-Modelo 'iniciar-monitoramento.ps1' $c.Launcher
  Write-Modelo 'runner.ps1' $c.Runner
  $cfg = Get-Cfg $Raiz; Set-CfgProp $cfg 'configuradoEm' (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); Save-Cfg $Raiz $cfg
}

function Acao-Tarefa {
  Titulo "TAREFA AGENDADA"
  Ensure-Dirs
  if (-not (Test-Path $c.Launcher)) { Write-Modelo 'iniciar-monitoramento.ps1' $c.Launcher }
  Register-TarefaMonitoramento $c
  Remove-RtssDoRun $c
}

function Acao-Enumerar {
  Titulo "ENUMERAR SENSORES"
  Ensure-Dirs
  if (-not (Test-Path $c.HwinfoExe)) { Fail "HWiNFO nao instalado em $Raiz" }
  $sm = Get-IniValue $c.HwinfoIni 'Settings' 'SensorsSM'
  $precisaReiniciar = $false
  if ($sm -ne '1') {
    if (Test-Rodando 'HWiNFO64') { Say "SensorsSM nao esta ligado no INI: fechando o HWiNFO para gravar"; Get-Process -Name HWiNFO64 | Stop-Process -Force; Start-Sleep -Seconds 3 }
    Set-IniKeys $c.HwinfoIni 'Settings' ([ordered]@{ SensorsSM = 1 })
    Say "INI: SensorsSM=1"
    $precisaReiniciar = $true
  }
  if ((Test-Rodando 'HWiNFO64') -and -not $precisaReiniciar -and -not (Test-HwinfoSM)) {
    Say "HWiNFO rodando mas sem memoria compartilhada (limite de 12 h?): reiniciando"
    Get-Process -Name HWiNFO64 | Stop-Process -Force; Start-Sleep -Seconds 3
  }
  Start-NaOrdem $c
  Say "esperando a memoria compartilhada do HWiNFO (ate 120 s; se demorar, olhe a tela: pode haver um dialogo do HWiNFO)"
  if (-not (Wait-HwinfoSM 120)) { Fail "memoria compartilhada do HWiNFO nao apareceu. Confira na tela se o HWiNFO abriu algum dialogo; se a versao gratis desligou o Shared Memory, feche o HWiNFO e rode de novo." }
  # espera a enumeracao estabilizar (quantidade de leituras igual em duas leituras seguidas) e o grupo [RTSS] aparecer
  $sens = Read-HwinfoSensores; $t = Get-Date
  while (((Get-Date) - $t).TotalSeconds -lt 90) {
    Start-Sleep -Seconds 5
    $s2 = Read-HwinfoSensores
    if ($s2 -and $sens -and $s2.leituras.Count -eq $sens.leituras.Count -and (Test-GrupoRtss $s2)) { $sens = $s2; break }
    if ($s2) { $sens = $s2 }
  }
  if (-not $sens) { Fail "nao consegui ler os sensores" }
  Save-Json $sens $c.Sensores
  Write-SensoresTxt $sens $c.SensoresTxt
  Say ("{0} grupos, {1} leituras, polling {2} ms, grupo [RTSS] presente={3}" -f $sens.grupos.Count, $sens.leituras.Count, $sens.polling, (Test-GrupoRtss $sens))
  foreach ($g in $sens.grupos) { Say ("   [{0,2}] {1}_{2}  {3}" -f $g.idx, $g.id, $g.inst, $g.nomeOrig) }
  if (-not (Test-GrupoRtss $sens)) { Warn "grupo [RTSS] ausente: o HWiNFO subiu antes do RTSS? rode 'enumerar' de novo com os dois fechados" }
  Say "gravado: $($c.Sensores) e $($c.SensoresTxt)"
}

function Acao-Mapear {
  Titulo "MAPEAR LAYOUT"
  if (-not (Test-Path $c.Sensores)) { Fail "sem $($c.Sensores); rode 'enumerar' primeiro" }
  $padrao = Load-Json (Join-Path $PSScriptRoot 'layout-padrao.json')
  $sens = Load-Json $c.Sensores
  $hw = Get-Hardware
  Say ("hardware: CPU '{0}' -> '{1}'; GPU '{2}' -> '{3}'; VRAM {4} MB; RAM {5} MB visiveis ({6} GB); notebook={7}" -f $hw.Cpu, $hw.CpuCurto, $hw.Gpu, $hw.GpuCurto, $hw.VramMB, $hw.RamMB, $hw.RamGB, $hw.Notebook)
  foreach ($d in $hw.Discos) { Say ("   disco #{0} {1} {2} [{3}] {4} GB" -f $d.Numero, $d.Modelo, $d.Tipo, ($d.Letras -join ','), $d.TamanhoGB) }
  $lay = Resolve-Layout $padrao $sens $hw
  if ((Test-Path $c.Layout) -and -not $Forcar) {
    $bk = Join-Path $c.Backup ("layout-{0}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    if (-not (Test-Path $c.Backup)) { New-Item -ItemType Directory -Path $c.Backup -Force | Out-Null }
    Copy-Item $c.Layout $bk -Force; Say "layout.json anterior guardado em $bk"
  }
  Save-Json $lay $c.Layout
  Say "linha  rotulo            <- grupo / leitura original (chave de registro) [confianca]"
  foreach ($l in $lay.linhas) {
    $extra = ''; if ($l.unidade) { $extra += " unidade='$($l.unidade)'" }; if ($l.valueMult) { $extra += " x$($l.valueMult)" }; if ($l.grafico) { $extra += ' +grafico' }
    Say ("{0,4}   {1,-17} <- {2} / {3} ({4}_{5}\{6}{7}) [{8}{9}]{10}" -f $l.linha, $l.label, $l.grupoNome, $l.leituraOrig, $l.grupoId, $l.inst, $l.tipoNome, $l.idx, $l.confianca, (& { if ($l.candidatos -gt 1) { ", $($l.candidatos) candidatos" } else { '' } }), $extra)
  }
  if ($lay.pcTotal) { Say ("{0,4}   {1,-17} <- sensor customizado '{2}' = {3}" -f $lay.pcTotal.linha, $lay.pcTotal.label, $lay.pcTotal.nome, $lay.pcTotal.formula) }
  else { Warn "PC total NAO criado: $($lay.pcTotalMotivo)" }
  foreach ($a in $lay.auxiliares) { Say ("       auxiliar {0,-12} <- {1} ({2}_{3}\{4}{5}), fora do OSD" -f $a.apelido, $a.leituraOrig, $a.grupoId, $a.inst, $a.tipoNome, $a.idx) }
  if ($lay.naoMapeado.Count -gt 0) {
    Warn "$($lay.naoMapeado.Count) linha(s) NAO mapeada(s):"
    foreach ($n in $lay.naoMapeado) { Warn ("   linha {0} '{1}': {2}" -f $n.linha, $n.chave, $n.motivo); if ($n.candidatosDoTipo) { Say ("      leituras do tipo no grupo: " + ($n.candidatosDoTipo -join ' | ')) } }
    Warn "revise $($c.SensoresTxt), edite $($c.Layout) (grupoId/inst/tipoNome/idx/label) e rode 'aplicar'"
  }
  Say "gravado: $($c.Layout)"
}

function Acao-Aplicar {
  Titulo "APLICAR LAYOUT NO REGISTRO"
  if (-not (Test-Path $c.Layout)) { Fail "sem $($c.Layout); rode 'mapear' primeiro" }
  $lay = Load-Json $c.Layout
  if ($DryRun) { Write-Layout $lay $c $true; return }
  if (Test-Rodando 'HWiNFO64') { Say "fechando o HWiNFO (ele regravaria o registro ao sair)"; Get-Process -Name HWiNFO64 | Stop-Process -Force; Start-Sleep -Seconds 3 }
  Write-Layout $lay $c $false
  Start-NaOrdem $c
  $ok = Wait-Fps 90
  Say "linha FPS presente no OSD=$ok"
  $osd = Get-OsdHwinfo
  Show-Osd $osd
  if ($osd) {
    $cmp = Compare-OsdComLayout $lay $osd
    if ($cmp.Faltando.Count -gt 0) { Warn ("linhas do layout ausentes no OSD: " + ($cmp.Faltando -join ', ') + " (sensor customizado novo so aparece apos reinicio do HWiNFO; se persistir, confira grupoId/idx no layout.json)") }
    else { Say "todas as linhas do layout estao no OSD, ordem ok=$($cmp.OrdemOk)" }
  }
  $cfg = Get-Cfg $Raiz; Set-CfgProp $cfg 'layoutAplicadoEm' (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); Save-Cfg $Raiz $cfg
}

function Acao-Iniciar {
  Titulo "INICIAR"
  $viaTarefa = $false
  try { Get-ScheduledTask -TaskName $script:GO_TAREFA -ErrorAction Stop | Out-Null; Start-ScheduledTask -TaskName $script:GO_TAREFA -ErrorAction Stop; $viaTarefa = $true; Say "tarefa '$($script:GO_TAREFA)' disparada" }
  catch { Warn "nao deu para disparar a tarefa ($($_.Exception.Message))" }
  if (-not $viaTarefa) {
    if (Test-Admin) { Start-NaOrdem $c } else { Fail "sem tarefa agendada e sem admin: rode 'tarefa' (ou 'tudo')" }
  }
  $ok = Wait-Fps 120
  Say "linha FPS presente no OSD=$ok"
  Show-Osd (Get-OsdHwinfo)
  if (Test-Path $c.InicioLog) { Say "inicio.log:"; Get-Content $c.InicioLog -Tail 8 | ForEach-Object { Say ("   " + $_) } }
}

function Acao-Verificar {
  Titulo "VERIFICAR"
  $itens = New-Object System.Collections.ArrayList
  function Chk([string]$nome, [bool]$ok, [string]$det) { [void]$itens.Add([pscustomobject]@{ Nome = $nome; Ok = $ok; Det = $det }); Say (("[{0}] {1}: {2}" -f (& { if ($ok) { 'PASS' } else { 'FAIL' } }), $nome, $det)) }
  Chk 'RTSS.exe presente' (Test-Path $c.RtssExe) $c.RtssExe
  Chk 'HWiNFO64.EXE presente' (Test-Path $c.HwinfoExe) $c.HwinfoExe
  $pr = Get-Process -Name RTSS -ErrorAction SilentlyContinue | Select-Object -First 1
  $ph = Get-Process -Name HWiNFO64 -ErrorAction SilentlyContinue | Select-Object -First 1
  Chk 'RTSS rodando' ([bool]$pr) (& { if ($pr) { "pid $($pr.Id)" } else { 'parado' } })
  Chk 'HWiNFO64 rodando' ([bool]$ph) (& { if ($ph) { "pid $($ph.Id)" } else { 'parado' } })
  if ($pr -and $ph) { Chk 'ordem RTSS antes do HWiNFO' ($pr.StartTime -lt $ph.StartTime) ("RTSS {0} / HWiNFO {1}" -f $pr.StartTime.ToString('HH:mm:ss'), $ph.StartTime.ToString('HH:mm:ss')) }
  try { $t = Get-ScheduledTask -TaskName $script:GO_TAREFA -ErrorAction Stop; $ti = Get-ScheduledTaskInfo -TaskName $script:GO_TAREFA
        Chk 'tarefa agendada elevada' ($t.Principal.RunLevel -eq 'Highest' -and $t.State -ne 'Disabled') ("estado {0}, RunLevel {1}, ultimo resultado {2}" -f $t.State, $t.Principal.RunLevel, $ti.LastTaskResult)
        $st = $t.Settings
        Chk 'tarefa sobe na bateria' (-not $st.DisallowStartIfOnBatteries -and -not $st.StopIfGoingOnBatteries) "AllowStartIfOnBatteries/DontStopIfGoingOnBatteries" }
  catch { Chk 'tarefa agendada elevada' $false 'nao existe' }
  $run = $false
  foreach ($hive in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run')) { if ((Get-ItemProperty $hive -Name RTSS -ErrorAction SilentlyContinue).RTSS) { $run = $true } }
  Chk 'RTSS fora do Run (sem UAC no logon)' (-not $run) ''
  Chk 'HWiNFO INI SensorInterval=1000' ((Get-IniValue $c.HwinfoIni 'Settings' 'SensorInterval') -eq '1000') ("valor: " + (Get-IniValue $c.HwinfoIni 'Settings' 'SensorInterval'))
  Chk 'HWiNFO INI SensorsOnly=1' ((Get-IniValue $c.HwinfoIni 'Settings' 'SensorsOnly') -eq '1') ''
  Chk 'RTSS RefreshPeriod=1000' ((Get-IniValue $c.RtssGlobal 'OSD' 'RefreshPeriod') -eq '1000') ("valor: " + (Get-IniValue $c.RtssGlobal 'OSD' 'RefreshPeriod'))
  Chk 'RTSS EnableOSD=1' ((Get-IniValue $c.RtssGlobal 'OSD' 'EnableOSD') -eq '1') ''
  Chk 'RTSS StartWithWindows=0' ((Get-IniValue $c.RtssConfig 'Settings' 'StartWithWindows') -eq '0') ''
  $hk = (Get-ItemProperty 'HKCU:\Software\HWiNFO64\Sensors' -Name RtssToggleHotKey -ErrorAction SilentlyContinue).RtssToggleHotKey
  Chk 'hotkey Ctrl+Alt+O' ($hk -eq 0x0003004F) ("RtssToggleHotKey=0x{0:X8}" -f [int]$hk)
  $osd = Get-OsdHwinfo
  Chk 'OSD do HWiNFO no RTSS' ($null -ne $osd) ''
  Chk 'linha FPS no OSD (grupo [RTSS])' (Test-OsdTemFps) ''
  $lay = $null
  if (Test-Path $c.Layout) {
    $lay = Load-Json $c.Layout
    if ($osd) {
      $cmp = Compare-OsdComLayout $lay $osd
      Chk 'todas as linhas do layout no OSD' ($cmp.Faltando.Count -eq 0) (& { if ($cmp.Faltando.Count -gt 0) { "faltam: " + ($cmp.Faltando -join ', ') } else { "$($cmp.Itens.Count) linhas" } })
      Chk 'ordem das linhas' $cmp.OrdemOk ''
    }
    Chk 'layout sem linhas nao mapeadas' ($lay.naoMapeado.Count -eq 0) (& { if ($lay.naoMapeado.Count -gt 0) { ($lay.naoMapeado | ForEach-Object { $_.chave }) -join ', ' } else { '' } })
  } else { Chk 'layout.json presente' $false 'rode enumerar + mapear + aplicar' }
  Show-Osd $osd
  if ($TesteCubo) {
    if (-not (Test-Path $c.Cubo)) { Chk 'teste vkcube' $false "vkcube ausente ($($c.Cubo)); instale o CapFrameX" }
    else {
      Say "abrindo o vkcube por 30 s (o RTSS injeta apos InjectionDelay)..."
      $pc = Start-Process -FilePath $c.Cubo -WorkingDirectory (Split-Path $c.Cubo) -PassThru
      Start-Sleep -Seconds 28
      $osd2 = Get-OsdHwinfo
      $fps = -1
      if ($osd2 -and $osd2 -match '(?m)^FPS:\s*([\d\.,]+)') { $fps = [double](($Matches[1]) -replace ',', '.') }
      $apps = @(Read-RtssApps)
      $cubo = $apps | Where-Object { $_.Exe -like '*vkcube*' } | Select-Object -First 1
      Chk 'RTSS enganchou o vkcube' ([bool]$cubo) (& { if ($cubo) { "pid $($cubo.Pid), $($cubo.Fps) FPS pelo RTSS" } else { 'nao apareceu na lista de apps do RTSS' } })
      Chk 'FPS > 0 no OSD com o cubo aberto' ($fps -gt 0) ("FPS lido: $fps")
      if ($osd2 -and $osd2 -match '(?m)^Frametime:\s*([\d\.,]+)') { Chk 'Frametime > 0' ([double]($Matches[1] -replace ',', '.') -gt 0) ("valor: $($Matches[1]) ms") }
      # Desenho do OSD dentro do app: dwOSDFrame > 0. No PC de referencia o vkcube (Vulkan puro) e
      # contado mas NAO recebe o desenho, entao isto e informativo, nao FAIL: a prova visual e num jogo.
      if ($cubo) {
        if ($cubo.OsdFrame -gt 0) { Say "[INFO] OSD desenhado dentro do vkcube (dwOSDFrame=$($cubo.OsdFrame)): a captura abaixo mostra o overlay" }
        else { Say "[INFO] RTSS conta os quadros do vkcube mas nao desenha o OSD nele (dwOSDFrame=0); a captura mostra so o cubo. Confirme o desenho abrindo um jogo (D3D) com o overlay ligado (Ctrl+Alt+O)" }
      }
      $shot = Join-Path $c.Capturas ("overlay-{0}.png" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
      if (Save-Screenshot $shot $pc.Id) { Say "screenshot da janela do vkcube: $shot" }
      Show-Osd $osd2
      try { Stop-Process -Id $pc.Id -Force -ErrorAction Stop } catch { }
    }
  }
  $falhas = @($itens | Where-Object { -not $_.Ok })
  Say ""
  Say ("RESULTADO: {0} de {1} checagens OK{2}" -f ($itens.Count - $falhas.Count), $itens.Count, (& { if ($falhas.Count -gt 0) { "; FALHAS: " + (($falhas | ForEach-Object { $_.Nome }) -join ', ') } else { '' } }))
  if ($falhas.Count -gt 0) { $script:GO_EXIT = 3 }
}

function Acao-Leiame {
  Titulo "LEIAME"
  if (-not (Test-Path $c.Layout)) { Fail "sem $($c.Layout); rode 'mapear' primeiro" }
  $lay = Load-Json $c.Layout
  $cfg = Get-Cfg $Raiz
  $modelo = Join-Path (Split-Path $PSScriptRoot -Parent) 'reference\LEIAME-modelo.md'
  $txt = Get-Content $modelo -Raw -Encoding UTF8
  $hw = $lay.hardware
  $tabela = New-Object System.Collections.ArrayList
  $ultima = 0
  foreach ($l in ($lay.linhas | Sort-Object linha)) {
    if ($l.linha -gt ($ultima + 1)) { [void]$tabela.Add('') }
    $un = ''; if ($l.unidade) { $un = " (unidade: $($l.unidade))" }
    [void]$tabela.Add(("{0,-18} {1,-46} ({2})" -f $l.label, ($l.grupoNome + ' > ' + $l.leituraOrig + $un), (& { if ($l.grupoId -eq 'F00F5000') { 'RTSS' } elseif ($l.grupoNome -like 'PresentMon*') { 'PresentMon' } else { 'HWiNFO' } })))
    $ultima = $l.linha
  }
  if ($lay.pcTotal) { [void]$tabela.Add(''); [void]$tabela.Add(("{0,-18} {1}" -f $lay.pcTotal.label, "sensor customizado, formula abaixo (estimativa)")) }
  $formula = 'nao criado nesta maquina: ' + $lay.pcTotalMotivo
  if ($lay.pcTotal) { $formula = $lay.pcTotal.formula + "   (constante fixa " + $lay.pcTotal.constante + " W para o resto da maquina, eficiencia da fonte " + $lay.pcTotal.eficiencia + ", perfil " + $lay.pcTotal.perfil + ")" }
  $versoes = 'nao registradas (rode instalar, ou veja status)'
  if ($cfg.versoes) { $versoes = ("HWiNFO {0}, RTSS {1}, CapFrameX {2}" -f $cfg.versoes.hwinfo, $cfg.versoes.rtss, $cfg.versoes.capframex); if ($cfg.versoes.presentmon) { $versoes += ", Intel PresentMon $($cfg.versoes.presentmon)" } }
  elseif (Test-Path $c.HwinfoExe) { $versoes = ("HWiNFO {0}, RTSS {1}, CapFrameX {2}" -f (Get-VersaoExe $c.HwinfoExe), (Get-VersaoExe $c.RtssExe), (Get-VersaoExe $c.CapExe)) }
  $discos = ($hw.discos -join '; ')
  $notaNotebook = ''
  if ($hw.notebook) { $notaNotebook = "Esta maquina e um notebook: a tarefa agendada sobe tambem na bateria, o bloco de GPU e o da placa dedicada, e a formula do PC total so vale na tomada (na bateria, a taxa de descarga do HWiNFO e o consumo real)." }
  $map = @{ '{RAIZ}' = $c.Raiz; '{DATA}' = (Get-Date -Format 'dd/MM/yyyy'); '{MAQUINA}' = $lay.maquina; '{CPU}' = $hw.cpu; '{CPU_CURTO}' = $hw.cpuCurto; '{GPU}' = $hw.gpu; '{GPU_CURTO}' = $hw.gpuCurto
            '{VRAM_MB}' = [string]$hw.vramMB; '{RAM_MB}' = [string]$hw.ramMB; '{RAM_GB}' = [string]$hw.ramGB; '{CPU_LIMITE_W}' = [string]$hw.cpuLimiteW; '{GPU_LIMITE_W}' = [string]$hw.gpuLimiteW
            '{DISCOS}' = $discos; '{VERSOES}' = $versoes; '{TABELA_LINHAS}' = ($tabela -join "`n"); '{FORMULA_PC_TOTAL}' = $formula; '{NOTA_NOTEBOOK}' = $notaNotebook }
  foreach ($k in $map.Keys) { $txt = $txt.Replace($k, [string]$map[$k]) }
  if (Test-Path $c.Leiame) { $bk = Join-Path $c.Backup ("LEIAME-{0}.md" -f (Get-Date -Format 'yyyyMMdd-HHmmss')); Copy-Item $c.Leiame $bk -Force; Say "LEIAME anterior guardado em $bk" }
  Set-Content -Path $c.Leiame -Value $txt -Encoding UTF8
  Say "gravado: $($c.Leiame) (revise e complete com o que so esta maquina tem)"
}

function Acao-Tudo {
  Titulo "TUDO ($Raiz)"
  Acao-Baixar
  Acao-Instalar
  Acao-Configurar
  Acao-Tarefa
  Acao-Enumerar
  Acao-Mapear
  Acao-Aplicar
  $script:TesteCubo = (-not $SemCubo -and (Test-Path $c.Cubo))
  Acao-Verificar
  Acao-Leiame
  if (-not $ManterInstaladores -and (Test-Path $c.Installers)) { Remove-Item $c.Installers -Recurse -Force -ErrorAction SilentlyContinue; Say "instaladores apagados ($($c.Installers))" }
  Say ""
  Say "PRONTO. Proximos passos: revisar $($c.Layout) (linhas nao mapeadas / confianca media), ajustar e rodar 'aplicar'; revisar $($c.Leiame); reiniciar o Windows e conferir 'status'."
}

function Acao-Desinstalar {
  Titulo "DESINSTALAR"
  try { Unregister-ScheduledTask -TaskName $script:GO_TAREFA -Confirm:$false -ErrorAction Stop; Say "tarefa removida" } catch { Say "tarefa nao existia" }
  Stop-Monitoramento
  $un = Join-Path $c.HwinfoDir 'unins000.exe'
  if (Test-Path $un) { Say "desinstalando HWiNFO"; Start-Process -FilePath $un -ArgumentList '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES' -Wait | Out-Null }
  $unR = Join-Path $c.RtssDir 'Uninstall.exe'
  if (Test-Path $unR) { Say "desinstalando RTSS (NSIS: o desinstalador se copia para o TEMP e volta na hora)"; Start-Process -FilePath $unR -ArgumentList '/S' -Wait | Out-Null; Start-Sleep -Seconds 10 }
  foreach ($k in @(Get-ChildItem 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall' -ErrorAction SilentlyContinue)) {
    $p = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
    if ($p.DisplayName -like '*PresentMon*' -and $k.PSChildName -match '^\{[0-9A-F-]+\}$') { Say "desinstalando Intel PresentMon ($($p.DisplayName))"; Start-Process msiexec.exe -ArgumentList "/x $($k.PSChildName) /qn /norestart" -Wait | Out-Null }
  }
  Remove-RtssDoRun $c
  if ($ApagarRegistro -and (Test-Path 'HKCU:\Software\HWiNFO64')) { Backup-RegistroHwinfo $c | Out-Null; Remove-Item 'HKCU:\Software\HWiNFO64' -Recurse -Force; Say "HKCU\Software\HWiNFO64 removido (backup em $($c.Backup))" }
  if ($ApagarPasta -and (Test-Path $c.Raiz)) { Remove-Item $c.Raiz -Recurse -Force -ErrorAction SilentlyContinue; Say "pasta $($c.Raiz) removida" }
  else { Say "pasta $($c.Raiz) mantida (use -ApagarPasta para remover)" }
}

# ------------------------------------------------------------------ dispatch
$script:GO_EXIT = 0
try {
  switch ($Acao) {
    'ajuda'       { Acao-Ajuda }
    'status'      { Acao-Status }
    'baixar'      { Acao-Baixar }
    'instalar'    { Acao-Instalar }
    'configurar'  { Acao-Configurar }
    'tarefa'      { Acao-Tarefa }
    'enumerar'    { Acao-Enumerar }
    'mapear'      { Acao-Mapear }
    'aplicar'     { Acao-Aplicar }
    'iniciar'     { Acao-Iniciar }
    'verificar'   { Acao-Verificar }
    'leiame'      { Acao-Leiame }
    'tudo'        { Acao-Tudo }
    'desinstalar' { Acao-Desinstalar }
  }
} catch {
  Say ("ERRO FATAL em '{0}': {1}" -f $Acao, $_.Exception.Message)
  if ($_.InvocationInfo -and $_.InvocationInfo.PositionMessage) { Say ($_.InvocationInfo.PositionMessage -replace "`r?`n", ' ') }
  $script:GO_EXIT = 1
}
exit $script:GO_EXIT
