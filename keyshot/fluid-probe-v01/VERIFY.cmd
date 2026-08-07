@echo off
REM Check this package survived the trip on the drive. No Python, no install, no admin needed.
REM Run it BEFORE blaming KeyShot for anything: a truncated USB copy and a broken exporter look
REM identical from the KeyShot side, and only one of them is real.
set "PKG=%~dp0"
echo.
echo Verifying package files against CHECKSUMS.txt
echo   %PKG%
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$true; Get-Content '%PKG%CHECKSUMS.txt' | Where-Object { $_.Trim() } | ForEach-Object { $p = $_ -split '\s+', 2; $h = $p[0].Trim(); $f = $p[1].Trim(); $fp = Join-Path '%PKG%' $f; if (-not (Test-Path $fp)) { Write-Host ('MISSING   ' + $f) -Foreground Red; $ok = $false; return }; $a = (Get-FileHash -Algorithm SHA256 -LiteralPath $fp).Hash; if ($a -ieq $h) { Write-Host ('ok        ' + $f) -Foreground Green } else { Write-Host ('CORRUPT   ' + $f) -Foreground Red; $ok = $false } }; Write-Host ''; if ($ok) { Write-Host 'All files match. The copy is good - anything odd from here is real.' -Foreground Green } else { Write-Host 'A file is missing or corrupt. Recopy from the drive before debugging anything else.' -Foreground Red }"
echo.
pause
