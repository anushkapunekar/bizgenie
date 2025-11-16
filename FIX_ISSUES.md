# Fix Guide - Current Issues

## ✅ Good News: Database is Working!

Your database has:
- ✅ 2 businesses saved
- ✅ 2 documents saved
- ✅ All tables exist

The data IS being saved! The issues are in the frontend display.

---

## Issue 1: Documents Not Showing in Frontend

### Problem:
Documents are saved but not visible in the UI.

### Solution:

1. **Check Browser Console:**
   - Press F12 → Console tab
   - Look for "Documents loaded:" log
   - Check for any errors

2. **Test API Directly:**
   ```powershell
   # Replace 1 with your business ID
   Invoke-RestMethod -Uri "http://localhost:8000/business/1/documents" -Method Get
   ```
   
   Should return an array of documents.

3. **Force Refresh:**
   - Hard refresh: Ctrl+Shift+R
   - Or clear browser cache

4. **Check Business ID:**
   - Make sure you're viewing the correct business
   - URL should be: `http://localhost:3000/business/1` (or your business ID)

---

## Issue 2: Chat Messages Invisible

### Problem:
Messages are sent but not visible.

### Solution:

1. **Check Browser Console:**
   - Press F12 → Console tab
   - Look for "Rendering message:" logs
   - Check for React errors

2. **Check Network Tab:**
   - Press F12 → Network tab
   - Send a message
   - Check if `/chat/` request succeeds
   - Check response status (should be 200)

3. **Check CSS:**
   - Messages might be there but invisible
   - Try inspecting element (F12 → Elements)
   - Look for message divs

4. **Clear Browser Cache:**
   - Hard refresh: Ctrl+Shift+R
   - Or clear cache completely

---

## Issue 3: Business Disappears After Refresh

### Problem:
Business data not showing after page refresh.

### Solution:

1. **Check Business ID in URL:**
   - After registration, note the business ID from URL
   - Example: `http://localhost:3000/business/1`
   - Use this exact URL after refresh

2. **Test API:**
   ```powershell
   # Test getting business
   Invoke-RestMethod -Uri "http://localhost:8000/business/1" -Method Get
   ```
   
   Should return business data.

3. **Check Database:**
   ```powershell
   python check_database.py
   ```
   
   Should show businesses count > 0

4. **Verify Business Exists:**
   - Go to: http://localhost:8000/docs
   - Try GET `/business/{id}` endpoint
   - Should return your business

---

## Quick Fixes to Try

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

### Fix 2: Clear Browser Data
- Press Ctrl+Shift+Delete
- Clear cache and cookies
- Restart browser

### Fix 3: Check API Responses
```powershell
# Test all endpoints
curl http://localhost:8000/health
curl http://localhost:8000/business/1
curl http://localhost:8000/business/1/documents
```

### Fix 4: Check Frontend Console
- Open browser DevTools (F12)
- Check Console for errors
- Check Network tab for failed requests

---

## Debugging Steps

### Step 1: Verify Backend
```powershell
python check_database.py
```

Should show:
- [OK] Database connected
- [OK] All required tables exist
- Businesses in database: X
- Documents in database: X

### Step 2: Test API Endpoints

**Business:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/business/1" -Method Get | ConvertTo-Json
```

**Documents:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/business/1/documents" -Method Get | ConvertTo-Json
```

**Chat:**
```powershell
$body = @{
    business_id = 1
    user_name = "Test"
    user_message = "Hello"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat/" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json
```

### Step 3: Check Frontend

1. Open: http://localhost:3000
2. Open DevTools (F12)
3. Go to Console tab
4. Try the actions:
   - View business dashboard
   - Upload document
   - Send chat message
5. Look for:
   - Console logs (should see API calls)
   - Error messages
   - Network requests

---

## What I Fixed in Code

1. **Database Initialization:**
   - Added model imports to ensure tables are created
   - Fixed `init_db()` function

2. **Document Loading:**
   - Added console logging
   - Better error handling

3. **Chat Messages:**
   - Added console logging for debugging
   - Fixed message rendering
   - Added min-height to message container

4. **Error Handling:**
   - Better error messages
   - More detailed logging

---

## Next Steps

1. **Restart both servers** (backend and frontend)
2. **Clear browser cache** (Ctrl+Shift+R)
3. **Test each feature:**
   - View business dashboard
   - Check documents list
   - Try chat interface
4. **Check browser console** for any errors
5. **Report back** what you see

---

## If Still Not Working

Share:
1. Browser console errors (F12 → Console)
2. Network tab errors (F12 → Network)
3. Backend terminal output
4. What you see vs what you expect

The database is working, so the issues are likely:
- Frontend not fetching data correctly
- API responses not being handled
- CSS/rendering issues
- Browser cache issues

