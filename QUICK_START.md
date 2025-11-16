# ⚡ Quick Start Guide

## 🎯 Minimum Setup (Get Running in 5 Minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Database
```bash
# Install PostgreSQL, then create database
createdb bizgenie
# Or using psql:
psql -U postgres -c "CREATE DATABASE bizgenie;"
```

### Step 3: Install Ollama (Free LLM)
```bash
# Download from https://ollama.ai
# Then pull a model:
ollama pull llama3.2
```

### Step 4: Create .env File
```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

### Step 5: Edit .env (Minimum Required)
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/bizgenie
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

### Step 6: Run the App
```bash
uvicorn app.main:app --reload
```

### Step 7: Test It
- Open: http://localhost:8000/docs
- Try the `/business/register` endpoint
- Try the `/chat/` endpoint

---

## ✅ That's It!

For detailed configuration, see `SETUP_GUIDE.md`

---

## 🆘 Common Issues

**Database Error?**
- Make sure PostgreSQL is running
- Check your DATABASE_URL format

**Ollama Not Working?**
- Run: `ollama serve`
- Test: `ollama run llama3.2 "hello"`

**Import Errors?**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

