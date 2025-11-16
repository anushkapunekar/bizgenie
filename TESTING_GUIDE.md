# BizGenie - Complete Testing Guide

This guide will walk you through testing the entire BizGenie application from start to finish.

## Prerequisites

✅ Backend is running on `http://localhost:8000`  
✅ Frontend is running on `http://localhost:3000`  
✅ Database is configured and connected

---

## Step-by-Step Testing Guide

### Step 1: Verify Backend is Running

**Check 1: Health Endpoint**
- Open browser: http://localhost:8000/health
- Should see: `{"status":"healthy"}`

**Check 2: API Documentation**
- Open browser: http://localhost:8000/docs
- Should see Swagger UI with all available endpoints

**Check 3: Root Endpoint**
- Open browser: http://localhost:8000/
- Should see: `{"message":"Welcome to BizGenie API","version":"1.0.0","docs":"/docs"}`

---

### Step 2: Test Frontend Homepage

1. Open browser: http://localhost:3000
2. You should see:
   - BizGenie logo and welcome message
   - Features grid (AI Chat Agent, Document Q&A, Appointments, MCP Tools)
   - "How It Works" section
   - "Get Started" button

---

### Step 3: Register a Business

**Via Frontend (Recommended):**

1. Click "Register Business" button or navigate to http://localhost:3000/register
2. Fill in the form:

   **Example Business Data:**
   ```
   Business Name: Acme Consulting
   Description: Professional consulting services for small businesses
   
   Services (click "Add Service" for each):
   - Business Strategy
   - Financial Planning
   - Marketing Consulting
   
   Working Hours:
   Monday: 09:00 to 17:00
   Tuesday: 09:00 to 17:00
   Wednesday: 09:00 to 17:00
   Thursday: 09:00 to 17:00
   Friday: 09:00 to 17:00
   
   Contact Email: contact@acmeconsulting.com
   Contact Phone: +1-555-0123
   ```

3. Click "Register Business"
4. You should be redirected to the business dashboard

**Via API (Alternative):**

```powershell
# Using PowerShell
$body = @{
    name = "Acme Consulting"
    description = "Professional consulting services"
    services = @("Business Strategy", "Financial Planning", "Marketing Consulting")
    working_hours = @{
        monday = @{ open = "09:00"; close = "17:00" }
        tuesday = @{ open = "09:00"; close = "17:00" }
        wednesday = @{ open = "09:00"; close = "17:00" }
        thursday = @{ open = "09:00"; close = "17:00" }
        friday = @{ open = "09:00"; close = "17:00" }
    }
    contact_email = "contact@acmeconsulting.com"
    contact_phone = "+1-555-0123"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/business/register" -Method Post -Body $body -ContentType "application/json"
```

