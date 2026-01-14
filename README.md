# BizGenie

A micro-SaaS small-business support AI agent built with FastAPI, LangGraph, and ChromaDB.

##  Features

- **AI-Powered Chat Agent**: LangGraph-based agent that intelligently routes and responds to customer queries
- **RAG (Retrieval-Augmented Generation)**: Document-based Q&A using ChromaDB vector store
- **MCP Tools Integration**: WhatsApp, Email, and Calendar scheduling tools
- **Business Management**: Register businesses, upload documents, manage profiles
- **PostgreSQL Database**: Robust data persistence with SQLAlchemy ORM
- **Document Storage**: Local storage or Supabase integration for document files

##  Project Structure

```
bizgenie/
│── app/                        # Backend (FastAPI)
│   ├── main.py                 # FastAPI application entry point
│   ├── schemas.py              # Pydantic schemas for validation
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── routes/
│   │   ├── chat.py             # Chat API endpoints
│   │   ├── business.py         # Business management endpoints
│   ├── agents/
│   │   ├── graph.py            # LangGraph agent definition
│   │   ├── nodes/
│   │   │   ├── classify.py     # Intent classification node
│   │   │   ├── rag.py          # RAG query node
│   │   │   ├── appointment.py  # Appointment scheduling node
│   │   │   ├── faq.py          # FAQ answering node
│   │   │   ├── tools_executor.py # MCP tools execution node
│   ├── tools/
│   │   ├── whatsapp_mcp.py     # WhatsApp MCP tool
│   │   ├── email_mcp.py        # Email MCP tool
│   │   ├── calendar_mcp.py     # Calendar/appointment MCP tool
│   ├── rag/
│   │   ├── vectorstore.py      # ChromaDB vector store wrapper
│   │   ├── ingest.py           # Document ingestion pipeline
│── frontend/                   # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API service layer
│   │   └── types/              # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│── requirements.txt
│── README.md
│── .env.example
```

##  Installation

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm/yarn/pnpm
- PostgreSQL database
- (Optional) Ollama for local LLM (recommended) OR Hugging Face account
- (Optional) Supabase account for document storage

### Backend Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   - `DATABASE_URL`: PostgreSQL connection string (REQUIRED)
   - `LLM_PROVIDER`: Choose "ollama" or "huggingface" (REQUIRED)
   - `LLM_MODEL`: Model name (e.g., "llama3.2" for Ollama)
   - `SMTP_*`: Email configuration (optional)
   - `WHATSAPP_API_*`: WhatsApp API configuration (optional)
   - See `SETUP_GUIDE.md` for detailed instructions

4. **Initialize the database**:
   ```bash
   # The database will be initialized automatically on startup
   # Or run migrations with Alembic (TODO: set up Alembic migrations)
   ```

5. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` if you need to change the API URL:
   ```
   VITE_API_URL=http://localhost:8000
   ```

4. **Run the frontend**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

### Quick Start (Both Backend & Frontend)

1. **Terminal 1 - Start Backend**:
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # Start FastAPI server
   uvicorn app.main:app --reload
   ```

2. **Terminal 2 - Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Open Browser**: Navigate to `http://localhost:3000`

## API Usage

### 1. Register a Business

```bash
POST /business/register
Content-Type: application/json

{
  "name": "Acme Consulting",
  "description": "Professional consulting services",
  "services": ["Consulting", "Strategy", "Analysis"],
  "working_hours": {
    "monday": {"open": "09:00", "close": "17:00"},
    "tuesday": {"open": "09:00", "close": "17:00"},
    "wednesday": {"open": "09:00", "close": "17:00"},
    "thursday": {"open": "09:00", "close": "17:00"},
    "friday": {"open": "09:00", "close": "17:00"}
  },
  "contact_email": "contact@acme.com",
  "contact_phone": "+1234567890"
}
```

### 2. Upload Documents

```bash
POST /business/upload-docs?business_id=1
Content-Type: multipart/form-data

file: [PDF file]
```

The document will be:
- Stored in local storage or Supabase
- Automatically ingested into the ChromaDB vector store
- Available for RAG queries

### 3. Chat with the Agent

```bash
POST /chat/
Content-Type: application/json

{
  "business_id": 1,
  "user_name": "John Doe",
  "user_message": "What services do you offer?",
  "conversation_id": "optional-conversation-id"
}
```

Response:
```json
{
  "reply": "Acme Consulting offers the following services: Consulting, Strategy, Analysis.",
  "tool_actions": [],
  "conversation_id": "conv_1_...",
  "intent": "faq"
}
```

### 4. Update Business Profile

