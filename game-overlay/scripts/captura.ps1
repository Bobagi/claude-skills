# captura.ps1 - salva em PNG um retangulo da tela (ou a tela virtual inteira).
# Fica num arquivo separado de proposito: o AMSI do Defender bloqueia um script que junta
# "localizar/ativar janela" com captura de tela; aqui so existe a captura, e o retangulo
# chega pronto por parametro (o overlay.ps1 o descobre por UI Automation).
param([int]$X = 0, [int]$Y = 0, [int]$W = 0, [int]$H = 0, [Parameter(Mandatory = $true)][string]$Path)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
if ($W -le 0 -or $H -le 0) {
  $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
  $X = $b.Left; $Y = $b.Top; $W = $b.Width; $H = $b.Height
}
$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($X, $Y, 0, 0, $bmp.Size)
$bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "ok $Path ${W}x${H}"
