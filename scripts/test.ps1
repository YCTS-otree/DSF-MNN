$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectDir
$env:PYTHONPATH = Join-Path $projectDir 'src'
$env:PYTHONIOENCODING = 'utf-8'
New-Item -ItemType Directory -Path '.cache' -Force | Out-Null
$testDir = Join-Path $projectDir ('.cache/pytest-' + [guid]::NewGuid().ToString('N'))
python -m pytest -q --tb=short --basetemp $testDir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
node --test tests/*.test.mjs
exit $LASTEXITCODE
