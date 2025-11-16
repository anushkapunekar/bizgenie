# Troubleshooting Guide - Chat & Document Upload Issues

## Issue 1: Chat Messages Disappear / Bot Not Working

### Symptoms:
- Messages disappear after sending
- No response from AI
- Chat history not showing

### Solutions:

#### 1. Check Backend is Running
```powershell
# Check if backend is accessible
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

**If not running:**
```powershell
.\start_backend.ps1
```

#### 2. Check Browser Console
- Open browser DevTools (F12)
- Go to Console tab
- Look for error messages
- Common errors:
  - `Network Error` → Backend not running
  - `CORS Error` → CORS configuration issue
  - `500 Internal Server Error` → Backend error

#### 3. Check LLM Configuration
The chat requires an LLM to be configured. Check your `.env` file:

```env
LLM_PROVIDER=ollama  # or "huggingface"
LLM_MODEL=llama3.2   # or your model name
```

**For Ollama:**
```powershell
# Check if Ollama is running
ollama serve

# In another terminal, test the model
ollama run llama3.2 "hello"
```

**For Hugging Face:**
- Make sure `HUGGINGFACE_API_KEY` is set in `.env`
- Or use free tier without API key

#### 4. Test Chat API Directly
```powershell
$chatRequest = @{
    business_id = 1  # Replace with your business ID
    user_name = "Test User"
    user_message = "Hello"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat/" -Method Post -Body $chatRequest -ContentType "application/json"
```

**Expected:** Should return a response with `reply`, `intent`, etc.

**If it fails:**
- Check backend logs for errors
- Verify database connection
- Check LLM service is working

#### 5. Check Network Tab
- Open DevTools → Network tab
- Send a chat message
- Look for the `/chat/` request
- Check:
  - Status code (should be 200)
  - Response body
  - Request payload

---

## Issue 2: Document Upload Disappears

### Symptoms:
- Document upload form disappears after clicking upload
- Document doesn't appear in list
- No error message shown

### Solutions:

#### 1. Check Backend Storage Path
The backend saves files to `./storage/documents` by default. Check:

```powershell
# Check if storage directory exists
Test-Path ".\storage\documents"

# If not, create it
New-Item -ItemType Directory -Path ".\storage\documents" -Force
```

#### 2. Check File Permissions
Make sure the backend has write permissions to the storage directory.

#### 3. Check Browser Console
- Open DevTools → Console
- Look for upload errors
- Check Network tab for the upload request

#### 4. Test Upload API Directly
```powershell
$businessId = 1  # Replace with your business ID
$filePath = "C:\path\to\test.pdf"  # Use a test PDF

$formData = @{
    file = Get-Item $filePath
}

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/business/upload-docs?business_id=$businessId" -Method Post -Form $formData
    Write-Host "Success: $($response | ConvertTo-Json)"
} catch {
    Write-Host "Error: $_"
    Write-Host "Status: $($_.Exception.Response.StatusCode)"
}
```

#### 5. Check Backend Logs
Look at the backend terminal for:
- File save errors
- Database errors
- RAG ingestion errors

#### 6. Verify Document in Database
```powershell
# Check documents endpoint
Invoke-RestMethod -Uri "http://localhost:8000/business/1/documents" -Method Get
```

Should return a list of documents.

#### 7. Check File Size
- Maximum file size: 10MB
- If file is larger, it will be rejected

---

## Common Error Messages

### "Failed to send message. Please check your connection"
**Cause:** Backend not accessible or network error
**Solution:**
1. Verify backend is running
2. Check `VITE_API_URL` in frontend `.env`
3. Check firewall/antivirus blocking connection

### "Internal server error"
**Cause:** Backend error (check backend logs)
**Solution:**
1. Check backend terminal for error details
2. Verify database connection
3. Check LLM configuration
4. Review backend logs

### "Business not found"
**Cause:** Invalid business ID
**Solution:**
1. Verify business exists
2. Check business ID in URL
3. Try registering a new business

### "Only PDF files are supported"
**Cause:** Wrong file type
**Solution:**
1. Ensure file is a PDF
2. Check file extension is `.pdf`

### "File size must be less than 10MB"
**Cause:** File too large
**Solution:**
1. Compress the PDF
2. Split into smaller files
3. Or increase limit in backend code

---

## Debugging Steps

### Step 1: Verify Backend
```powershell
# Health check
curl http://localhost:8000/health

# API docs
# Open: http://localhost:8000/docs
```

### Step 2: Check Frontend Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors when:
   - Sending chat message
   - Uploading document
   - Loading pages

### Step 3: Check Network Requests
1. Open DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Try the action (chat/upload)
4. Check:
   - Request URL
   - Request method
   - Status code
   - Response body

### Step 4: Check Backend Logs
Look at the backend terminal for:
- Request received
- Processing steps
- Errors or exceptions
- Response sent

### Step 5: Test API Directly
Use PowerShell or curl to test endpoints directly:
- Chat endpoint
- Upload endpoint
- Business endpoints

---

## Quick Fixes

### Fix 1: Restart Everything
```powershell
# Stop backend (Ctrl+C)
# Stop frontend (Ctrl+C)

# Restart backend
.\start_backend.ps1

# Restart frontend (new terminal)
cd frontend
npm run dev
```

### Fix 2: Clear Browser Cache
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Or clear browser cache

### Fix 3: Check Environment Variables
```powershell
# Backend .env
Get-Content .env

# Frontend .env
Get-Content frontend\.env
```

### Fix 4: Verify Database
```powershell
# Check DATABASE_URL in .env
# Test connection if possible
```

---

## Still Not Working?

1. **Check all logs:**
   - Backend terminal
   - Frontend console
   - Browser network tab

2. **Test with simple requests:**
   - Health endpoint
   - Business registration
   - Simple chat message

3. **Verify configuration:**
   - All environment variables set
   - Ports not blocked
   - Services running

4. **Check for updates:**
   - Dependencies installed
   - Code is latest version

---

## Getting Help

When asking for help, provide:
1. Error messages from console
2. Backend logs
3. Network request details
4. Steps to reproduce
5. Environment details (OS, Node version, Python version)

