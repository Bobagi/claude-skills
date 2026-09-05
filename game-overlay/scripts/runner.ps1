# Runner elevado temporario: executa os scripts job-*.ps1 deixados em
# <Raiz>\_Config\jobs\ (ordem alfabetica), grava a saida em .out ao lado e renomeia
# o job para .done. Um unico UAC serve para a sessao inteira. Encerra sozinho
# quando aparecer o arquivo jobs\STOP ou depois de 60 minutos.
#
# Instalado pela skill game-overlay. Inicie com:
#   Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "<Raiz>\_Config\runner.ps1"'
# Enquanto jobs\_runner-vivo.txt existir, o overlay.ps1 enfileira nele em vez de pedir UAC.
$ErrorActionPreference = 'Continue'
$jobs = "__RAIZ__\_Config\jobs"
New-Item -ItemType Directory -Path $jobs -Force | Out-Null
Remove-Item "$jobs\STOP" -Force -ErrorAction SilentlyContinue
Set-Content -Path "$jobs\_runner-vivo.txt" -Value "iniciado $(Get-Date -Format 'HH:mm:ss') pid=$PID" -Encoding UTF8
$fim = (Get-Date).AddMinutes(60)
while ((Get-Date) -lt $fim) {
  if (Test-Path "$jobs\STOP") { break }
  $j = Get-ChildItem $jobs -Filter "job-*.ps1" -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -First 1
  if ($j) {
    $out = [IO.Path]::ChangeExtension($j.FullName, ".out")
    try   { $r = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $j.FullName 2>&1 }
    catch { $r = "ERRO: $($_.Exception.Message)" }
    Set-Content -Path $out -Value ($r | Out-String) -Encoding UTF8
    Rename-Item $j.FullName ($j.FullName + ".done") -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Milliseconds 700
}
Remove-Item "$jobs\_runner-vivo.txt" -Force -ErrorAction SilentlyContinue
Remove-Item "$jobs\STOP" -Force -ErrorAction SilentlyContinue
