. (Join-Path $PSScriptRoot 'LocalEnvironment.ps1')
Set-Location -LiteralPath $projectRoot
& (Join-Path $projectRoot '.venv/Scripts/python.exe') -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
exit $LASTEXITCODE

