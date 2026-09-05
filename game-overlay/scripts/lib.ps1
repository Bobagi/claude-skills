# lib.ps1 - funcoes compartilhadas da skill game-overlay (HWiNFO + RTSS).
# Carregado por dot-source pelo overlay.ps1. Nao rode direto.
#
# Regras deste arquivo:
#  - ASCII puro (o PowerShell 5.1 le .ps1 sem BOM como ANSI e acento vira lixo).
#  - Compativel com Windows PowerShell 5.1 (sem ternario, sem ??, sem pwsh-only).
#  - Nunca New-Item -Force em chave de registro existente (apaga os valores).

$script:GO_TAREFA = 'HWiNFO64 (monitoramento)'
$script:GO_UA     = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
$script:GO_PROCS  = @('HWiNFO64','HWiNFO32','RTSS','RTSSHooksLoader','RTSSHooksLoader64','EncoderServer','EncoderServer64',
                      'DesktopOverlayHost','DesktopOverlayHost64','DesktopOverlayHostLoader','CapFrameX','vkcube')
$script:GO_TIPOS  = @{ 1='Temp'; 2='Volt'; 3='Fan'; 4='Current'; 5='Power'; 6='Clock'; 7='Usage'; 8='Other' }
$script:GO_LOG    = $null
$script:GO_RTSS_ZIP_DIRETO = 'https://ftp.nluug.nl/pub/games/PC/guru3d/afterburner/[Guru3D]-RTSSSetup737Build28314.zip'
$script:GO_HWINFO_PAGINA   = 'https://www.hwinfo.com/download/'

# ---------------------------------------------------------------- log / erro
function Say([string]$m) {
  $l = "{0}  {1}" -f (Get-Date -Format 'HH:mm:ss'), $m
  Write-Host $l
  if ($script:GO_LOG) { Add-Content -Path $script:GO_LOG -Value $l -Encoding UTF8 }
}
function Warn([string]$m) { Say ("AVISO: " + $m) }
function Fail([string]$m) { Say ("ERRO: " + $m); throw $m }
function Titulo([string]$m) { Say ""; Say ("===== " + $m + " =====") }

function Test-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  return ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ---------------------------------------------------------------- raiz / config
function Get-RaizPadrao {
  if ($env:GAME_OVERLAY_RAIZ) { return $env:GAME_OVERLAY_RAIZ }
  foreach ($c in @('D:\Tools\Monitoring','C:\Tools\Monitoring')) {
    if (Test-Path (Join-Path $c '_Config\overlay.json')) { return $c }
    if ((Test-Path (Join-Path $c 'RTSS\RTSS.exe')) -and (Test-Path (Join-Path $c 'HWiNFO\HWiNFO64.EXE'))) { return $c }
  }
  try {
    $t = Get-ScheduledTask -TaskName $script:GO_TAREFA -ErrorAction Stop
    $arg = [string]$t.Actions[0].Arguments
    if ($arg -match '([A-Za-z]:\\[^"]*?)\\_Config\\iniciar-monitoramento\.ps1') { return $Matches[1] }
  } catch { }
  $d = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'" -ErrorAction SilentlyContinue
  if ($d -and $d.DriveType -eq 3 -and $d.FreeSpace -gt 2GB) { return 'D:\Tools\Monitoring' }
  return 'C:\Tools\Monitoring'
}

function Get-Caminhos([string]$Raiz) {
  return [pscustomobject]@{
    Raiz        = $Raiz
    Config      = (Join-Path $Raiz '_Config')
    Installers  = (Join-Path $Raiz '_Config\installers')
    Jobs        = (Join-Path $Raiz '_Config\jobs')
    Backup      = (Join-Path $Raiz '_Config\backup')
    Capturas    = (Join-Path $Raiz '_Capturas')
    HwinfoDir   = (Join-Path $Raiz 'HWiNFO')
    HwinfoExe   = (Join-Path $Raiz 'HWiNFO\HWiNFO64.EXE')
    HwinfoIni   = (Join-Path $Raiz 'HWiNFO\HWiNFO64.INI')
    RtssDir     = (Join-Path $Raiz 'RTSS')
    RtssExe     = (Join-Path $Raiz 'RTSS\RTSS.exe')
    RtssGlobal  = (Join-Path $Raiz 'RTSS\Profiles\Global')
    RtssConfig  = (Join-Path $Raiz 'RTSS\Profiles\Config')
    CapDir      = (Join-Path $Raiz 'CapFrameX')
    CapExe      = (Join-Path $Raiz 'CapFrameX\CapFrameX.exe')
    Cubo        = (Join-Path $Raiz 'CapFrameX\3d-test-app\vkcube.exe')
    PmDir       = (Join-Path $Raiz 'PresentMon')
    Launcher    = (Join-Path $Raiz '_Config\iniciar-monitoramento.ps1')
    Runner      = (Join-Path $Raiz '_Config\runner.ps1')
    InicioLog   = (Join-Path $Raiz '_Config\inicio.log')
    Sensores    = (Join-Path $Raiz '_Config\sensores.json')
    SensoresTxt = (Join-Path $Raiz '_Config\sensores.txt')
    Layout      = (Join-Path $Raiz '_Config\layout.json')
    Cfg         = (Join-Path $Raiz '_Config\overlay.json')
    Leiame      = (Join-Path $Raiz 'LEIAME.md')
  }
}

