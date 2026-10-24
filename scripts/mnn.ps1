$projectDir = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $projectDir 'src'
$env:PYTHONIOENCODING = 'utf-8'
python -m dsf_mnn @args
exit $LASTEXITCODE
