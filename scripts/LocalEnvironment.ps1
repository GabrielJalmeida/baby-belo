param([switch]$TestDatabase)
$projectRoot = Split-Path -Parent $PSScriptRoot
$localConfig = Get-Content -LiteralPath (Join-Path $projectRoot '.local/config.json') -Raw | ConvertFrom-Json
$dbName = if ($TestDatabase) { 'baby_belo_test' } else { 'baby_belo_dev' }
$env:DATABASE_URL = 'postgresql+psycopg://{0}:{1}@127.0.0.1:{2}/{3}' -f $localConfig.user,$localConfig.password,$localConfig.port,$dbName
$env:TEST_AUTH_DATABASE_URL = 'postgresql+psycopg://{0}:{1}@127.0.0.1:{2}/baby_belo_auth_test' -f $localConfig.user,$localConfig.password,$localConfig.port
$env:SECRET_KEY = $localConfig.secret
$env:CORS_ALLOWED_ORIGINS = '["http://127.0.0.1:5174","http://localhost:5174"]'
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = Join-Path $projectRoot 'backend'

