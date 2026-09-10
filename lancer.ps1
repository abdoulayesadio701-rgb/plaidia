$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$backendUrl = "http://localhost:8000/api/health"
$frontendUrl = "http://localhost:5173"

Start-Process cmd.exe -ArgumentList @(
    "/k",
    "cd /d `"$backend`" && python -m uvicorn app.main:app --reload --port 8000"
) -WindowStyle Normal

Start-Process cmd.exe -ArgumentList @(
    "/k",
    "cd /d `"$frontend`" && npm run dev"
) -WindowStyle Normal

function Wait-ForUrl([string]$url, [string]$name) {
    for ($attempt = 1; $attempt -le 180; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$name est prêt : $url"
                return
            }
        } catch {
            # Le serveur est encore en démarrage.
        }
        if ($attempt % 15 -eq 0) {
            Write-Host "$name démarre toujours... ($attempt/180 secondes)"
        }
        Start-Sleep -Seconds 1
    }
    throw "$name n'est pas devenu disponible après 180 secondes : $url"
}

Wait-ForUrl $backendUrl "Backend FastAPI"
Wait-ForUrl $frontendUrl "Frontend Vite"
Start-Process $frontendUrl
Write-Host "Plaid'IA est ouvert dans le navigateur."
