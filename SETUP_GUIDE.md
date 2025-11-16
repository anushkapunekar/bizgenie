# 🚀 BizGenie Environment Variables Setup Guide

This guide will help you configure all environment variables for BizGenie.

## 📋 Quick Start

1. **Copy the example file:**
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```

2. **Edit `.env` file** with your actual values (see details below)

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🔧 Environment Variables Explained

### 1. Database Configuration (REQUIRED)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/bizgenie
```

**How to set up:**
- Install PostgreSQL: https://www.postgresql.org/download/
- Create a database:
  ```sql
  CREATE DATABASE bizgenie;
  ```
- Replace `user`, `password`, `localhost`, `5432` with your PostgreSQL credentials
- Format: `postgresql://username:password@host:port/database_name`

**Example:**
```env
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/bizgenie
```

---

### 2. Free LLM Configuration (REQUIRED - Choose One)

#### Option A: Ollama (Recommended - Completely Free)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2
```

**Setup Steps:**
1. Install Ollama from https://ollama.ai
2. Download a model:
   ```bash
   ollama pull llama3.2
   # Or try: ollama pull mistral
   # Or try: ollama pull phi3
   ```
3. Start Ollama (usually runs automatically):
   ```bash
   ollama serve
   ```
4. Test it:
   ```bash
   ollama run llama3.2 "Hello"
   ```

**Available Models:**
- `llama3.2` - Fast, good quality (recommended)
- `mistral` - Great quality, multilingual
- `phi3` - Small, fast
- `gemma2` - Google's model

#### Option B: Hugging Face Inference API (Free Tier)

```env
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=your_hf_token_here
LLM_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

**Setup Steps:**
1. Create free account at https://huggingface.co
2. Go to https://huggingface.co/settings/tokens
3. Create a new token (read access is enough)
4. Copy token to `HUGGINGFACE_API_KEY`

**Free Models:**
- `mistralai/Mistral-7B-Instruct-v0.2`
- `meta-llama/Llama-2-7b-chat-hf`
- `google/flan-t5-large`

---

### 3. Embeddings Configuration (Optional - Has Default)

```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**Options:**
- `all-MiniLM-L6-v2` - Fast, good quality (default)
- `all-mpnet-base-v2` - Better quality, slower
- `paraphrase-MiniLM-L6-v2` - Good for similarity

**Note:** Models download automatically on first use (~80MB)

---

### 4. Document Storage (Optional)

#### Local Storage (Default - No Setup Needed)

```env
USE_LOCAL_STORAGE=true
LOCAL_STORAGE_PATH=./storage/documents
```

#### Supabase Storage (Optional)

```env
USE_LOCAL_STORAGE=false
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
SUPABASE_BUCKET=documents
```

**Setup Steps:**
1. Create account at https://supabase.com
2. Create a new project
3. Go to Storage → Create bucket named "documents"
4. Copy URL and anon key from Settings → API

---

### 5. Email Configuration (Optional - For Email Tool)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Go to https://myaccount.google.com/apppasswords
3. Generate an "App Password" for "Mail"
4. Use that password (not your regular password)

**Other Email Providers:**
- **Outlook:** `smtp-mail.outlook.com:587`
- **Yahoo:** `smtp.mail.yahoo.com:587`
- **Custom:** Use your provider's SMTP settings

---

### 6. WhatsApp Configuration (Optional - For WhatsApp Tool)

```env
WHATSAPP_API_URL=https://api.whatsapp.com/v1
WHATSAPP_API_TOKEN=your_whatsapp_token_here
```

**Note:** Currently placeholder. Integrate with:
- Twilio WhatsApp API
- WhatsApp Business API
- Or other WhatsApp service providers

---

### 7. Calendar Configuration (Optional - For Calendar Tool)

```env
CALENDAR_API_URL=https://api.calendar.com/v1
CALENDAR_API_TOKEN=your_calendar_token_here
```

**Note:** Currently uses database. Can integrate with:
- Google Calendar API
- Outlook Calendar API
- Cal.com API

---

### 8. Application Settings (Optional)

```env
LOG_LEVEL=INFO
ENVIRONMENT=development
CHROMA_PERSIST_DIR=./chroma_db
```

**Log Levels:**
- `DEBUG` - Most verbose
- `INFO` - Normal operation (default)
- `WARNING` - Warnings only
- `ERROR` - Errors only

---

## ✅ Complete Example `.env` File

```env
# Database (REQUIRED)
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/bizgenie

# LLM - Ollama (REQUIRED - Choose one)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2

# Embeddings (Optional - has default)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Storage (Optional - local is default)
USE_LOCAL_STORAGE=true
LOCAL_STORAGE_PATH=./storage/documents

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=myemail@gmail.com
SMTP_PASSWORD=my_app_password

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
CHROMA_PERSIST_DIR=./chroma_db
```

---

## 🧪 Testing Your Configuration

### Test Database Connection

```python
# In Python
from app.database import engine
engine.connect()  # Should work without error
```

### Test Ollama

```bash
ollama run llama3.2 "Hello, how are you?"
```

### Test Email (if configured)

```python
from app.tools.email_mcp import send_email
result = send_email("test@example.com", "Test", "This is a test")
print(result)
```

---

## 🐛 Troubleshooting

### Database Connection Error
- Check PostgreSQL is running: `pg_isready`
- Verify credentials in `DATABASE_URL`
- Ensure database exists: `psql -U postgres -c "CREATE DATABASE bizgenie;"`

### Ollama Not Working
- Check Ollama is running: `ollama list`
- Verify model is downloaded: `ollama list`
- Test manually: `ollama run llama3.2 "test"`

### Embeddings Model Download Issues
- First run downloads model (~80MB) - be patient
- Check internet connection
- Models are cached in `~/.cache/huggingface/`

### Email Not Sending
- Verify SMTP credentials
- Check firewall/network settings
- For Gmail, use App Password (not regular password)
- Try different SMTP port (465 for SSL)

---

## 📝 Notes

- **All values are optional except `DATABASE_URL` and LLM configuration**
- **Local storage works out of the box** - no setup needed
- **Ollama is recommended** for completely free, local operation
- **Environment variables are loaded from `.env` file automatically**
- **Never commit `.env` file to git** (it's in `.gitignore`)

---

## 🆘 Need Help?

If you encounter issues:
1. Check logs in console output
2. Verify all required variables are set
3. Test each service individually
4. Check the README.md for more details