```bash
PATCH /business/update/1
Content-Type: application/json

{
  "description": "Updated description",
  "services": ["Consulting", "Strategy", "Analysis", "Training"]
}
```

##  Agent Flow

The LangGraph agent follows this flow:

1. **Classify Node**: Determines user intent (FAQ, RAG, Appointment, Tools)
2. **Route to Node**:
   - **FAQ Node**: Answers simple questions from business context
   - **RAG Node**: Queries documents using ChromaDB vector search
   - **Appointment Node**: Checks availability and suggests time slots
   - **Tools Executor Node**: Executes MCP tools (WhatsApp, Email, Calendar)
3. **Response**: Returns formatted reply with any tool actions

##  Document Ingestion

Documents are processed as follows:

1. **Upload**: PDF files are uploaded via `/business/upload-docs`
2. **Storage**: Files are stored locally or in Supabase
3. **Text Extraction**: PDF text is extracted using PyPDF2
4. **Chunking**: Text is split into chunks (1000 chars, 200 overlap)
5. **Embedding**: Chunks are embedded and stored in ChromaDB
6. **Indexing**: Documents are indexed by business_id

### Ingesting Documents Programmatically

```python
from app.rag.ingest import ingest_document

ingest_document(
    business_id=1,
    file_path="./documents/brochure.pdf",
    filename="brochure.pdf",
    metadata={"category": "marketing"}
)
```

##  Database Schema

### Business
- `id`: Primary key
- `name`: Business name
- `description`: Business description
- `services`: JSON array of services
- `working_hours`: JSON object with day schedules
- `contact_email`, `contact_phone`: Contact information
- `created_at`, `updated_at`: Timestamps

### Document
- `id`: Primary key
- `business_id`: Foreign key to Business
- `filename`: Original filename
- `file_path`: Storage path/URL
- `file_type`: File type (default: "pdf")
- `metadata`: JSON metadata
- `created_at`: Timestamp

### Appointment
- `id`: Primary key
- `business_id`: Foreign key to Business
- `customer_name`, `customer_email`, `customer_phone`: Customer info
- `appointment_date`: Scheduled date/time
- `service`: Service type
- `status`: pending, confirmed, cancelled, completed
- `notes`: Additional notes

### Lead
- `id`: Primary key
- `business_id`: Foreign key to Business
- `name`, `email`, `phone`: Lead information
- `source`: Lead source (chat, website, etc.)
- `notes`: Lead notes
- `created_at`: Timestamp

## MCP Tools

### WhatsApp Tool
- **Function**: `send_whatsapp_message(to, message)`
- **Configuration**: Set `WHATSAPP_API_URL` and `WHATSAPP_API_TOKEN` in `.env`
- **Status**: Placeholder implementation (TODO: integrate with actual WhatsApp API)

### Email Tool
- **Function**: `send_email(to, subject, body)`
- **Configuration**: Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` in `.env`
- **Status**: Functional with SMTP

### Calendar Tool
- **Functions**: 
  - `get_available_slots(business_id, date, duration_minutes)`
  - `generate_appointment_confirmation(appointment_id)`
- **Status**: Functional with database integration

##  Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test business registration
curl -X POST http://localhost:8000/business/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Business", "services": ["Test"]}'

# Test chat
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"business_id": 1, "user_name": "Test User", "user_message": "Hello"}'
```

##  TODO / Future Enhancements

- [ ] Set up Alembic for database migrations
- [x] Use free embeddings (sentence-transformers) ✅
- [x] Use free LLM (Ollama/Hugging Face) ✅
- [ ] Implement actual WhatsApp API integration
- [ ] Add Supabase storage implementation
- [ ] Add authentication and authorization
- [ ] Implement conversation history persistence
- [ ] Add rate limiting
- [ ] Add comprehensive error handling and retries
- [ ] Add unit and integration tests
- [ ] Add Docker configuration
- [ ] Add CI/CD pipeline
- [ ] Improve intent classification with LLM
- [ ] Add support for more file types (docx, txt, etc.)
- [ ] Implement async email sending
- [ ] Add monitoring and logging dashboard

##  Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database exists: `CREATE DATABASE bizgenie;`

### ChromaDB Issues
- Check write permissions for `./chroma_db` directory
- Clear ChromaDB data if needed: `rm -rf ./chroma_db`

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

##  License

This project is provided as-is for development purposes.

##  Contributing

This is a template project. Feel free to customize and extend as needed.

---

**Built with**: 
- **Backend**: FastAPI, LangGraph, ChromaDB, PostgreSQL, SQLAlchemy
- **Frontend**: React, TypeScript, Vite, Tailwind CSS

