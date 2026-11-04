. (Join-Path $PSScriptRoot 'LocalEnvironment.ps1') -TestDatabase
Set-Location -LiteralPath $projectRoot
& (Join-Path $projectRoot '.venv/Scripts/python.exe') -m pytest backend/tests -q
exit $LASTEXITCODE

