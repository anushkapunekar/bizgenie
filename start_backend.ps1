Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1
Write-Host "Starting BizGenie backend..." -ForegroundColor Green
uvicorn app.main:app --reload

