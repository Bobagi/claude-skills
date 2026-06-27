#!/usr/bin/env pwsh
# claude-sync.ps1 — port PowerShell do claude-sync.sh (Windows nativo / pwsh).
# Mesma semântica do .sh:
#   pull   (hook SessionStart) -> git pull --ff-only; reaplica config que estava EM
#          SYNC (sem clobberar edição local) e avisa se houver drift local.
#   check  (hook SessionEnd)   -> só detecta drift e avisa. NUNCA pusha.
#   save   (/sync-claude --save) -> copia a config viva -> config/, scan de segredos,
#          commita + pusha.
# pull/check são não-bloqueantes (sempre saem 0). 'save' pode abortar (ex.: segredo).

param([string]$Cmd = '')

$ErrorActionPreference = 'SilentlyContinue'
$ClaudeHome = Join-Path $HOME '.claude'
$BackupDir  = Join-Path $ClaudeHome 'backups'

# --- localizar o repo -------------------------------------------------------
function Find-Repo {
  $cands = @()
  if ($PSScriptRoot) { $cands += (Split-Path $PSScriptRoot -Parent) }   # <repo>/scripts/..
  $cands += '/opt/claude-skills'
  $cands += (Join-Path $ClaudeHome 'claude-skills')
  $cands += (Join-Path $ClaudeHome 'skills')                            # symlink/junction
  foreach ($d in $cands) {
    if ($d -and (Test-Path (Join-Path $d '.git'))) { return (Resolve-Path $d).Path }
  }
  return $null
}
$RepoDir = Find-Repo
if (-not $RepoDir) { exit 0 }   # sem repo nesta máquina: nada a fazer

# config espelhada: Rel (no repo) -> Live (caminho vivo)
$ConfigPairs = @(
  [pscustomobject]@{ Rel = 'config/CLAUDE.md';                Live = (Join-Path $ClaudeHome 'CLAUDE.md') }
  [pscustomobject]@{ Rel = 'config/settings.json';            Live = (Join-Path $ClaudeHome 'settings.json') }
  [pscustomobject]@{ Rel = 'config/skill-first-reminder.txt'; Live = (Join-Path $ClaudeHome 'skill-first-reminder.txt') }
)

# --- helpers ----------------------------------------------------------------
function Files-Equal($a, $b) {
  if (-not (Test-Path $a) -or -not (Test-Path $b)) { return $false }
  return (Get-FileHash -Algorithm SHA256 $a).Hash -eq (Get-FileHash -Algorithm SHA256 $b).Hash
}

function Emit($msg) {
  # {"systemMessage": "..."} — ConvertTo-Json escapa aspas/barras/quebras
  [pscustomobject]@{ systemMessage = $msg } | ConvertTo-Json -Compress
}

function Get-DriftReport {
  $lines = @()
  foreach ($p in $ConfigPairs) {
    $src = Join-Path $RepoDir $p.Rel
    if (-not (Test-Path $src)) { continue }
    if (-not (Files-Equal $src $p.Live)) {
      $lines += ('• ' + (Split-Path $p.Live -Leaf) + ' difere do repo')
    }
  }
  $status = git -C $RepoDir status --porcelain 2>$null
  if ($status) { $lines += '• árvore do repo com mudanças não-commitadas' }
  git -C $RepoDir rev-parse '@{u}' 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $unpushed = git -C $RepoDir log '@{u}..HEAD' --oneline 2>$null
    if ($unpushed) { $lines += '• commits locais ainda não enviados (push)' }
  }
  return ($lines -join "`n")
}

# --- subcomandos ------------------------------------------------------------
function Cmd-Pull {
  # snapshot pré-pull: o que estava EM SYNC
  $insync = @{}
  foreach ($p in $ConfigPairs) {
    $src = Join-Path $RepoDir $p.Rel
    $insync[$p.Rel] = (Files-Equal $src $p.Live)
  }

  git -C $RepoDir pull --ff-only 2>$null | Out-Null

  New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  foreach ($p in $ConfigPairs) {
    $src = Join-Path $RepoDir $p.Rel
    if (-not (Test-Path $src)) { continue }
    if ($insync[$p.Rel] -and -not (Files-Equal $src $p.Live)) {
      if (Test-Path $p.Live) {
        Copy-Item $p.Live (Join-Path $BackupDir ((Split-Path $p.Live -Leaf) + ".bak-$stamp")) -Force
      }
      Copy-Item $src $p.Live -Force
    }
  }

  $report = Get-DriftReport
  if ($report) {
    Emit "Config local do Claude difere do repo claude-skills:`n$report`n`nRode /sync-claude --save para versionar e propagar às outras máquinas (ou /sync-claude para puxar do repo)."
  }
}

function Cmd-Check {
  $report = Get-DriftReport
  if ($report) {
    Emit "Mudanças de config locais do Claude ainda não versionadas:`n$report`n`nRode /sync-claude --save para enviá-las ao repo claude-skills."
  }
}

function Cmd-Save {
  foreach ($p in $ConfigPairs) {
    $src = Join-Path $RepoDir $p.Rel
    if (-not (Test-Path $p.Live)) { continue }
    if (-not (Files-Equal $p.Live $src)) { Copy-Item $p.Live $src -Force }
  }

  git -C $RepoDir add -A
  git -C $RepoDir diff --cached --quiet
  if ($LASTEXITCODE -eq 0) { Write-Output '✓ Nada a salvar — repo já está em dia.'; return }

  $secretRe = '(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN[A-Z ]*PRIVATE KEY-----|AIza[0-9A-Za-z_-]{30,})'
  $diff = git -C $RepoDir diff --cached
  $hits = $diff | Select-String -Pattern $secretRe
  if ($hits) {
    git -C $RepoDir reset -q
    Write-Output '✗ ABORTADO: o diff parece conter um segredo — nada foi commitado/pushado.'
    Write-Output '  Padrões batidos (revise e remova antes de salvar):'
    ($hits | Select-Object -First 20).Line -replace '[A-Za-z0-9_-]{8,}', '[REDACTED]' | ForEach-Object { Write-Output $_ }
    exit 1
  }

  git -C $RepoDir commit -q -m ("sync: salvar config local (" + (hostname) + ") via claude-sync save")
  git -C $RepoDir push -q 2>$null
  if ($LASTEXITCODE -eq 0) { Write-Output '✓ Config salva e pushada para claude-skills.' }
  else { Write-Output "! Commit feito, mas o push falhou (offline/sem auth). Rode 'git -C $RepoDir push' depois." }
}

try {
  switch ($Cmd) {
    'pull'   { Cmd-Pull }
    'check'  { Cmd-Check }
    'save'   { Cmd-Save }
    '--save' { Cmd-Save }
    default  { [Console]::Error.WriteLine('uso: claude-sync.ps1 {pull|check|save}') }
  }
} catch {
  # hook nunca derruba a sessão
}
exit 0