function Get-Cfg([string]$Raiz) {
  $p = Join-Path $Raiz '_Config\overlay.json'
  if (Test-Path $p) { try { return (Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { } }
  return [pscustomobject]@{}
}
function Set-CfgProp($cfg, [string]$nome, $valor) {
  if ($cfg.PSObject.Properties[$nome]) { $cfg.$nome = $valor }
  else { $cfg | Add-Member -NotePropertyName $nome -NotePropertyValue $valor }
}
function Save-Cfg([string]$Raiz, $cfg) {
  $dir = Join-Path $Raiz '_Config'
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Set-CfgProp $cfg 'raiz' $Raiz
  Set-CfgProp $cfg 'atualizadoEm' (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
  ($cfg | ConvertTo-Json -Depth 8) | Set-Content -Path (Join-Path $dir 'overlay.json') -Encoding UTF8
}

function Get-VersaoExe([string]$Path) {
  if (-not (Test-Path $Path)) { return $null }
  $vi = (Get-Item $Path).VersionInfo
  if ($vi.ProductVersion) { return ([string]$vi.ProductVersion).Trim() }
  return ([string]$vi.FileVersion).Trim()
}

# ---------------------------------------------------------------- processos
function Test-Rodando([string]$Nome) { return [bool](Get-Process -Name $Nome -ErrorAction SilentlyContinue) }

function Stop-Monitoramento([string[]]$Nomes) {
  if (-not $Nomes) { $Nomes = $script:GO_PROCS }
  # o RTSS fecha bem por WM_CLOSE; o HWiNFO a gente mata (ele regravaria o registro ao sair,
  # e e justamente isso que queremos evitar antes de escrever a configuracao)
  Get-Process -Name RTSS -ErrorAction SilentlyContinue | ForEach-Object { try { $_.CloseMainWindow() | Out-Null } catch { } }
  Start-Sleep -Seconds 2
  foreach ($n in $Nomes) {
    Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
      try { Stop-Process -Id $_.Id -Force -ErrorAction Stop; Say "encerrado: $n (pid $($_.Id))" }
      catch { Warn "nao consegui encerrar $n (pid $($_.Id)): $($_.Exception.Message)" }
    }
  }
  Start-Sleep -Seconds 2
}

function Start-Rtss($c) {
  if (Test-Rodando 'RTSS') { Say 'RTSS ja estava rodando'; return }
  if (-not (Test-Path $c.RtssExe)) { Fail "RTSS nao encontrado em $($c.RtssExe)" }
  # Sempre Start-Process: 'cmd /c start | Out-Null' trava o script porque o RTSS herda o handle de saida.
  Start-Process -FilePath $c.RtssExe -WorkingDirectory $c.RtssDir
  Say 'RTSS lancado'
}
function Start-Hwinfo($c) {
  if (Test-Rodando 'HWiNFO64') { Say 'HWiNFO ja estava rodando'; return }
  if (-not (Test-Path $c.HwinfoExe)) { Fail "HWiNFO nao encontrado em $($c.HwinfoExe)" }
  Start-Process -FilePath $c.HwinfoExe -WorkingDirectory $c.HwinfoDir
  Say 'HWiNFO lancado'
}

function Open-MMF([string]$Nome) {
  try {
    $m = [System.IO.MemoryMappedFiles.MemoryMappedFile]::OpenExisting($Nome, [System.IO.MemoryMappedFiles.MemoryMappedFileRights]::Read)
    return $m
  } catch { return $null }
}
function Wait-RtssSM([int]$Seg = 90) {
  $t = Get-Date
  while (((Get-Date) - $t).TotalSeconds -lt $Seg) {
    $m = Open-MMF 'RTSSSharedMemoryV2'
    if ($m) { $m.Dispose(); return $true }
    Start-Sleep -Milliseconds 500
  }
  return $false
}
function Test-HwinfoSM {
  $m = Open-MMF 'Global\HWiNFO_SENS_SM2'
  if ($m) { $m.Dispose(); return $true }
  return $false
}
function Wait-HwinfoSM([int]$Seg = 120) {
  $t = Get-Date
  while (((Get-Date) - $t).TotalSeconds -lt $Seg) {
    $m = Open-MMF 'Global\HWiNFO_SENS_SM2'
    if ($m) { $m.Dispose(); return $true }
    Start-Sleep -Seconds 2
  }
  return $false
}
function Start-NaOrdem($c) {
  # RTSS primeiro, HWiNFO depois: o HWiNFO enumera o grupo [RTSS] (FPS/Frametime) so ao iniciar.
  Start-Rtss $c
  $ok = Wait-RtssSM 90
  Say "memoria compartilhada do RTSS pronta=$ok"
  Start-Hwinfo $c
}

# ---------------------------------------------------------------- memoria compartilhada
function Read-Str($acc, [long]$Pos, [int]$Len, [bool]$Utf8) {
  $b = New-Object byte[] $Len
  $acc.ReadArray($Pos, $b, 0, $Len) | Out-Null
  if ($Utf8) { $s = [Text.Encoding]::UTF8.GetString($b) } else { $s = [Text.Encoding]::Default.GetString($b) }
  $i = $s.IndexOf([char]0)
  if ($i -ge 0) { $s = $s.Substring(0, $i) }
  return $s
}

# Le o OSD do RTSS: lista de slots com dono e texto. Cabecalho: dwOSDEntrySize em 20,
# dwOSDArrOffset em 24, dwOSDArrSize em 28; entrada: szOSD[256], szOSDOwner[256], szOSDEx[4096].
function Read-RtssOsd {
  $m = Open-MMF 'RTSSSharedMemoryV2'
  if (-not $m) { return $null }
  $a = $m.CreateViewAccessor(0, 0, [System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read)
  $r = @()
  try {
    $tam = $a.ReadUInt32(20); $off = $a.ReadUInt32(24); $n = $a.ReadUInt32(28)
    for ($i = 0; $i -lt $n; $i++) {
      $base = $off + [long]$i * $tam
      $dono = Read-Str $a ($base + 256) 256 $false
      if (-not $dono) { continue }
      $t1 = Read-Str $a $base 256 $false
      $t2 = Read-Str $a ($base + 512) 4096 $false
      $txt = ($t1 + "`n" + $t2) -replace '<OBJ=[0-9A-Fa-f]+>', ''
      $r += [pscustomobject]@{ Slot = $i; Dono = $dono; Texto = $txt.Trim() }
    }
  } finally { $a.Dispose(); $m.Dispose() }
  return $r
}
function Get-OsdHwinfo {
  $slots = Read-RtssOsd
  if (-not $slots) { return $null }
  $s = $slots | Where-Object { $_.Dono -like 'HWiNFO*' } | Select-Object -First 1
  if ($s) { return $s.Texto }
  return $null
}
function Test-OsdTemFps {
  $t = Get-OsdHwinfo
  if (-not $t) { return $false }
  return [bool]($t -match '(?m)^FPS:')
}
# Aplicativos que o RTSS enganchou (pid, exe, FPS calculado da janela de contagem).
function Read-RtssApps {
  $m = Open-MMF 'RTSSSharedMemoryV2'
  if (-not $m) { return @() }
  $a = $m.CreateViewAccessor(0, 0, [System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read)
  $r = @()
  try {
    $sz = $a.ReadUInt32(8); $off = $a.ReadUInt32(12); $n = $a.ReadUInt32(16)
    for ($i = 0; $i -lt $n; $i++) {
      $p = $off + [long]$i * $sz
      $pidv = $a.ReadUInt32($p)
      if ($pidv -eq 0) { continue }
      $nome = Read-Str $a ($p + 4) 260 $false
      $t0 = $a.ReadUInt32($p + 268); $t1 = $a.ReadUInt32($p + 272); $fr = $a.ReadUInt32($p + 276)
      $fps = 0
      if ($t1 -gt $t0) { $fps = [math]::Round($fr * 1000.0 / ($t1 - $t0), 1) }
      # dwOSDFrame (332) avanca a cada quadro em que o RTSS DESENHOU o OSD dentro do app; 0 = so contou quadros
      $r += [pscustomobject]@{ Pid = $pidv; Exe = $nome; Fps = $fps; OsdFrame = $a.ReadUInt32($p + 332) }
    }
  } finally { $a.Dispose(); $m.Dispose() }
  return $r
}

# Le todos os sensores do HWiNFO (Global\HWiNFO_SENS_SM2). Precisa de SensorsSM=1 no INI.
# Cabecalho: offset da secao de grupos em 20, tamanho do elemento em 24, quantidade em 28;
# leituras em 32/36/40; dwPollingPeriod em 44.
# Grupo: dwSensorID(0) dwSensorInst(4) szNameOrig[128](8) szNameUser[128](136) [+utf8 em 264/392]
# Leitura: tReading(0) dwSensorIndex(4) dwReadingID(8) szLabelOrig[128](12) szLabelUser[128](140)
#          szUnit[16](268) Value(284) Min(292) Max(300) Avg(308) [+utf8 orig/user/unit em 316/444/572]
function Read-HwinfoSensores {
  $m = Open-MMF 'Global\HWiNFO_SENS_SM2'
  if (-not $m) { return $null }
  $a = $m.CreateViewAccessor(0, 0, [System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read)
  try {
    $offS = $a.ReadUInt32(20); $szS = $a.ReadUInt32(24); $nS = $a.ReadUInt32(28)
    $offR = $a.ReadUInt32(32); $szR = $a.ReadUInt32(36); $nR = $a.ReadUInt32(40)
    $poll = $a.ReadUInt32(44)
    $grupos = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $nS; $i++) {
      $p = $offS + [long]$i * $szS
      $orig = Read-Str $a ($p + 8) 128 $false
      $user = Read-Str $a ($p + 136) 128 $false
      if ($szS -ge 520) {
        $u1 = Read-Str $a ($p + 264) 128 $true; $u2 = Read-Str $a ($p + 392) 128 $true
        if ($u1) { $orig = $u1 }; if ($u2) { $user = $u2 }
      }
      [void]$grupos.Add([pscustomobject]@{
        idx = $i; id = ("{0:X8}" -f $a.ReadUInt32($p)); inst = [int]$a.ReadUInt32($p + 4)
        nomeOrig = $orig; nomeUser = $user })
    }
    $leituras = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $nR; $i++) {
      $p = $offR + [long]$i * $szR
      $tipo = [int]$a.ReadUInt32($p); $gi = [int]$a.ReadUInt32($p + 4); $id = $a.ReadUInt32($p + 8)
      $lo = Read-Str $a ($p + 12) 128 $false
      $lu = Read-Str $a ($p + 140) 128 $false
      $un = Read-Str $a ($p + 268) 16 $false
      if ($szR -ge 588) {
        $x1 = Read-Str $a ($p + 316) 128 $true; $x2 = Read-Str $a ($p + 444) 128 $true; $x3 = Read-Str $a ($p + 572) 16 $true
        if ($x1) { $lo = $x1 }; if ($x2) { $lu = $x2 }; if ($x3) { $un = $x3 }
      }
      $tn = $script:GO_TIPOS[$tipo]; if (-not $tn) { $tn = "Tipo$tipo" }
      [void]$leituras.Add([pscustomobject]@{
        ordem = $i; grupoIdx = $gi; tipo = $tipo; tipoNome = $tn
        id = ("{0:X8}" -f $id); idx = [int]($id -band 0x00FFFFFF)
        labelOrig = $lo; labelUser = $lu; unidade = $un; valor = $a.ReadDouble($p + 284) })
    }
    return [pscustomobject]@{ lidoEm = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); polling = $poll
                              grupos = @($grupos); leituras = @($leituras) }
  } finally { $a.Dispose(); $m.Dispose() }
}
function Test-GrupoRtss($sens) {
  if (-not $sens) { return $false }
  return [bool]($sens.grupos | Where-Object { $_.id -eq 'F00F5000' -or $_.nomeOrig -eq 'RTSS' })
}
function Write-SensoresTxt($sens, [string]$Path) {
  $l = New-Object System.Collections.ArrayList
  [void]$l.Add("# sensores do HWiNFO lidos da memoria compartilhada em $($sens.lidoEm) (polling $($sens.polling) ms)")
  [void]$l.Add("# formato: [grupo] ID_inst  nome original | nome exibido")
  [void]$l.Add("#          tipo idx  rotulo original | rotulo exibido | unidade | valor")
  [void]$l.Add("# chave de registro de uma leitura: HKCU\Software\HWiNFO64\Sensors\<ID_inst>\<tipo><idx>")
  foreach ($g in $sens.grupos) {
    [void]$l.Add("")
    [void]$l.Add(("[{0}] {1}_{2}  {3} | {4}" -f $g.idx, $g.id, $g.inst, $g.nomeOrig, $g.nomeUser))
    foreach ($r in ($sens.leituras | Where-Object { $_.grupoIdx -eq $g.idx })) {
      [void]$l.Add(("    {0,-7} {1,-5} {2} | {3} | {4} | {5}" -f $r.tipoNome, $r.idx, $r.labelOrig, $r.labelUser, $r.unidade, ("{0:N3}" -f $r.valor)))
    }
  }
  Set-Content -Path $Path -Value ($l -join "`r`n") -Encoding UTF8
}

# ---------------------------------------------------------------- INI (RTSS e HWiNFO)
function Read-Ini([string]$Path) {
  $secoes = New-Object System.Collections.ArrayList
  $atual = $null
  if (Test-Path $Path) {
    foreach ($l in @(Get-Content $Path -Encoding Default)) {
      if ($l -match '^\s*\[(.+?)\]\s*$') {
        $atual = [pscustomobject]@{ Nome = $Matches[1]; Linhas = (New-Object System.Collections.ArrayList) }
        [void]$secoes.Add($atual)
      } else {
        if (-not $atual) { $atual = [pscustomobject]@{ Nome = ''; Linhas = (New-Object System.Collections.ArrayList) }; [void]$secoes.Add($atual) }
        [void]$atual.Linhas.Add($l)
      }
    }
  }
  return $secoes   # o PowerShell desenrola (0 itens -> nada, 1 item -> o objeto): quem chama usa @(Read-Ini ...)
}
function Write-Ini([string]$Path, $Secoes) {
  $out = New-Object System.Collections.ArrayList
  foreach ($s in $Secoes) {
    if ($s.Nome -ne '') { [void]$out.Add("[$($s.Nome)]") }
    foreach ($l in $s.Linhas) { [void]$out.Add($l) }
  }
  $dir = Split-Path $Path -Parent
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Set-Content -Path $Path -Value ($out -join "`r`n") -Encoding Ascii
}
# Define chaves numa secao preservando o resto do arquivo. $Valores deve ser [ordered]@{}.
function Set-IniKeys([string]$Path, [string]$Secao, [System.Collections.IDictionary]$Valores) {
  $secoes = New-Object System.Collections.ArrayList
  foreach ($x in @(Read-Ini $Path)) { if ($x) { [void]$secoes.Add($x) } }
  $s = $secoes | Where-Object { $_.Nome -eq $Secao } | Select-Object -First 1
  if (-not $s) { $s = [pscustomobject]@{ Nome = $Secao; Linhas = (New-Object System.Collections.ArrayList) }; [void]$secoes.Add($s) }
  foreach ($k in $Valores.Keys) {
    $achou = $false
    for ($i = 0; $i -lt $s.Linhas.Count; $i++) {
      if ($s.Linhas[$i] -match ('^\s*' + [regex]::Escape($k) + '\s*=')) { $s.Linhas[$i] = "$k=$($Valores[$k])"; $achou = $true; break }
    }
    if (-not $achou) { [void]$s.Linhas.Add("$k=$($Valores[$k])") }
  }
  Write-Ini $Path $secoes
}
function Get-IniValue([string]$Path, [string]$Secao, [string]$Chave) {
  $s = @(Read-Ini $Path) | Where-Object { $_ -and $_.Nome -eq $Secao } | Select-Object -First 1
  if (-not $s) { return $null }
  foreach ($l in $s.Linhas) { if ($l -match ('^\s*' + [regex]::Escape($Chave) + '\s*=\s*(.*)$')) { return $Matches[1].Trim() } }
  return $null
}

# ---------------------------------------------------------------- registro
function Ensure-RegKey([string]$Path) {
  # cria a cadeia de chaves; NUNCA New-Item -Force em chave que ja existe (recria e apaga os valores)
  if (Test-Path $Path) { return }
  $pai = Split-Path $Path -Parent
  if ($pai -and -not (Test-Path $pai)) { Ensure-RegKey $pai }
  New-Item -Path $Path | Out-Null
}
# $Valores: [ordered]@{ Nome = valor }; string -> REG_SZ, numero -> REG_DWORD, $null -> remove o valor.
function Set-RegValues([string]$Path, [System.Collections.IDictionary]$Valores) {
  Ensure-RegKey $Path
  foreach ($k in $Valores.Keys) {
    $v = $Valores[$k]
    if ($null -eq $v) { Remove-ItemProperty -Path $Path -Name $k -ErrorAction SilentlyContinue; continue }
    if ($v -is [string]) { New-ItemProperty -Path $Path -Name $k -Value $v -PropertyType String -Force | Out-Null }
    else { New-ItemProperty -Path $Path -Name $k -Value ([int]$v) -PropertyType DWord -Force | Out-Null }
  }
}
function Backup-RegistroHwinfo($c) {
  if (-not (Test-Path $c.Backup)) { New-Item -ItemType Directory -Path $c.Backup -Force | Out-Null }
  $f = Join-Path $c.Backup ("hwinfo-registro-{0}.reg" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
  if (Test-Path 'HKCU:\Software\HWiNFO64') {
    & reg.exe export 'HKCU\Software\HWiNFO64' $f /y | Out-Null
    Say "backup do registro do HWiNFO: $f"
  }
  return $f
}

# ---------------------------------------------------------------- hardware
function Get-CpuNomeCurto([string]$n) {
  $s = $n
  $s = $s -replace '\(R\)|\(TM\)|\(tm\)|\(r\)', ''
  $s = $s -replace '\d+(st|nd|rd|th) Gen', ''
  $s = $s -replace 'Intel Core|Intel|AMD|Processor|CPU|with Radeon Graphics|w/ Radeon.*$|\d+-Core|@.*$', ''
  $s = ($s -replace '\s+', ' ').Trim()
  if (-not $s) { $s = $n }
  return $s
}
function Get-GpuNomeCurto([string]$n) {
  $s = $n
  $s = $s -replace 'NVIDIA GeForce|NVIDIA|AMD Radeon|AMD|Intel\(R\)|Intel|\(R\)|\(TM\)', ''
  $s = $s -replace 'Laptop GPU', 'Laptop'
  $s = ($s -replace '\s+', ' ').Trim()
  if (-not $s) { $s = $n }
  return $s
}
function Get-Hardware {
  $cpu = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1).Name
  $gpus = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | Where-Object { $_.Name })
  $ded = $gpus | Where-Object { $_.Name -match 'GeForce|RTX|GTX|Radeon RX|Radeon Pro|Arc\s?[AB]\d' -and
                                $_.Name -notmatch 'UHD|Iris|Radeon\(TM\) Graphics|Radeon Graphics$|Vega \d' } | Select-Object -First 1
  if (-not $ded) { $ded = $gpus | Select-Object -First 1 }
  $gpuNome = $null; if ($ded) { $gpuNome = $ded.Name }
  # VRAM: Win32_VideoController.AdapterRAM estoura em 4 GB; o registro guarda o valor real (QWORD)
  $vram = $null
  $classe = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
  foreach ($k in @(Get-ChildItem $classe -ErrorAction SilentlyContinue)) {
    $p = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
    if ($p -and $p.DriverDesc -eq $gpuNome -and $p.'HardwareInformation.qwMemorySize') { $vram = [math]::Round($p.'HardwareInformation.qwMemorySize' / 1MB); break }
  }
  $gpuLim = $null
  if (-not $vram -or $gpuNome -match 'NVIDIA|GeForce') {
    try {
      $smi = & nvidia-smi --query-gpu=memory.total,power.default_limit --format=csv,noheader,nounits 2>$null
      if ($smi) { $parts = ([string]$smi[0]).Split(','); if (-not $vram) { $vram = [int]$parts[0].Trim() }; $gpuLim = [int][double]$parts[1].Trim() }
    } catch { }
  }
  if (-not $vram -and $ded -and $ded.AdapterRAM -and $ded.AdapterRAM -lt 4GB) { $vram = [math]::Round($ded.AdapterRAM / 1MB) }
  $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
  $ramMB = $null; if ($os) { $ramMB = [math]::Round($os.TotalVisibleMemorySize / 1024) }
  $fis = (Get-CimInstance Win32_PhysicalMemory -ErrorAction SilentlyContinue | Measure-Object Capacity -Sum).Sum
  $ramGB = $null
  if ($fis) { $ramGB = [math]::Round($fis / 1GB) } elseif ($ramMB) { $ramGB = [math]::Round($ramMB / 1024) }
  # discos: letra, modelo, tipo (NVMe / SSD / HDD)
  $discos = @()
  try {
    $fisicos = @(Get-PhysicalDisk -ErrorAction Stop)
    $letras = @{}
    foreach ($part in @(Get-Partition -ErrorAction SilentlyContinue | Where-Object { $_.DriveLetter })) {
      if (-not $letras.ContainsKey([string]$part.DiskNumber)) { $letras[[string]$part.DiskNumber] = @() }
      $letras[[string]$part.DiskNumber] += [string]$part.DriveLetter
    }
    foreach ($d in $fisicos) {
      $tipo = ''
      if ($d.BusType -eq 'NVMe') { $tipo = 'NVMe' } elseif ($d.MediaType -eq 'SSD') { $tipo = 'SSD' } elseif ($d.MediaType -eq 'HDD') { $tipo = 'HDD' }
      $ls = @(); if ($letras.ContainsKey([string]$d.DeviceId)) { $ls = $letras[[string]$d.DeviceId] | Sort-Object }
      $discos += [pscustomobject]@{ Numero = [int]$d.DeviceId; Modelo = ([string]$d.FriendlyName).Trim(); Tipo = $tipo; Letras = @($ls); TamanhoGB = [math]::Round($d.Size / 1GB) }
    }
  } catch { Warn "Get-PhysicalDisk falhou: $($_.Exception.Message)" }
  $chassi = @((Get-CimInstance Win32_SystemEnclosure -ErrorAction SilentlyContinue).ChassisTypes)
  $bateria = (Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Measure-Object).Count
  $chassiPortatil = @($chassi | Where-Object { @(8,9,10,11,12,14,18,21,30,31,32) -contains $_ }).Count -gt 0
  $notebook = ($chassiPortatil -or ($bateria -gt 0))
  return [pscustomobject]@{
    Maquina = $env:COMPUTERNAME; Usuario = "$env:USERDOMAIN\$env:USERNAME"
    Cpu = $cpu; CpuCurto = (Get-CpuNomeCurto $cpu)
    Gpu = $gpuNome; GpuCurto = (Get-GpuNomeCurto $gpuNome); Gpus = @($gpus | ForEach-Object { $_.Name })
    VramMB = $vram; GpuLimiteW = $gpuLim
    RamMB = $ramMB; RamGB = $ramGB
    Discos = $discos; Notebook = $notebook
    Windows = (& { if ($os) { "$($os.Caption) $($os.Version)" } else { '' } })
  }
}

# ---------------------------------------------------------------- download
function Get-CurlExe {
  # o Windows 10 1803+ traz curl.exe em System32; hwinfo.com responde 403 ao Invoke-WebRequest
  # (mesmo com User-Agent de browser) e 200 ao curl, entao o curl e a primeira opcao.
  $c = Get-Command curl.exe -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  return $null
}
function Get-Arquivo([string]$Url, [string]$Destino, [string]$Tipo) {
  # $Tipo: exe | zip | msi (confere a assinatura do arquivo). Retorna $true/$false.
  $ProgressPreference = 'SilentlyContinue'
  try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
  Say "baixando $Url"
  Remove-Item $Destino -Force -ErrorAction SilentlyContinue
  $curl = Get-CurlExe
  $ok = $false
  if ($curl) {
    & $curl -sL --fail --max-time 900 -A $script:GO_UA -o $Destino $Url 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $Destino)) { $ok = $true } else { Warn "curl falhou (codigo $LASTEXITCODE) em $Url; tentando Invoke-WebRequest" }
  }
  if (-not $ok) {
    try { Invoke-WebRequest -Uri $Url -OutFile $Destino -UserAgent $script:GO_UA -UseBasicParsing -TimeoutSec 900 -ErrorAction Stop; $ok = $true }
    catch { Warn "download falhou: $($_.Exception.Message)" }
  }
  if (-not $ok) { Remove-Item $Destino -Force -ErrorAction SilentlyContinue; return $false }
  if (-not (Test-Path $Destino)) { return $false }
  $len = (Get-Item $Destino).Length
  if ($len -lt 1MB) { Warn "arquivo pequeno demais ($len bytes), provavelmente pagina de erro"; Remove-Item $Destino -Force; return $false }
  $fs = [IO.File]::OpenRead($Destino); $b = New-Object byte[] 2; $fs.Read($b, 0, 2) | Out-Null; $fs.Close()
  $ok = $true
  switch ($Tipo) {
    'exe' { $ok = ($b[0] -eq 0x4D -and $b[1] -eq 0x5A) }
    'zip' { $ok = ($b[0] -eq 0x50 -and $b[1] -eq 0x4B) }
    'msi' { $ok = ($b[0] -eq 0xD0 -and $b[1] -eq 0xCF) }
  }
  if (-not $ok) { Warn "assinatura do arquivo nao bate com $Tipo"; Remove-Item $Destino -Force; return $false }
  Unblock-File -Path $Destino -ErrorAction SilentlyContinue
  Say ("ok: {0} ({1:N1} MB)" -f (Split-Path $Destino -Leaf), ($len / 1MB))
  return $true
}
function Get-PaginaTexto([string]$Url) {
  $ProgressPreference = 'SilentlyContinue'
  try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
  $curl = Get-CurlExe
  if ($curl) {
    $s = & $curl -sL --fail --max-time 60 -A $script:GO_UA $Url 2>$null
    if ($LASTEXITCODE -eq 0 -and $s) { return (@($s) -join "`n") }
    Warn "curl nao leu $Url (codigo $LASTEXITCODE); tentando Invoke-WebRequest"
  }
  try { return (Invoke-WebRequest -Uri $Url -UserAgent $script:GO_UA -Headers @{ 'Accept' = 'text/html,*/*;q=0.8'; 'Accept-Language' = 'en-US,en;q=0.9' } -UseBasicParsing -TimeoutSec 60 -ErrorAction Stop).Content }
  catch { Warn "nao consegui ler $Url ($($_.Exception.Message))"; return $null }
}
function Test-UrlExiste([string]$Url) {
  try { $r = Invoke-WebRequest -Uri $Url -Method Head -UserAgent $script:GO_UA -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop; return ($r.StatusCode -eq 200) }
  catch { return $false }
}
function Find-HwinfoNoEspelho {
  # Ultimo recurso quando a pagina oficial nao abre: sonda o espelho sac.sk (hwi_NNNx.exe) numa
  # janela de versoes acima da que o winget conhece (o manifesto do winget fica para tras).
  $base = 850
  try { $v = (& winget show --id REALiX.HWiNFO --accept-source-agreements 2>$null | Select-String '^Version:\s*(\d+)\.(\d+)').Matches
        if ($v -and $v.Count -gt 0) { $base = [int]($v[0].Groups[1].Value + $v[0].Groups[2].Value.PadRight(2, '0').Substring(0, 2)) } } catch { }
  Say "sondando o espelho sac.sk a partir da versao $base (winget) para cima..."
  for ($v = $base + 30; $v -ge $base - 4; $v--) {
    $u = "https://www.sac.sk/download/utildiag/hwi_{0}x.exe" -f $v
    if (Test-UrlExiste $u) { Say "achado: $u"; return [pscustomobject]@{ Versao = $v; Url = $u } }
  }
  return $null
}
function Get-GithubUltimoAsset([string]$Repo, [string]$Padrao) {
  # Retorna @{ Tag; Nome; Url } do asset mais recente que casa com $Padrao (regex).
  try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
  try {
    $r = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ 'User-Agent' = 'game-overlay-skill'; 'Accept' = 'application/vnd.github+json' } -TimeoutSec 60 -ErrorAction Stop
    $a = @($r.assets | Where-Object { $_.name -match $Padrao }) | Select-Object -First 1
    if ($a) { return [pscustomobject]@{ Tag = $r.tag_name; Nome = $a.name; Url = $a.browser_download_url } }
    Warn "release $($r.tag_name) de $Repo nao tem asset que case com $Padrao"
  } catch { Warn "API do GitHub falhou para $Repo ($($_.Exception.Message)); tentando pelo redirect" }
  try {
    $resp = $null
    try { $resp = Invoke-WebRequest -Uri "https://github.com/$Repo/releases/latest" -MaximumRedirection 0 -UseBasicParsing -ErrorAction Stop } catch { $resp = $_.Exception.Response }
    $loc = $null
    if ($resp -and $resp.Headers -and $resp.Headers['Location']) { $loc = [string]$resp.Headers['Location'] }
    if ($loc -match '/tag/([^/]+)$') { return [pscustomobject]@{ Tag = $Matches[1]; Nome = $null; Url = $null } }
  } catch { }
  return $null
}

