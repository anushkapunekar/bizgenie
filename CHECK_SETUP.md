# How to Check Your BizGenie Setup

## 1. Check if Virtual Environment is Activated

**In PowerShell:**
```powershell
# Check if venv is active - you should see (venv) in your prompt
# If not, activate it:
.\venv\Scripts\Activate.ps1
```

**In Command Prompt:**
```cmd
# Check if venv is active - you should see (venv) in your prompt
# If not, activate it:
venv\Scripts\activate.bat
```

**Verify Python path:**
```powershell
python --version
where python
# Should show: C:\Users\DELL\Desktop\bizgenie\venv\Scripts\python.exe
```

## 2. Check if Dependencies are Installed

**List installed packages:**
```powershell
pip list
```

**Check specific packages:**
```powershell
pip show sqlalchemy
pip show fastapi
pip show uvicorn
```

**Verify all requirements:**
```powershell
pip check
```

## 3. Check if Backend Starts Correctly

**Test import:**
```powershell
python -c "from app.main import app; print('✓ Backend imports successfully')"
```

**Start backend and check for errors:**
```powershell
uvicorn app.main:app --reload
```

**Look for:**
- ✓ "Uvicorn running on http://127.0.0.1:8000"
- ✓ "Application startup complete"
- ✗ Any "ModuleNotFoundError" means venv is not activated

## 4. Check Backend Health

**Once backend is running, test it:**

**In PowerShell (new terminal):**
```powershell
# Test health endpoint
curl http://localhost:8000/health

# Or use Invoke-WebRequest
Invoke-WebRequest -Uri http://localhost:8000/health
```

**In browser:**
- Open: http://localhost:8000/health
- Should return: `{"status":"healthy"}`

**Check API docs:**
- Open: http://localhost:8000/docs
- Should show Swagger UI

## 5. Check Frontend Setup

**Navigate to frontend:**
```powershell
cd frontend
```

**Check if node_modules exists:**
```powershell
Test-Path node_modules
# Should return: True
```

**Check if dependencies are installed:**
```powershell
npm list --depth=0
```

**Start frontend:**
```powershell
npm run dev
```

**Check frontend:**
- Open: http://localhost:3000
- Should show BizGenie homepage

## 6. Quick Health Check Script

Run this to check everything at once:

```powershell
Write-Host "=== BizGenie Setup Check ===" -ForegroundColor Cyan

# Check Python
Write-Host "`n1. Checking Python..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath -like "*venv*") {
    Write-Host "   ✓ Virtual environment is active" -ForegroundColor Green
    Write-Host "   Python: $pythonPath" -ForegroundColor Gray
} else {
    Write-Host "   ✗ Virtual environment NOT active" -ForegroundColor Red
    Write-Host "   Run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}

# Check key packages
Write-Host "`n2. Checking key packages..." -ForegroundColor Yellow
$packages = @("sqlalchemy", "fastapi", "uvicorn", "langgraph")
foreach ($pkg in $packages) {
    $result = pip show $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        $version = ($result | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host "   ✓ $pkg ($version)" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $pkg not found" -ForegroundColor Red
    }
}

# Check backend import
Write-Host "`n3. Testing backend import..." -ForegroundColor Yellow
try {
    python -c "from app.main import app; print('   ✓ Backend imports successfully')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Backend imports successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Backend import failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Backend import failed" -ForegroundColor Red
}

# Check frontend
Write-Host "`n4. Checking frontend..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Write-Host "   ✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ✗ Frontend dependencies NOT installed" -ForegroundColor Red
    Write-Host "   Run: cd frontend && npm install" -ForegroundColor Yellow
}

Write-Host "`n=== Check Complete ===" -ForegroundColor Cyan
```

## 7. Common Issues and Solutions

### Issue: "ModuleNotFoundError: No module named 'sqlalchemy'"
**Solution:** Virtual environment is not activated
```powershell
.\venv\Scripts\Activate.ps1
```

### Issue: "Command not found: uvicorn"
**Solution:** Install dependencies or activate venv
```powershell
pip install -r requirements.txt
```

### Issue: Backend starts but frontend can't connect
**Solution:** Check CORS settings and ensure backend is running on port 8000

### Issue: Frontend shows "Network Error"
**Solution:** 
1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend .env file has correct API URL
3. Check browser console for detailed errors

## 8. Verify Database Connection

**Check if PostgreSQL is accessible:**
```powershell
# If you have psql installed
psql -U postgres -c "SELECT version();"
```

**Check DATABASE_URL in .env:**
```powershell
Get-Content .env | Select-String "DATABASE_URL"
```

## 9. Test Full Stack

1. **Start Backend:**
   ```powershell
   .\start_backend.ps1
   ```

2. **Start Frontend (new terminal):**
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Test in Browser:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Try registering a business
   - Try uploading a document
   - Try chatting with the AI

