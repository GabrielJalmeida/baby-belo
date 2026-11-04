$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$stateDir = Join-Path $projectRoot '.local'
if (-not (Test-Path -LiteralPath (Join-Path $stateDir 'config.json'))) {
    throw 'Inicie primeiro: node scripts/local-db.mjs. Consulte docs/EXECUCAO_LOCAL.md.'
}
function Test-LocalPort([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try { $client.Connect('127.0.0.1', $Port); return $true } catch { return $false } finally { $client.Dispose() }
}
function Wait-LocalPort([int]$Port) {
    for ($attempt = 0; $attempt -lt 150; $attempt++) {
        if (Test-LocalPort $Port) { return }
        Start-Sleep -Milliseconds 200
    }
    throw "O serviço na porta $Port não iniciou. Consulte os logs em .local."
}
$localConfig = Get-Content -LiteralPath (Join-Path $stateDir 'config.json') -Raw | ConvertFrom-Json
$nodeExe = (Get-Command node -ErrorAction Stop).Source
if (-not (Test-LocalPort $localConfig.port)) {
    Start-Process -FilePath $nodeExe -ArgumentList @('scripts/local-db.mjs') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $stateDir 'postgres.log') -RedirectStandardError (Join-Path $stateDir 'postgres-error.log') | Out-Null
    Wait-LocalPort $localConfig.port
}
if (-not (Test-LocalPort 8000)) {
    Start-Process -FilePath powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/start-api.ps1') -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $stateDir 'api.log') -RedirectStandardError (Join-Path $stateDir 'api-error.log') | Out-Null
    Wait-LocalPort 8000
}
if (-not (Test-LocalPort 5174)) {
    Start-Process -FilePath $nodeExe -ArgumentList @('node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5174','--strictPort') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $stateDir 'frontend.log') -RedirectStandardError (Join-Path $stateDir 'frontend-error.log') | Out-Null
    Wait-LocalPort 5174
}
$health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health'
if ($health.status -ne 'ok') { throw 'A API não confirmou que está pronta.' }
Write-Host 'Baby Belo disponível em http://127.0.0.1:5174/'
Write-Host 'Primeiro acesso: execute scripts/create-owner.ps1 para criar sua conta pessoal.'

