# BizGenie Frontend

Modern React + TypeScript frontend for the BizGenie AI business assistant platform.

## 🚀 Features

- **Business Registration**: Register and manage business profiles
- **AI Chat Interface**: Real-time chat with the LangGraph-powered AI agent
- **Document Management**: Upload and manage PDF documents for RAG
- **Responsive Design**: Beautiful, modern UI with Tailwind CSS
- **Type-Safe**: Full TypeScript support

## 📋 Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running on `http://localhost:8000` (or configure via env)

## 🛠️ Installation

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

3. **Create environment file** (optional):
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` if you need to change the API URL:
   ```
   VITE_API_URL=http://localhost:8000
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── Layout.tsx
│   │   └── DocumentUpload.tsx
│   ├── pages/            # Page components
│   │   ├── Home.tsx
│   │   ├── BusinessRegister.tsx
│   │   ├── BusinessDashboard.tsx
│   │   └── Chat.tsx
│   ├── services/         # API services
│   │   └── api.ts
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

## 🎨 Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **Lucide React** - Icon library

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🌐 API Integration

The frontend communicates with the FastAPI backend through the `api.ts` service layer. All API calls are configured to proxy through Vite's dev server:

- Development: `/api/*` → `http://localhost:8000/*`
- Production: Configure `VITE_API_URL` environment variable

## 📱 Pages

### Home (`/`)
Landing page with features overview and getting started guide.

### Register Business (`/register`)
Form to register a new business with:
- Basic information (name, description)
- Services list
- Working hours
- Contact information

### Business Dashboard (`/business/:id`)
View and manage business:
- Business details
- Services and contact info
- Working hours
- Document list
- Quick actions (upload, chat)

### Chat (`/business/:id/chat`)
AI chat interface:
- Real-time messaging
- Conversation history
- Intent display
- User name collection

## 🎯 Key Features

### Document Upload
- Drag-and-drop or click to upload
- PDF file validation
- File size limits (10MB)
- Automatic RAG ingestion

### Chat Interface
- Real-time message exchange
- Loading states
- Error handling
- Intent classification display
- Conversation ID tracking

### Responsive Design
- Mobile-friendly layout
- Adaptive grid systems
- Touch-friendly interactions

## 🔒 Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## 🚢 Production Build

1. **Build the project**:
   ```bash
   npm run build
   ```

2. **Preview the build**:
   ```bash
   npm run preview
   ```

3. **Deploy**: The `dist/` folder contains the production-ready files.

## 🐛 Troubleshooting

### CORS Issues
- Ensure the backend CORS middleware allows your frontend origin
- Check that `VITE_API_URL` matches your backend URL

### API Connection Errors
- Verify the backend is running on the configured port
- Check browser console for detailed error messages
- Ensure network connectivity

### Build Errors
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## 📝 Development Notes

- The frontend uses Vite's proxy feature in development to avoid CORS issues
- All API calls are centralized in `src/services/api.ts`
- Type definitions match the backend Pydantic schemas
- Components are organized by feature/page

## 🤝 Contributing

This frontend is part of the BizGenie project. See the main README for contribution guidelines.

---

**Built with**: React, TypeScript, Vite, Tailwind CSS

