# Rebuild script for generated-projects (auto mode)
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_generated.ps1 -Chunk 0 -Size 20
param(
  [int]$Chunk = 0,
  [int]$Size  = 20,
  [switch]$Single,
  [string]$Slug
)

$root = "D:\lumicorepro-core"
$gp   = Join-Path $root "generated-projects"
$logDir = Join-Path $root "logs\rebuild"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$dirs = Get-ChildItem -LiteralPath $gp -Directory | Sort-Object Name
if ($Slug) { $dirs = $dirs | Where-Object { $_.Name -eq $Slug } }
if ($Single) { $dirs = @($dirs | Select-Object -First 1) }
elseif ($Size -gt 0) {
  $start = $Chunk * $Size
  $dirs  = @($dirs | Select-Object -Skip $start -First $Size)
}

$results = @()
foreach ($d in $dirs) {
  $name = $d.Name
  $fe   = Join-Path $d.FullName "frontend"
  $pkg  = Join-Path $fe "package.json"
  if (-not (Test-Path -LiteralPath $pkg)) {
    $results += [pscustomobject]@{ Name=$name; Status="NO_FRONTEND_PKG"; Exit=1; Sec=0 }
    continue
  }
  $log = Join-Path $logDir ("{0}-chunk{1}-{2:yyyyMMddHHmmss}.log" -f $name, $Chunk, [DateTime]::Now)
  $sw  = [Diagnostics.Stopwatch]::StartNew()
  $hasLock = Test-Path -LiteralPath (Join-Path $fe "package-lock.json")
  $hasNm   = Test-Path -LiteralPath (Join-Path $fe "node_modules\vite")
  Push-Location -LiteralPath $fe
  try {
    # 91/95 already have a populated node_modules - reuse it and build directly.
    # `npm ci` needs a lockfile; 4 of the 95 projects ship without one.
    if (-not $hasNm) {
      if ($hasLock) {
        npm ci --no-audit --no-fund --prefer-offline 2>&1 | Tee-Object -FilePath $log | Out-Null
      } else {
        npm install --no-audit --no-fund --prefer-offline 2>&1 | Tee-Object -FilePath $log | Out-Null
      }
      $codeCi = $LASTEXITCODE
      if ($codeCi -ne 0) {
        $sw.Stop()
        Pop-Location
        $results += [pscustomobject]@{ Name=$name; Status="NPM_CI_FAIL"; Exit=$codeCi; Sec=[int]$sw.Elapsed.TotalSeconds }
        continue
      }
    }
    npm run build 2>&1 | Tee-Object -Append -FilePath $log | Out-Null
    $codeB = $LASTEXITCODE
    $sw.Stop()
    if ($codeB -eq 0) {
      $dist = Join-Path $fe "dist"
      $hasDist = Test-Path -LiteralPath $dist
      $results += [pscustomobject]@{ Name=$name; Status=("OK" + $(if ($hasDist) {""} else {"_NO_DIST_DIR"})); Exit=0; Sec=[int]$sw.Elapsed.TotalSeconds }
    } else {
      $results += [pscustomobject]@{ Name=$name; Status="BUILD_FAIL"; Exit=$codeB; Sec=[int]$sw.Elapsed.TotalSeconds }
    }
  } catch {
    $sw.Stop()
    Pop-Location
    $results += [pscustomobject]@{ Name=$name; Status="EXC"; Exit=1; Sec=[int]$sw.Elapsed.TotalSeconds }
  } finally {
    Pop-Location -ErrorAction SilentlyContinue
  }
}
$csv = Join-Path $logDir ("chunk{0}-{1:yyyyMMddHHmmss}.csv" -f $Chunk, [DateTime]::Now)
$results | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding UTF8
$results | Format-Table -AutoSize | Out-String | Out-Host
$ok = @($results | Where-Object { $_.Status -like "OK*" }).Count
$fail = $results.Count - $ok
Write-Host ("CHUNK {0} DONE  ok={1} fail={2} total={3}  csv={4}" -f $Chunk, $ok, $fail, $results.Count, $csv)
if ($fail -gt 0) { exit 1 } else { exit 0 }
