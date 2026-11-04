. (Join-Path $PSScriptRoot 'LocalEnvironment.ps1')
Set-Location -LiteralPath $projectRoot
Write-Host 'Crie sua conta pessoal. No nome da empresa, informe Baby Belo Ateliê.'
& (Join-Path $projectRoot '.venv/Scripts/python.exe') backend/create_initial_user.py
exit $LASTEXITCODE

