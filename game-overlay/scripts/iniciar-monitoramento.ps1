# Sobe o monitoramento na ordem certa: RTSS primeiro, HWiNFO depois.
# O HWiNFO so enumera o grupo de sensores [RTSS] (de onde vem o FPS atual e o
# Frametime) na inicializacao. Se ele nascer antes do RTSS, o grupo nao existe e
# essas duas linhas somem do overlay ate o proximo reinicio do HWiNFO.
#
# Instalado pela skill game-overlay em <Raiz>\_Config\ e chamado pela tarefa
# agendada "HWiNFO64 (monitoramento)" no logon, ja elevada (sem UAC).
# ASCII puro: o PowerShell 5.1 le .ps1 sem BOM como ANSI.
$ErrorActionPreference = 'Continue'
$Raiz = '__RAIZ__'          # raiz da instalacao (a skill substitui ao instalar)
$log  = "$Raiz\_Config\inicio.log"
$exeR = "$Raiz\RTSS\RTSS.exe"
$exeH = "$Raiz\HWiNFO\HWiNFO64.EXE"
$ini  = "$Raiz\HWiNFO\HWiNFO64.INI"
function A($m){ Add-Content $log ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) -Encoding UTF8 }
if ((Test-Path $log) -and ((Get-Item $log).Length -gt 65536)) {
  Set-Content $log ((Get-Content $log -Tail 200) -join "`r`n") -Encoding UTF8 }
A "--- inicio do monitoramento ---"

# 0) Shared Memory Support do HWiNFO: a versao gratis desliga depois de 12 h e regrava
#    o INI sem a chave. Reafirmar aqui (com o HWiNFO ainda fechado) garante as primeiras
#    12 h de cada sessao com a memoria compartilhada ligada (CapFrameX e diagnostico usam).
if ((Test-Path $ini) -and -not (Get-Process -Name HWiNFO64 -ErrorAction SilentlyContinue)) {
  try {
    $txt = Get-Content $ini -Encoding Default
    if ($txt -match '^\s*SensorsSM\s*=') { $txt = $txt | ForEach-Object { if ($_ -match '^\s*SensorsSM\s*=') { 'SensorsSM=1' } else { $_ } } }
    else { $txt = $txt | ForEach-Object { $_; if ($_ -match '^\s*\[Settings\]') { 'SensorsSM=1' } } }
    Set-Content -Path $ini -Value $txt -Encoding Ascii
    A "INI do HWiNFO: SensorsSM=1 reafirmado"
  } catch { A "INI do HWiNFO: nao consegui reafirmar SensorsSM ($($_.Exception.Message))" }
}

# 1) RTSS. Exige administrador; nascendo daqui herda o token elevado da tarefa,
#    entao nao aparece UAC nenhum. Sempre Start-Process: "cmd /c start | Out-Null"
#    trava o script, porque o RTSS herda o handle de saida e o pipeline nunca fecha.
if (Get-Process -Name RTSS -ErrorAction SilentlyContinue) { A "RTSS ja estava rodando" }
else { Start-Process -FilePath $exeR -WorkingDirectory (Split-Path $exeR); A "RTSS lancado" }

# 2) espera a memoria compartilhada do RTSS existir (ate 90 s)
$t0 = Get-Date; $pronto = $false
while (-not $pronto -and ((Get-Date)-$t0).TotalSeconds -lt 90) {
  try { $m=[System.IO.MemoryMappedFiles.MemoryMappedFile]::OpenExisting("RTSSSharedMemoryV2",
          [System.IO.MemoryMappedFiles.MemoryMappedFileRights]::Read); $m.Dispose(); $pronto=$true }
  catch { Start-Sleep -Milliseconds 500 } }
A ("memoria compartilhada do RTSS pronta={0} apos {1:N1} s" -f $pronto, ((Get-Date)-$t0).TotalSeconds)

# 3) HWiNFO
if (Get-Process -Name HWiNFO64 -ErrorAction SilentlyContinue) { A "HWiNFO ja estava rodando" }
else { Start-Process -FilePath $exeH -WorkingDirectory (Split-Path $exeH); A "HWiNFO lancado" }

# 4) confere que o HWiNFO esta escrevendo a linha "FPS:" no OSD do RTSS. Essa linha
#    so existe se o grupo [RTSS] foi enumerado. Le o slot de OSD do RTSSSharedMemoryV2
#    cujo dono e o HWiNFO64 (cabecalho: dwOSDEntrySize em 20, dwOSDArrOffset em 24,
#    dwOSDArrSize em 28; entrada: szOSD[256], szOSDOwner[256], szOSDEx[4096]).
function OsdTemFps {
  try { $m=[System.IO.MemoryMappedFiles.MemoryMappedFile]::OpenExisting("RTSSSharedMemoryV2",
          [System.IO.MemoryMappedFiles.MemoryMappedFileRights]::Read) } catch { return $false }
  $a=$m.CreateViewAccessor(0,0,[System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read)
  $tam=$a.ReadUInt32(20); $off=$a.ReadUInt32(24); $n=$a.ReadUInt32(28); $achou=$false
  for($i=0;$i -lt $n;$i++){
    $base=$off+[long]$i*$tam
    $b=New-Object byte[] 256; $a.ReadArray($base+256,$b,0,256)|Out-Null
    $dono=[Text.Encoding]::ASCII.GetString($b).TrimEnd([char]0)
    if($dono -like 'HWiNFO*'){
      $b1=New-Object byte[] 256;  $a.ReadArray($base,$b1,0,256)|Out-Null
      $b2=New-Object byte[] 4096; $a.ReadArray($base+512,$b2,0,4096)|Out-Null
      $txt=([Text.Encoding]::Default.GetString($b1)+"`n"+[Text.Encoding]::Default.GetString($b2))
      if($txt -match '(?m)^FPS:'){ $achou=$true } } }
  $a.Dispose(); $m.Dispose(); return $achou }

# 4b) fallback: grupo [RTSS] (ID F00F5000) na memoria compartilhada do HWiNFO.
#     So funciona com "Shared Memory Support" ligado no HWiNFO.
function TemGrupoRtss {
  try { $m=[System.IO.MemoryMappedFiles.MemoryMappedFile]::OpenExisting("Global\HWiNFO_SENS_SM2",
          [System.IO.MemoryMappedFiles.MemoryMappedFileRights]::Read) } catch { return $false }
  $a=$m.CreateViewAccessor(0,0,[System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read)
  $off=$a.ReadUInt32(20); $tam=$a.ReadUInt32(24); $n=$a.ReadUInt32(28); $achou=$false
  for($i=0;$i -lt $n;$i++){ if((("{0:X8}" -f $a.ReadUInt32($off+[long]$i*$tam))) -eq 'F00F5000'){ $achou=$true } }
  $a.Dispose(); $m.Dispose(); return $achou }

function EsperaFps([int]$seg){
  $t=Get-Date
  while(((Get-Date)-$t).TotalSeconds -lt $seg){ if((OsdTemFps) -or (TemGrupoRtss)){ return $true }; Start-Sleep -Seconds 2 }
  return $false }

if (EsperaFps 60) { A "linha FPS presente no OSD, grupo [RTSS] OK" }
else {
  A "linha FPS ausente no OSD, reiniciando o HWiNFO uma vez"
  Get-Process -Name HWiNFO64 -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 4
  Start-Process -FilePath $exeH -WorkingDirectory (Split-Path $exeH)
  A ("apos reinicio, linha FPS presente={0}" -f (EsperaFps 60)) }
A "--- fim ---"