**Expected Result:**
- Business is created successfully
- You see the business dashboard with all details
- Note the `business_id` (you'll need it for chat)

---

### Step 4: View Business Dashboard

After registration, you should see:

1. **Business Header:**
   - Business name
   - Description
   - "Start Chat" button

2. **Quick Actions:**
   - Upload Documents button
   - Chat with AI button

3. **Business Details:**
   - Services listed as badges
   - Contact information (email, phone)
   - Working hours table

4. **Documents Section:**
   - Currently empty (we'll add documents next)

---

### Step 5: Upload a Document (PDF)

**Via Frontend:**

1. On the business dashboard, click "Upload Documents"
2. Click the upload area or drag & drop a PDF file
3. Select a PDF file (any PDF will work for testing)
4. Click "Upload"
5. Wait for upload to complete
6. The document should appear in the documents list

**What Happens Behind the Scenes:**
- File is saved to local storage
- PDF text is extracted
- Text is chunked and embedded
- Chunks are stored in ChromaDB vector store
- Document is now available for RAG queries

**Via API (Alternative):**

```powershell
# Replace BUSINESS_ID with your actual business ID
$businessId = 1
$filePath = "C:\path\to\your\document.pdf"

$formData = @{
    file = Get-Item $filePath
}

Invoke-RestMethod -Uri "http://localhost:8000/business/upload-docs?business_id=$businessId" -Method Post -Form $formData
```

**Expected Result:**
- Document appears in the documents list
- Upload success message
- Document is ready for AI queries

---

### Step 6: Test AI Chat Interface

**Via Frontend:**

1. Click "Start Chat" button on the business dashboard
2. Or navigate to: http://localhost:3000/business/{business_id}/chat
3. Enter your name when prompted (e.g., "John Doe")
4. Start chatting! Try these examples:

**Example 1: FAQ Query**
```
User: What services do you offer?
```
**Expected:** AI responds with the business services from the registered data

**Example 2: Working Hours Query**
```
User: What are your working hours?
```
**Expected:** AI responds with the working hours you configured

**Example 3: Contact Information**
```
User: How can I contact you?
```
**Expected:** AI responds with email and phone number

**Example 4: RAG Query (if you uploaded a document)**
```
User: What is mentioned in your documents about [topic from your PDF]?
```
**Expected:** AI searches the uploaded documents and provides relevant information

**Example 5: Appointment Request**
```
User: I'd like to schedule an appointment
```
**Expected:** AI checks availability and suggests time slots

**Example 6: General Query**
```
User: Tell me about your business
```
**Expected:** AI provides a summary using business information

**Via API (Alternative):**

```powershell
$chatRequest = @{
    business_id = 1  # Replace with your business ID
    user_name = "John Doe"
    user_message = "What services do you offer?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat/" -Method Post -Body $chatRequest -ContentType "application/json"
```

**Expected Response:**
```json
{
  "reply": "Acme Consulting offers the following services: Business Strategy, Financial Planning, and Marketing Consulting...",
  "tool_actions": [],
  "conversation_id": "conv_1_...",
  "intent": "faq"
}
```

---

### Step 7: Test Different Intent Types

The AI agent classifies intents automatically. Test each type:

**FAQ Intent:**
```
"What is your phone number?"
"What services do you provide?"
"What are your hours?"
```

**RAG Intent (Document Q&A):**
```
"Tell me about [something from your uploaded document]"
"What does your documentation say about [topic]?"
```

**Appointment Intent:**
```
"I want to schedule an appointment"
"When are you available?"
"Can I book a consultation?"
```

**Tools Intent:**
```
"Send me an email"
"Contact me via WhatsApp"
```

---

### Step 8: Verify Conversation Flow

1. **Start a conversation:**
   - Enter your name
   - Send first message

2. **Continue the conversation:**
   - Send follow-up messages
   - Check that conversation_id persists
   - Verify context is maintained

3. **Check Intent Classification:**
   - Look at the intent displayed below AI responses
   - Should show: "faq", "rag", "appointment", or "tools"

---

### Step 9: Test Business Profile Update

**Via API:**

```powershell
$updateData = @{
    description = "Updated description: We now offer digital marketing services"
    services = @("Business Strategy", "Financial Planning", "Marketing Consulting", "Digital Marketing")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/business/update/1" -Method Patch -Body $updateData -ContentType "application/json"
```

**Expected:** Business profile is updated, changes reflect in dashboard

---

### Step 10: Test Document Retrieval

**Via API:**

```powershell
# Get all documents for a business
Invoke-RestMethod -Uri "http://localhost:8000/business/1/documents" -Method Get
```

**Expected:** Returns list of uploaded documents with metadata

---

## Complete Test Scenario

Here's a complete end-to-end test scenario:

### Scenario: Customer Journey

1. **Business Registration**
   - Register "Tech Solutions Inc"
   - Services: "Web Development", "Mobile Apps", "Consulting"
   - Hours: Mon-Fri 9am-6pm
   - Email: info@techsolutions.com

2. **Document Upload**
   - Upload a PDF with company information
   - Verify it appears in documents list

3. **Customer Chat Session**
   ```
   Customer: Hi, I'm interested in your services
   AI: Hello! I'd be happy to help. What would you like to know?
   
   Customer: What services do you offer?
   AI: [Lists services from registration]
   
   Customer: What are your working hours?
   AI: [Shows working hours]
   
   Customer: Can you tell me about your company?
   AI: [Uses RAG to answer from uploaded document]
   
   Customer: I'd like to schedule a consultation
   AI: [Checks availability and suggests time slots]
   ```

4. **Verify Lead Creation**
   - Check database or logs
   - Lead should be created automatically from first chat message

---

## Troubleshooting

### Issue: Chat returns generic responses
**Solution:** 
- Check LLM_PROVIDER in .env
- Verify Ollama is running: `ollama serve`
- Or configure Hugging Face API key

### Issue: RAG queries don't work
**Solution:**
- Verify document was uploaded successfully
- Check ChromaDB is accessible
- Verify embeddings model loaded correctly

### Issue: Frontend can't connect to backend
**Solution:**
- Check backend is running on port 8000
- Verify CORS settings in backend
- Check browser console for errors
- Verify VITE_API_URL in frontend .env

### Issue: Database errors
**Solution:**
- Verify DATABASE_URL in .env
- Check PostgreSQL is running
- Verify database exists

---

## Success Criteria

✅ Business registration works  
✅ Documents can be uploaded  
✅ Chat interface is responsive  
✅ AI responds with business context  
✅ RAG queries work (if documents uploaded)  
✅ Intent classification works  
✅ Conversation tracking works  
✅ All API endpoints respond correctly  

---

## Quick Test Checklist

- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Business registration form works
- [ ] Business dashboard displays correctly
- [ ] Document upload works
- [ ] Chat interface loads
- [ ] AI responds to messages
- [ ] FAQ queries work
- [ ] RAG queries work (if documents uploaded)
- [ ] Intent classification displays
- [ ] Conversation ID persists

---

## Next Steps After Testing

Once everything works:

1. **Customize Business Profile**
   - Add more services
   - Update working hours
   - Add more contact information

2. **Upload More Documents**
   - Add company brochures
   - Add service descriptions
   - Add FAQ documents

3. **Test with Real Customers**
   - Share chat link
   - Monitor conversations
   - Review leads generated

4. **Configure LLM**
   - Set up Ollama with better models
   - Or configure Hugging Face API
   - Adjust temperature and other parameters

---

**Happy Testing! 🚀**

