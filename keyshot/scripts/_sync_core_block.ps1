# _sync_core_block.ps1 -- copy the CORE BLOCK from the canonical source into all carriers
# Usage: powershell -ExecutionPolicy Bypass -File keyshot/scripts/_sync_core_block.ps1
# Optional: -Source <path>  (defaults to the 1_HLP_MAT_GENERATOR_*.py file in this directory)
param([string]$Source)

$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startMark = '# ===== CORE BLOCK v1 --'
$endMark   = '# ===== END CORE BLOCK v1'

# --- resolve source ---
if (-not $Source) {
    $hits = @(Get-ChildItem -Path $dir -Filter '1_HLP_MAT_GENERATOR_*.py')
    if ($hits.Count -eq 0) { Write-Error "No file matching 1_HLP_MAT_GENERATOR_*.py in $dir"; exit 1 }
    $Source = ($hits | Sort-Object Name)[-1].FullName  # latest REV by alpha sort
} elseif (-not (Test-Path $Source)) { Write-Error "Source not found: $Source"; exit 1 }

# --- extract block from a file (returns $null on missing/malformed markers) ---
function Get-CoreBlock([string]$path) {
    $lines = [System.IO.File]::ReadAllLines($path)
    $s = -1; $e = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($s -lt 0 -and $lines[$i].StartsWith($startMark)) { $s = $i }
        elseif ($s -ge 0 -and $lines[$i].StartsWith($endMark)) { $e = $i; break }
    }
    if ($s -lt 0 -and $e -lt 0) { return $null }                         # no markers at all
    if ($s -ge 0 -xor $e -ge 0) { return @{ Error = 'unpaired marker' } } # malformed
    return @{ Before = $lines[0..($s-1)]; Block = $lines[$s..$e]; After = $lines[($e+1)..($lines.Count-1)] }
}

# --- read canonical block ---
$src = Get-CoreBlock $Source
if ($src -eq $null)           { Write-Error "Source has no CORE BLOCK markers: $Source"; exit 1 }
if ($src.ContainsKey('Error')){ Write-Error "Source has $($src.Error): $Source"; exit 1 }
$canonical = $src.Block

# --- sweep targets ---
$checked = 0; $updated = 0; $identical = 0
foreach ($f in Get-ChildItem -Path $dir -Filter '*.py') {
    if ($f.FullName -eq (Resolve-Path $Source).Path) { continue }
    $t = Get-CoreBlock $f.FullName
    if ($t -eq $null) { continue }  # no markers -- not a carrier
    if ($t.ContainsKey('Error')) {
        Write-Warning "$($f.Name): $($t.Error) -- skipped"
        $checked++; continue
    }
    $checked++
    if (($t.Block -join "`n") -eq ($canonical -join "`n")) {
        Write-Host "  identical  $($f.Name)"
        $identical++; continue
    }
    $merged = @($t.Before) + @($canonical) + @($t.After)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($f.FullName, ($merged -join "`n") + "`n", $utf8NoBom)
    Write-Host "  UPDATED    $($f.Name)"
    $updated++
}

Write-Host "`n$checked carriers checked: $updated updated, $identical already identical."
