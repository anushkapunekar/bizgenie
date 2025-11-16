# Quick Test - Verify Fixes

## ✅ Step 1: Check Document Upload is Working

I can see you have a document uploaded: `1_9708a122-0c69-4ab9-b0e8-a3d328426d34.pdf`

**Test:**
1. Go to your business dashboard: http://localhost:3000/business/1
2. Scroll to "Documents" section
3. ✅ **Expected:** You should see your uploaded PDF in the list

If you see it, document upload is working! 🎉

---

## ✅ Step 2: Test Chat Interface

1. **Open Chat:**
   - Click "Start Chat" button
   - Or go to: http://localhost:3000/business/1/chat

2. **Enter Your Name:**
   - Type your name (e.g., "John")
   - Press Enter

3. **Send a Test Message:**
   ```
   What services do you offer?
   ```

4. **What to Check:**
   - ✅ Your message stays visible (doesn't disappear)
   - ✅ You see a loading indicator
   - ✅ You get a response from AI (or an error message)
   - ✅ Open browser console (F12) - should see API logs

5. **If You Get an Error:**
   - Check the error message shown in chat
   - Check browser console (F12) for details
   - Check backend terminal for errors

---

## ✅ Step 3: Test Document Upload Again (Optional)

If you want to test upload again:

1. Click "Upload Documents"
2. Select a PDF file
3. Click "Upload"
4. **Expected:**
   - ✅ See "Uploading..." indicator
   - ✅ See green success message: "✓ Document uploaded successfully!"
   - ✅ Success message stays for 1.5 seconds
   - ✅ Document appears in the list
   - ✅ Upload form closes automatically

---

## 🔍 What to Look For

### ✅ Good Signs:
- Messages stay in chat
- You see responses (or clear error messages)
- Documents appear in list
- Success messages show
- Console shows API calls

### ⚠️ Issues to Report:
- Messages still disappear
- No response from AI (check LLM config)
- Documents don't appear
- Error messages not clear
- Console shows errors

---

## 🐛 If Chat Still Doesn't Work

**Check 1: Backend is Running**
```powershell
curl http://localhost:8000/health
```

**Check 2: LLM is Configured**
- Check `.env` file has `LLM_PROVIDER` set
- If using Ollama: `ollama serve` should be running
- Test: `ollama run llama3.2 "hello"`

**Check 3: Browser Console**
- Press F12
- Go to Console tab
- Look for errors when sending message

**Check 4: Backend Logs**
- Look at backend terminal
- Should see chat requests being processed

---

## 📊 Quick Status Check

Run this to check everything:

```powershell
# Check backend
curl http://localhost:8000/health

# Check documents
Invoke-RestMethod -Uri "http://localhost:8000/business/1/documents" -Method Get
```

---

**Go ahead and test! Let me know what you see! 🚀**

