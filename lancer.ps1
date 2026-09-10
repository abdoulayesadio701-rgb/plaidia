$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$backendUrl = "http://localhost:8000/api/health"
$frontendUrl = "http://localhost:5173"

Start-Process powershell.exe -WorkingDirectory $backend -ArgumentList @(
    "-NoExit",
    "-Command",
    "python -m uvicorn app.main:app --reload --port 8000"
) -WindowStyle Normal

Start-Process powershell.exe -WorkingDirectory $frontend -ArgumentList @(
    "-NoExit",
    "-Command",
    "npm run dev"
) -WindowStyle Normal

function Wait-ForUrl([string]$url, [string]$name) {
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$name est prêt : $url"
                return
            }
        } catch {
            # Le serveur est encore en démarrage.
        }
        Start-Sleep -Seconds 1
    }
    throw "$name n'est pas devenu disponible après 60 secondes : $url"
}

Wait-ForUrl $backendUrl "Backend FastAPI"
Wait-ForUrl $frontendUrl "Frontend Vite"
Start-Process $frontendUrl
Write-Host "Plaid'IA est ouvert dans le navigateur."
