Write-Host "🚀 Reorganizando proyecto BENDICIÓN..."

$base = "C:\Users\empir\Documents\GitHub\Criptomoneda-BENDICION"

# Crear estructura
$folders = @(
    "$base\backend\app\admin",
    "$base\backend\app\user",
    "$base\backend\app\security",
    "$base\backend\app\utils",
    "$base\backend",
    "$base\frontend\templates",
    "$base\frontend\public\css",
    "$base\frontend\public\js",
    "$base\frontend\public\img",
    "$base\docs"
)

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "📁 Creado: $folder"
    }
}

# Mover backend
if (Test-Path "$base\node.py") { Move-Item "$base\node.py" "$base\backend\app\node.py" }
if (Test-Path "$base\blockchain.py") { Move-Item "$base\blockchain.py" "$base\backend\app\blockchain.py" }
if (Test-Path "$base\database.py") { Move-Item "$base\database.py" "$base\backend\app\database.py" }
if (Test-Path "$base\wallet.py") { Move-Item "$base\wallet.py" "$base\backend\app\wallet.py" }
if (Test-Path "$base\wallet_manager.py") { Move-Item "$base\wallet_manager.py" "$base\backend\app\wallet_manager.py" }
if (Test-Path "$base\admin_server.py") { Move-Item "$base\admin_server.py" "$base\backend\app\admin\admin_routes.py" }

# JSON
if (Test-Path "$base\database.json") { Move-Item "$base\database.json" "$base\backend\database.json" }
if (Test-Path "$base\wallets.json") { Move-Item "$base\wallets.json" "$base\backend\wallets.json" }

# KYC docs
if (Test-Path "$base\kyc_docs") { Move-Item "$base\kyc_docs" "$base\backend\kyc_docs" }

# Docker
if (Test-Path "$base\Dockerfile") { Move-Item "$base\Dockerfile" "$base\backend\Dockerfile" }
if (Test-Path "$base\docker-compose.yml") { Move-Item "$base\docker-compose.yml" "$base\backend\docker-compose.yml" }

# HTML
$htmlFiles = @(
    "index.html", "login.html", "register.html", "admin_kyc.html",
    "estado_kyc.html", "KYC_aprobado.html", "kyc.html", "KYCtelefono.html"
)

foreach ($file in $htmlFiles) {
    if (Test-Path "$base\$file") {
        Move-Item "$base\$file" "$base\frontend\templates\$file"
        Write-Host "📄 Movido: $file"
    }
}

# Templates folder
if (Test-Path "$base\templates\admin.html") { Move-Item "$base\templates\admin.html" "$base\frontend\templates\admin.html" }
if (Test-Path "$base\templates\login.html") { Move-Item "$base\templates\login.html" "$base\frontend\templates\login.html" }

# Documentación
if (Test-Path "$base\readme") {
    Move-Item "$base\readme\*" "$base\docs\" -Force
}

# Eliminar __pycache__
Get-ChildItem -Path $base -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Host "✨ Proyecto reorganizado con éxito."
