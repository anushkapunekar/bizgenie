Write-Host "=== BizGenie Setup Check ===" -ForegroundColor Cyan

# Check Python
Write-Host ""
Write-Host "1. Checking Python..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath -like "*venv*") {
    Write-Host "   [OK] Virtual environment is active" -ForegroundColor Green
    Write-Host "   Python: $pythonPath" -ForegroundColor Gray
} else {
    Write-Host "   [FAIL] Virtual environment NOT active" -ForegroundColor Red
    Write-Host "   Run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}

# Check key packages
Write-Host ""
Write-Host "2. Checking key packages..." -ForegroundColor Yellow
$packages = @("sqlalchemy", "fastapi", "uvicorn", "langgraph")
foreach ($pkg in $packages) {
    $result = pip show $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        $version = ($result | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host "   [OK] $pkg ($version)" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] $pkg not found" -ForegroundColor Red
    }
}

# Check backend import
Write-Host ""
Write-Host "3. Testing backend import..." -ForegroundColor Yellow
$importTest = python -c "from app.main import app; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Backend imports successfully" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Backend import failed" -ForegroundColor Red
    Write-Host "   Error: $importTest" -ForegroundColor Gray
}

# Check frontend
Write-Host ""
Write-Host "4. Checking frontend..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Write-Host "   [OK] Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Frontend dependencies NOT installed" -ForegroundColor Red
    Write-Host "   Run: cd frontend && npm install" -ForegroundColor Yellow
}

# Check if backend can start
Write-Host ""
Write-Host "5. Quick backend test..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   [OK] Backend is running" -ForegroundColor Green
    }
} catch {
    Write-Host "   [INFO] Backend is not running (this is OK if you haven't started it)" -ForegroundColor Yellow
    Write-Host "   Start with: .\start_backend.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Check Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. If venv not active: .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  2. Start backend: .\start_backend.ps1" -ForegroundColor Gray
Write-Host "  3. Start frontend: cd frontend && npm run dev" -ForegroundColor Gray
