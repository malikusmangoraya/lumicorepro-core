param(
  [string]$DestinationName = 'new rebuilt',
  [switch]$DryRun,
  [switch]$Resume,
  [int]$Limit = 0,
  [string]$Provider
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceRoot = Join-Path $repoRoot 'generated-projects'
$outputRoot = Join-Path (Join-Path $repoRoot $DestinationName) 'agent-generated'
$arguments = @(
  '-m', 'agent.rebuild_generated_projects',
  '--source-root', $sourceRoot,
  '--output-root', $outputRoot,
  '--limit', $Limit
)

if ($Resume) { $arguments += '--resume' }
if ($DryRun) { $arguments += '--dry-run' }
if ($Provider) { $arguments += @('--provider', $Provider) }

Push-Location (Join-Path $repoRoot 'ai-agent')
try {
  & python @arguments
  $agentExitCode = $LASTEXITCODE
} finally {
  Pop-Location
}
exit $agentExitCode