# ---------------------------------------------------------------- tarefa agendada / atalhos
function Register-TarefaMonitoramento($c) {
  $ps = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
  $usuario = "$env:USERDOMAIN\$env:USERNAME"
  $act = New-ScheduledTaskAction -Execute $ps -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $c.Launcher)
  $trg = New-ScheduledTaskTrigger -AtLogOn -User $usuario
  $trg.Delay = 'PT15S'
  $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) `
           -StartWhenAvailable -Hidden -MultipleInstances IgnoreNew -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1)
  $prc = New-ScheduledTaskPrincipal -UserId $usuario -LogonType Interactive -RunLevel Highest
  Register-ScheduledTask -TaskName $script:GO_TAREFA -Action $act -Trigger $trg -Settings $set -Principal $prc -Force | Out-Null
  Say "tarefa '$($script:GO_TAREFA)' registrada (logon de $usuario, +15 s, elevada, sobe na bateria)"
}
function Remove-RtssDoRun($c) {
  foreach ($hive in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run', 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run')) {
    $v = (Get-ItemProperty $hive -Name RTSS -ErrorAction SilentlyContinue).RTSS
    if ($v) {
      Add-Content -Path (Join-Path $c.Config 'run-rtss-removido.txt') -Value ("{0}  {1}  RTSS = {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm'), $hive, $v) -Encoding UTF8
      try { Remove-ItemProperty -Path $hive -Name RTSS -Force -ErrorAction Stop; Say "entrada Run 'RTSS' removida de $hive (pedia UAC todo logon)" }
      catch { Warn "nao consegui remover RTSS do Run em $hive : $($_.Exception.Message)" }
    }
  }
}
function New-Atalho([string]$Caminho, [string]$Alvo, [string]$Pasta) {
  if (-not (Test-Path $Alvo)) { return }
  $w = New-Object -ComObject WScript.Shell
  $s = $w.CreateShortcut($Caminho)
  $s.TargetPath = $Alvo; $s.WorkingDirectory = $Pasta
  $s.Save()
}

# ---------------------------------------------------------------- layout: mapear
function Expand-Marcadores([string]$s, [hashtable]$vars) {
  # troca {chave} pelo valor; se alguma chave nao tem valor, devolve $null (quem chama decide o fallback)
  if ($null -eq $s) { return $null }
  $ms = [regex]::Matches($s, '\{(\w+)\}')
  foreach ($m in $ms) {
    $k = $m.Groups[1].Value
    if (-not $vars.ContainsKey($k) -or $null -eq $vars[$k] -or [string]$vars[$k] -eq '') { return $null }
  }
  $out = $s
  foreach ($m in $ms) { $out = $out.Replace($m.Value, [string]$vars[$m.Groups[1].Value]) }
  return $out
}
function Resolve-Layout($padrao, $sens, $hw) {
  $grupos = @($sens.grupos); $leituras = @($sens.leituras)
  # 1) grupos candidatos por seletor (nome primeiro; ID conhecido so se nenhum nome casou)
  $sel = @{}
  foreach ($p in $padrao.grupos.PSObject.Properties) {
    $def = $p.Value; $porNome = @(); $porId = @()
    for ($i = 0; $i -lt $grupos.Count; $i++) {
      $g = $grupos[$i]
      foreach ($rx in @($def.nome)) { if ($g.nomeOrig -match $rx -or $g.nomeUser -match $rx) { $porNome += $i; break } }
      foreach ($id in @($def.id)) { if ($g.id -eq $id) { $porId += $i; break } }
    }
    $cands = $porNome; if ($cands.Count -eq 0) { $cands = $porId }
    if ($p.Name -eq 'gpu' -and $cands.Count -gt 1) {
      $ded = @($cands | Where-Object { $grupos[$_].nomeOrig -notmatch 'UHD|Iris|Radeon\(TM\) Graphics|Radeon Graphics$|Vega \d|Intel\(R\) (HD|Arc\(TM\)) Graphics' })
      $pref = @($ded | Where-Object { $grupos[$_].nomeOrig -match '^dGPU' })
      if ($pref.Count -gt 0) { $cands = $pref } elseif ($ded.Count -gt 0) { $cands = $ded }
    }
    $sel[$p.Name] = @($cands)
  }
  # 2) limites de potencia lidos do proprio HWiNFO
  $cpuLim = $null; $gpuLim = $hw.GpuLimiteW
  foreach ($r in $leituras) {
    if ($sel['cpu'] -contains $r.grupoIdx -and $r.tipo -eq 5 -and -not $cpuLim -and $r.labelOrig -match '^PL1 Power Limit|^Long Duration Power Limit|^CPU PPT Limit|^PPT Limit|^Package Power Limit') { if ($r.valor -gt 0) { $cpuLim = [math]::Round($r.valor) } }
    if ($sel['gpu'] -contains $r.grupoIdx -and $r.tipo -eq 5 -and $r.labelOrig -match '^GPU Power Limit \(rated\)$|^GPU Power Limit$') { if ($r.valor -gt 0) { $gpuLim = [math]::Round($r.valor) } }
  }
  $vars = @{ cpuNome = $hw.CpuCurto; gpuNome = $hw.GpuCurto; ramGB = $hw.RamGB; ramMB = $hw.RamMB; vramMB = $hw.VramMB; cpuLimiteW = $cpuLim; gpuLimiteW = $gpuLim }

  $linhas = New-Object System.Collections.ArrayList
  $nao = New-Object System.Collections.ArrayList
  $usadas = @{}
  function Find-Leitura($def, [int[]]$gIdx) {
    $tipo = [int]$def.tipo
    $pool = @($leituras | Where-Object { $gIdx -contains $_.grupoIdx -and $_.tipo -eq $tipo -and -not $usadas.ContainsKey($_.ordem) })
    foreach ($rx in @($def.leitura)) {
      $c = @($pool | Where-Object { $_.labelOrig -match $rx })
      if ($c.Count -eq 0) { $c = @($pool | Where-Object { $_.labelUser -match $rx }) }
      if ($c.Count -gt 0) {
        $best = $null; $hintOk = $false
        if ($null -ne $def.idHint) { $best = $c | Where-Object { $_.idx -eq [int]$def.idHint } | Select-Object -First 1; if ($best) { $hintOk = $true } }
        if (-not $best) { $best = $c[0] }
        return [pscustomobject]@{ Leitura = $best; Candidatos = $c.Count; HintOk = $hintOk; Regex = $rx }
      }
    }
    return $null
  }
  function Nova-Linha($def, $r, [int]$linha, [string]$label, [string]$unidade, [string]$mult, $conf, [int]$cands) {
    $g = $grupos[$r.grupoIdx]
    return [pscustomobject]@{
      linha = $linha; chave = [string]$def.chave; label = $label
      grupoId = $g.id; inst = $g.inst; grupoNome = $g.nomeOrig
      tipo = $r.tipo; tipoNome = $r.tipoNome; idx = $r.idx; leituraId = $r.id
      leituraOrig = $r.labelOrig; leituraExibida = $r.labelUser; unidadeAtual = $r.unidade; valorAtual = [math]::Round($r.valor, 2)
      unidade = $unidade; valueMult = $mult; grafico = $def.grafico
      confianca = $conf; candidatos = $cands }
  }
  $ultimaLinha = 0
  foreach ($def in @($padrao.linhas)) {
    $gIdx = @($sel[[string]$def.grupo])
    if ($gIdx.Count -eq 0) {
      [void]$nao.Add([pscustomobject]@{ chave = $def.chave; linha = $def.linha; motivo = "nenhum grupo de sensores casou com o seletor '$($def.grupo)'" })
      continue
    }
    if ($def.porDisco) {
      # uma linha por disco fisico, ordenada pela letra que o HWiNFO poe no nome do grupo: "Drive: MODELO (serial) [C:]"
      $ordem = @()
      foreach ($gi in $gIdx) {
        $g = $grupos[$gi]; $letra = $null
        if ($g.nomeOrig -match '\[([A-Za-z]):\]') { $letra = $Matches[1].ToUpper() }
        $tipo = ''; $modelo = ''
        foreach ($d in @($hw.Discos)) {
          if ($d.Modelo -and $g.nomeOrig -like "*$($d.Modelo)*") { $tipo = $d.Tipo; $modelo = $d.Modelo; if (-not $letra -and $d.Letras.Count -gt 0) { $letra = $d.Letras[0] }; break }
        }
        $chaveOrd = '~'; if ($letra) { $chaveOrd = $letra }
        $ordem += [pscustomobject]@{ gi = $gi; letra = $letra; tipo = $tipo; modelo = $modelo; ord = $chaveOrd }
      }
      $n = 0
      foreach ($o in ($ordem | Sort-Object ord, gi)) {
        $r = Find-Leitura $def @($o.gi)
        if (-not $r) { [void]$nao.Add([pscustomobject]@{ chave = "disco:$($grupos[$o.gi].nomeOrig)"; linha = 0; motivo = "grupo de disco sem leitura 'Total Activity'" }); continue }
        $lbl = $null
        if ($o.letra) { $lbl = ("Disco {0} {1}" -f $o.letra, $o.tipo).Trim() } else { $lbl = ("Disco {0}" -f $o.modelo).Trim() }
        $linha = [int]$def.linha + $n
        $l = Nova-Linha $def $r.Leitura $linha $lbl $null $null 'alta' $r.Candidatos
        [void]$linhas.Add($l); $usadas[$r.Leitura.ordem] = $true; $n++
        $ultimaLinha = $linha
      }
      continue
    }
    $r = Find-Leitura $def $gIdx
    if (-not $r) {
      $tn = $script:GO_TIPOS[[int]$def.tipo]
      $vistos = @($leituras | Where-Object { $gIdx -contains $_.grupoIdx -and $_.tipo -eq [int]$def.tipo } | ForEach-Object { $_.labelOrig } | Select-Object -Unique -First 12)
      [void]$nao.Add([pscustomobject]@{ chave = $def.chave; linha = $def.linha; motivo = "nenhuma leitura $tn casou com $(@($def.leitura) -join ' | ') no grupo '$($def.grupo)'"; candidatosDoTipo = $vistos })
      continue
    }
    $label = Expand-Marcadores ([string]$def.label) $vars
    if (-not $label) { $label = ([string]$def.label -replace '\{\w+\}', '').Trim() }
    $unid = $null; if ($def.unidade) { $unid = Expand-Marcadores ([string]$def.unidade) $vars }
    $mult = $null; if ($def.valueMult) { $mult = [string]$def.valueMult }
    $conf = 'alta'; if ($r.Candidatos -gt 1 -and -not $r.HintOk) { $conf = 'media' }
    $l = Nova-Linha $def $r.Leitura ([int]$def.linha) $label $unid $mult $conf $r.Candidatos
    [void]$linhas.Add($l); $usadas[$r.Leitura.ordem] = $true
    if ([int]$def.linha -gt $ultimaLinha) { $ultimaLinha = [int]$def.linha }
  }

  # 3) PC total: sensor customizado com formula (so quando existem leituras auxiliares sem ambiguidade)
  $aux = New-Object System.Collections.ArrayList
  $pcTotal = $null; $pcMotivo = $null
  $pt = $padrao.pcTotal
  if ($pt) {
    function Resolve-Apelidos($opcoes, [int[]]$gIdx) {
      foreach ($op in @($opcoes)) {
        $achados = @(); $ok = $true
        foreach ($p in $op.apelidos.PSObject.Properties) {
          $r = $null
          foreach ($rx in @($p.Value)) { $r = $leituras | Where-Object { $gIdx -contains $_.grupoIdx -and $_.tipo -eq 5 -and $_.labelOrig -match $rx } | Select-Object -First 1; if ($r) { break } }
          if ($r) { $achados += [pscustomobject]@{ apelido = $p.Name; leitura = $r } }
          elseif (-not ($op.opcionais -and (@($op.opcionais) -contains $p.Name))) { $ok = $false; break }
        }
        if ($ok -and $achados.Count -gt 0) { return $achados }
      }
      return $null
    }
    $auxCpu = @(Resolve-Apelidos $pt.cpu @($sel['cpu']) | Where-Object { $_ })
    $auxGpu = @(Resolve-Apelidos $pt.gpu @($sel['gpu']) | Where-Object { $_ })
    if ($auxCpu.Count -gt 0 -and $auxGpu.Count -gt 0) {
      $termos = @()
      foreach ($x in ($auxCpu + $auxGpu)) {
        $g = $grupos[$x.leitura.grupoIdx]
        [void]$aux.Add([pscustomobject]@{ apelido = $x.apelido; grupoId = $g.id; inst = $g.inst; tipoNome = $x.leitura.tipoNome; idx = $x.leitura.idx; leituraOrig = $x.leitura.labelOrig })
        $termos += ('"' + $x.apelido + '"')
      }
      $perfil = $pt.desktop; if ($hw.Notebook) { $perfil = $pt.notebook }
      $formula = ($termos -join ' + ') + (' + {0} / {1}' -f $perfil.constante, ([string]$perfil.eficiencia))
      $gid = [string]$pt.grupoId
      $gc = $grupos | Where-Object { $_.nomeOrig -eq [string]$pt.grupoCustom -or $_.nomeUser -eq [string]$pt.grupoCustom } | Select-Object -First 1
      if ($gc) { $gid = $gc.id }
      $pcTotal = [pscustomobject]@{ linha = ($ultimaLinha + [int]$pt.linhaAposDiscos); label = [string]$pt.label; unidade = [string]$pt.unidade
                                    grupoCustom = [string]$pt.grupoCustom; nome = [string]$pt.nome; grupoId = $gid; formula = $formula
                                    constante = $perfil.constante; eficiencia = $perfil.eficiencia; perfil = (& { if ($hw.Notebook) { 'notebook' } else { 'desktop' } }) }
    } else {
      $falta = @(); if ($auxCpu.Count -eq 0) { $falta += 'CPU' }; if ($auxGpu.Count -eq 0) { $falta += 'GPU' }
      $pcMotivo = "sem leituras auxiliares de potencia sem ambiguidade para: $($falta -join ', '). Veja reference/layout.md, secao 'PC total', para montar a formula na mao."
    }
  }
  return [pscustomobject]@{
    geradoEm = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); maquina = $hw.Maquina
    hardware = [pscustomobject]@{ cpu = $hw.Cpu; cpuCurto = $hw.CpuCurto; gpu = $hw.Gpu; gpuCurto = $hw.GpuCurto; vramMB = $hw.VramMB
                                  ramMB = $hw.RamMB; ramGB = $hw.RamGB; cpuLimiteW = $cpuLim; gpuLimiteW = $gpuLim; notebook = $hw.Notebook
                                  discos = @($hw.Discos | ForEach-Object { "{0} {1} [{2}]" -f $_.Modelo, $_.Tipo, ($_.Letras -join ',') }) }
    gruposUsados = [pscustomobject]@{ rtss = @($sel['rtss'] | ForEach-Object { $grupos[$_].nomeOrig }); presentmon = @($sel['presentmon'] | ForEach-Object { $grupos[$_].nomeOrig })
                                      cpu = @($sel['cpu'] | ForEach-Object { $grupos[$_].nomeOrig }); gpu = @($sel['gpu'] | ForEach-Object { $grupos[$_].nomeOrig })
                                      sistema = @($sel['sistema'] | ForEach-Object { $grupos[$_].nomeOrig }); memtimings = @($sel['memtimings'] | ForEach-Object { $grupos[$_].nomeOrig })
                                      drive = @($sel['drive'] | ForEach-Object { $grupos[$_].nomeOrig }) }
    linhas = @($linhas | Sort-Object linha); auxiliares = @($aux); pcTotal = $pcTotal; pcTotalMotivo = $pcMotivo; naoMapeado = @($nao)
  }
}

# ---------------------------------------------------------------- layout: aplicar
function Get-PlanoRegistro($layout) {
  # devolve hashtable (case-insensitive) chave de registro -> [ordered] valores
  $base = 'HKCU:\Software\HWiNFO64\Sensors'
  $alvo = New-Object System.Collections.Hashtable ([StringComparer]::OrdinalIgnoreCase)
  foreach ($l in @($layout.linhas)) {
    $key = "$base\$($l.grupoId)_$($l.inst)\$($l.tipoNome)$($l.idx)"
    $v = [ordered]@{ Label = [string]$l.label; RtssInclude = 1; RtssLine = [int]$l.linha; RtssColumn = 1; RtssShowLabel = 1
                     RtssUseColor = 0; RtssAlignNum = 0; RtssRawValue = 0; RtssUnitsSuperscript = 0 }
    if ($l.unidade) { $v['Unit'] = [string]$l.unidade } else { $v['Unit'] = $null }
    if ($l.valueMult) { $v['ValueMult'] = [string]$l.valueMult } else { $v['ValueMult'] = $null }
    if ($l.grafico) { foreach ($p in $l.grafico.PSObject.Properties) { $v[$p.Name] = $p.Value } } else { $v['RtssGraphShow'] = 0 }
    $alvo[$key] = $v
  }
  foreach ($a in @($layout.auxiliares)) {
    $key = "$base\$($a.grupoId)_$($a.inst)\$($a.tipoNome)$($a.idx)"
    if (-not $alvo.ContainsKey($key)) { $alvo[$key] = [ordered]@{ Label = [string]$a.apelido; RtssInclude = 0 } }
  }
  if ($layout.pcTotal) {
    $pt = $layout.pcTotal
    $alvo["$base\Custom\$($pt.grupoCustom)\Power0"] = [ordered]@{ Name = [string]$pt.nome; Value = [string]$pt.formula }
    $alvo["$base\$($pt.grupoId)_0\Power0"] = [ordered]@{ Label = [string]$pt.label; Unit = [string]$pt.unidade; RtssInclude = 1; RtssLine = [int]$pt.linha
                                                        RtssColumn = 1; RtssShowLabel = 1; RtssUseColor = 0; RtssAlignNum = 0; RtssRawValue = 0; RtssUnitsSuperscript = 0; RtssGraphShow = 0 }
  }
  # linhas antigas que nao estao mais no layout saem do OSD
  if (Test-Path $base) {
    foreach ($g in @(Get-ChildItem $base -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^[0-9A-F]{8}_\d+$' })) {
      foreach ($k in @(Get-ChildItem $g.PSPath -ErrorAction SilentlyContinue)) {
        $inc = (Get-ItemProperty $k.PSPath -Name RtssInclude -ErrorAction SilentlyContinue).RtssInclude
        $caminho = 'HKCU:' + $k.Name.Substring('HKEY_CURRENT_USER'.Length)
        if ($inc -eq 1 -and -not $alvo.ContainsKey($caminho)) { $alvo[$caminho] = [ordered]@{ RtssInclude = 0 } }
      }
    }
  }
  return $alvo
}
function Write-Layout($layout, $c, [bool]$DryRun) {
  $plano = Get-PlanoRegistro $layout
  $base = 'HKCU:\Software\HWiNFO64\Sensors'
  $baseVals = [ordered]@{ RtssToggleHotKey = 0x0003004F; OrderLocked = 1; OsdEnabled = 0 }
  if ($DryRun) {
    Say "--- DRY RUN: valores que seriam escritos no registro ---"
    Say "$base : $(($baseVals.Keys | ForEach-Object { "$_=$($baseVals[$_])" }) -join ', ')"
    foreach ($k in ($plano.Keys | Sort-Object)) {
      $v = $plano[$k]
      $desc = ($v.Keys | ForEach-Object { if ($null -eq $v[$_]) { "$_=<remove>" } else { "$_=$($v[$_])" } }) -join ', '
      Say "$k : $desc"
    }
    return
  }
  Backup-RegistroHwinfo $c | Out-Null
  Set-RegValues $base $baseVals
  $n = 0
  foreach ($k in ($plano.Keys | Sort-Object)) { Set-RegValues $k $plano[$k]; $n++ }
  Say "registro escrito: $n chaves"
}

# ---------------------------------------------------------------- verificacao
function Get-LinhasOsd([string]$Texto) {
  if (-not $Texto) { return @() }
  return @($Texto -split "`r?`n")
}
function Compare-OsdComLayout($layout, [string]$Texto) {
  # devolve lista de [label, presente(bool), ordemOk(bool)]
  $linhas = @(Get-LinhasOsd $Texto)
  $esperado = @($layout.linhas | Sort-Object linha | ForEach-Object { $_.label })
  if ($layout.pcTotal) { $esperado += [string]$layout.pcTotal.label }
  $res = @(); $pos = -1; $ordemOk = $true
  foreach ($e in $esperado) {
    $rx = '^' + [regex]::Escape($e) + ':'
    $i = -1
    for ($j = $pos + 1; $j -lt $linhas.Count; $j++) { if ($linhas[$j] -match $rx) { $i = $j; break } }
    if ($i -lt 0) {
      for ($j = 0; $j -lt $linhas.Count; $j++) { if ($linhas[$j] -match $rx) { $i = $j; $ordemOk = $false; break } }
    }
    $presente = ($i -ge 0)
    $texto = ''
    if ($presente) { $texto = $linhas[$i]; if ($i -gt $pos) { $pos = $i } }
    $res += [pscustomobject]@{ Label = $e; Presente = $presente; Linha = $texto }
  }
  return [pscustomobject]@{ Itens = $res; OrdemOk = $ordemOk; Faltando = @($res | Where-Object { -not $_.Presente } | ForEach-Object { $_.Label }) }
}
