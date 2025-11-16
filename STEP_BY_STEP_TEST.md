# Step-by-Step Testing Guide - BizGenie

Follow these steps to test your entire BizGenie application.

## 🚀 Quick Start

### Step 1: Start Both Servers

**Terminal 1 - Backend:**
```powershell
.\start_backend.ps1
```
Wait until you see: `Uvicorn running on http://127.0.0.1:8000`

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```
Wait until you see: `Local: http://localhost:3000`

---

## 📝 Complete Testing Flow

### Test 1: Verify Servers are Running

**Backend Check:**
- Open: http://localhost:8000/health
- ✅ Should see: `{"status":"healthy"}`

**Frontend Check:**
- Open: http://localhost:3000
- ✅ Should see BizGenie homepage

---

### Test 2: Register a Business (Frontend)

1. **Go to Registration Page:**
   - Click "Register Business" button
   - Or go to: http://localhost:3000/register

2. **Fill in the Form:**

   ```
   Business Name: Acme Consulting
   
   Description: 
   Professional consulting services for small businesses. 
   We help companies grow and succeed.
   
   Services (click "Add Service" for each):
   - Business Strategy
   - Financial Planning  
   - Marketing Consulting
   
   Working Hours:
   Monday:    09:00 to 17:00
   Tuesday:   09:00 to 17:00
   Wednesday: 09:00 to 17:00
   Thursday:  09:00 to 17:00
   Friday:    09:00 to 17:00
   
   Contact Email: contact@acmeconsulting.com
   Contact Phone: +1-555-0123
   ```

3. **Click "Register Business"**

4. **✅ Expected Result:**
   - Redirected to business dashboard
   - See all your business information displayed
   - Note the URL: `http://localhost:3000/business/1` (or similar ID)

---

### Test 3: View Business Dashboard

You should see:

✅ **Header Section:**
- Business name: "Acme Consulting"
- Description
- "Start Chat" button

✅ **Quick Actions:**
- "Upload Documents" card
- "Chat with AI" card

✅ **Business Details:**
- Services as colored badges
- Contact information (email, phone)
- Working hours table

✅ **Documents Section:**
- Currently empty (we'll add one next)

---

### Test 4: Upload a Document

1. **Click "Upload Documents"** on the dashboard

2. **Upload a PDF:**
   - Click the upload area
   - Select any PDF file from your computer
   - Click "Upload"
   - Wait for upload to complete

3. **✅ Expected Result:**
   - Document appears in the documents list
   - Shows filename and upload date
   - Document is now available for AI queries

**💡 Tip:** You can use any PDF - even a simple text document saved as PDF works!

---

### Test 5: Test AI Chat Interface

1. **Start Chat:**
   - Click "Start Chat" button
   - Or go to: http://localhost:3000/business/1/chat (use your business ID)

2. **Enter Your Name:**
   - Type your name (e.g., "John Doe")
   - Press Enter

3. **Test Different Queries:**

   **Query 1: Services**
   ```
   You: What services do you offer?
   ```
   **Expected:** AI lists all your registered services

   **Query 2: Working Hours**
   ```
   You: What are your working hours?
   ```
   **Expected:** AI shows your configured working hours

   **Query 3: Contact Info**
   ```
   You: How can I contact you?
   ```
   **Expected:** AI provides email and phone number

   **Query 4: General Business Info**
   ```
   You: Tell me about your business
   ```
   **Expected:** AI gives a summary using your business data

   **Query 5: Document Query (if you uploaded a PDF)**
   ```
   You: What information do you have in your documents?
   ```
   **Expected:** AI searches your uploaded document and provides relevant info

   **Query 6: Appointment**
   ```
   You: I'd like to schedule an appointment
   ```
   **Expected:** AI checks availability and suggests time slots

4. **✅ Check Intent Classification:**
   - Look below each AI response
   - Should see: "Intent: faq" or "Intent: rag" etc.

---

### Test 6: Verify Conversation Flow

1. **Continue the Conversation:**
   - Send multiple messages
   - Check that conversation context is maintained
   - Verify conversation_id persists

2. **✅ Expected:**
   - All messages appear in chat history
   - AI responds contextually
   - Intent is shown for each response

---

## 🎯 Complete Example Scenario

Here's a full example conversation to test:

```
1. You: Hi, I'm interested in your services
   AI: Hello! I'd be happy to help. What would you like to know?
      Intent: faq

2. You: What services do you offer?
   AI: Acme Consulting offers the following services:
       - Business Strategy
       - Financial Planning
       - Marketing Consulting
      Intent: faq

3. You: What are your working hours?
   AI: Our working hours are:
       Monday to Friday: 9:00 AM to 5:00 PM
      Intent: faq

4. You: Can you tell me more about your company?
   AI: [Uses RAG to search uploaded documents if available]
      Intent: rag

5. You: I'd like to schedule a consultation
   AI: I'd be happy to help you schedule a consultation...
      Intent: appointment
```

---

## ✅ Success Checklist

After completing all tests, verify:

- [ ] Backend health check works
- [ ] Frontend loads correctly
- [ ] Business registration form works
- [ ] Business dashboard displays all information
- [ ] Document upload works
- [ ] Document appears in list
- [ ] Chat interface loads
- [ ] Can enter name and start chatting
- [ ] AI responds to FAQ queries
- [ ] AI responds to RAG queries (if document uploaded)
- [ ] Intent classification displays correctly
- [ ] Conversation persists across messages
- [ ] All information from registration is accessible to AI

---

## 🔧 Troubleshooting

### Chat returns generic responses
- **Check:** LLM configuration in `.env`
- **Solution:** Make sure `LLM_PROVIDER` is set (ollama or huggingface)
- **For Ollama:** Run `ollama serve` in a separate terminal

### RAG queries don't work
- **Check:** Document was uploaded successfully
- **Solution:** Verify document appears in dashboard
- **Note:** RAG needs documents to be uploaded first

### Frontend can't connect
- **Check:** Backend is running on port 8000
- **Check:** Browser console for errors
- **Solution:** Verify both servers are running

### Registration fails
- **Check:** Backend is running
- **Check:** Database connection in `.env`
- **Solution:** Verify `DATABASE_URL` is correct

---

## 📊 What to Look For

### Good Signs ✅
- Fast response times
- Accurate business information in responses
- Intent classification working
- Documents being used in RAG queries
- Smooth UI interactions

### Issues to Watch For ⚠️
- Slow responses (might need better LLM)
- Generic responses (LLM not configured)
- Errors in browser console
- Database connection errors
- Document upload failures

---

## 🎉 Next Steps After Testing

Once everything works:

1. **Customize Your Business:**
   - Update services
   - Add more contact information
   - Adjust working hours

2. **Add More Documents:**
   - Upload company brochures
   - Add service descriptions
   - Include FAQ documents

3. **Test with Real Scenarios:**
   - Try different types of customer queries
   - Test edge cases
   - Monitor conversation quality

4. **Configure LLM:**
   - Set up Ollama with better models
   - Or configure Hugging Face API
   - Adjust response parameters

---

## 🚀 Quick Test Script

Run this automated test:

```powershell
.\quick_test.ps1
```

This will:
- Check backend health
- Register a test business
- Test chat endpoint
- Verify frontend accessibility

---

**Happy Testing! Your BizGenie is ready to go! 🎊**

