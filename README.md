# 🤖 AI Personal Agent Workspace

> A full-stack, production-ready AI productivity platform — featuring an autonomous chat agent, intelligent task extraction, email sync, RAG-powered code & document intelligence, all wrapped in a sleek glassmorphism UI.

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16.2-black?style=for-the-badge&logo=next.js" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=for-the-badge&logo=openai" />
  <img src="https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6B35?style=for-the-badge" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript" />
</p>

---

## 🚀 What This Does

This isn't a simple chatbot. It's a **multi-agent AI workspace** that integrates with your email, your codebases, and your personal documents — then lets you talk to all of it through a single sleek interface.

| Module | What It Does |
|--------|-------------|
| 💬 **Chat Agent** | Conversational AI that automatically extracts and saves actionable tasks from your messages |
| ✅ **Task Manager** | Priority-aware task board populated by AI — from chat *and* your inbox |
| 📧 **Email Sync** | Connects to Gmail via IMAP, reads unread mail, and uses GPT to extract meetings & action items |
| 🗄️ **Repo Intelligence** | Clones any GitHub repo, embeds it into a vector store, and lets you query the codebase in plain English |
| 📚 **Personal Knowledge** | Upload PDFs or markdown docs and chat with them using semantic search + RAG |

---

## 🧠 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js 16 Frontend                     │
│  React 19 · TypeScript · Tailwind CSS v4 · Glassmorphism    │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                          │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Auth    │  │  Agent   │  │  Email   │  │   RAG    │     │
│  │  JWT +   │  │  GPT-4o  │  │  IMAP +  │  │ChromaDB  │     │
│  │  bcrypt  │  │  mini    │  │  OpenAI  │  │Embeddings│     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                             │
│              SQLAlchemy ORM · SQLite                        │
└─────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          OpenAI API   ChromaDB    Gmail IMAP
        (GPT + Embeds) (Vectors)  (Email Sync)
```

---

## 🛠️ Tech Stack

### Backend — Python
| Technology | Usage |
|---|---|
| **FastAPI** | Async REST API framework with auto-generated OpenAPI docs |
| **SQLAlchemy** | ORM for relational data (Users, Messages, Tasks) |
| **SQLite** | Embedded DB — zero-config persistence |
| **python-jose** | JWT token generation & validation |
| **passlib + bcrypt** | Secure password hashing |
| **OpenAI SDK (async)** | GPT-4o-mini for chat, email analysis, and RAG Q&A |
| **OpenAI Embeddings** | `text-embedding-3-small` for semantic vector search |
| **ChromaDB** | Persistent local vector database for similarity search |
| **GitPython** | Programmatic git clone for repo ingestion |
| **PyPDF2** | PDF text extraction for the knowledge base |
| **imaplib** | Native IMAP client for Gmail inbox sync |
| **uvicorn** | ASGI server for production-grade async serving |

### Frontend — TypeScript / React
| Technology | Usage |
|---|---|
| **Next.js 16.2** | App Router, SSR/CSR hybrid, optimised bundling |
| **React 19** | Latest concurrent features + hooks |
| **TypeScript 5** | Full type safety across all components |
| **Tailwind CSS v4** | Utility-first styling with PostCSS pipeline |
| **react-markdown** | Safe markdown rendering for AI responses with code blocks |
| **Lucide React** | Crisp, consistent icon set |
| **CSS Glassmorphism** | Custom `backdrop-filter` design system with CSS variables |

### AI / ML Pipeline
| Concept | Implementation |
|---|---|
| **RAG (Retrieval-Augmented Generation)** | Embed → Store in ChromaDB → Retrieve top-k → Prompt GPT |
| **Semantic Search** | `text-embedding-3-small` + cosine similarity via ChromaDB |
| **Structured JSON outputs** | `response_format: json_object` for reliable task extraction |
| **In-memory caching** | Query-level cache to reduce API costs on repeated questions |
| **Chunking strategy** | Fixed-size chunking (1500 chars) with source metadata for attribution |

---

## ✨ Features Deep-Dive

### 🔐 Authentication System
- Stateless **JWT bearer token** auth with 30-minute expiry
- **bcrypt** password hashing via passlib
- Per-user data isolation — every message, task, and conversation is scoped to the authenticated user
- OAuth2PasswordBearer compatible flow for standard tooling support

### 💬 Conversational AI Agent
- Maintains a **rolling 5-message context window** for coherent multi-turn conversations
- Every response is parsed as structured JSON: `{ reply, tasks[] }` — the agent extracts actionable items *automatically* while responding naturally
- Falls back to mock responses gracefully when no API key is configured

### 📧 Email Intelligence
- Authenticates to **Gmail via IMAP SSL** using app passwords
- Fetches up to 10 recent **unread emails**, truncates bodies to 2000 chars for token efficiency
- GPT classifies each email: meeting invite → `High` priority task; action item → task; newsletter → ignored
- Handles multipart MIME emails, strips attachments, decodes headers safely

### 🗄️ Repository Intelligence (Code RAG)
- Clones any **public GitHub repo** to a temp directory via GitPython
- Walks the directory tree, filtering to meaningful file types: `.py .js .jsx .ts .tsx .md .html .css`
- Chunks files at 4000 characters, embeds with OpenAI, upserts into **ChromaDB** with file path metadata
- Answers natural language questions grounded strictly in the indexed code context
- Query cache prevents redundant API calls for repeated questions

### 📚 Personal Knowledge Base (Document RAG)
- Accepts **PDF and plain text / Markdown** uploads via multipart form
- Extracts text page-by-page from PDFs using PyPDF2
- Chunks at 1500 characters with source filename metadata
- Semantic retrieval of top-5 relevant chunks → GPT synthesizes a grounded answer
- Separate ChromaDB collection from repo index, with cache invalidation on new uploads

### 🎨 UI / UX
- **Glassmorphism design system** with CSS variables, `backdrop-filter`, and layered radial gradients
- Smooth **fade-in animations** on messages with cubic-bezier easing
- AI typing indicator with animated dots
- Module-based sidebar navigation with active state highlighting
- Priority badges with colour-coded severity (red / amber / blue)
- Custom scrollbar styling; responsive chat container with auto-scroll

---

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py          # FastAPI app, all route definitions
│   ├── agent.py         # OpenAI chat agent + task extraction
│   ├── auth.py          # JWT auth, password hashing, user guards
│   ├── database.py      # SQLAlchemy engine + session factory
│   ├── models.py        # User, Message, Task ORM models
│   ├── email_sync.py    # IMAP email fetch + AI task extraction
│   ├── rag.py           # Git repo clone, embed, query pipeline
│   └── knowledge.py     # Document upload, embed, RAG query
│
└── frontend/
    └── src/app/
        ├── page.tsx     # Main SPA — auth, chat, tasks, RAG modules
        ├── layout.tsx   # Root layout with font optimisation
        └── globals.css  # Design system, glassmorphism utilities
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- *(Optional)* Gmail app password for email sync

### Backend

```bash
cd backend
pip install fastapi uvicorn sqlalchemy python-jose passlib openai chromadb pypdf2 gitpython python-dotenv
```

Create a `.env` file:
```env
OPENAI_API_KEY=sk-...
EMAIL_ADDRESS=you@gmail.com        # optional
EMAIL_APP_PASSWORD=xxxx xxxx xxxx  # optional — Gmail App Password
```

```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — sign up, and start building.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/signup` | Register a new user |
| `POST` | `/token` | Login → returns JWT |
| `POST` | `/chat` | Send message, get AI reply + auto-extracted tasks |
| `GET` | `/history` | Fetch full conversation history |
| `POST` | `/history/clear` | Wipe conversation memory |
| `GET` | `/tasks` | List all tasks for authenticated user |
| `PUT` | `/tasks/{id}` | Update task status (Open / Done) |
| `POST` | `/tasks/sync-email` | Trigger Gmail inbox scan → task extraction |
| `POST` | `/repo/index` | Clone & embed a GitHub repository |
| `POST` | `/repo/query` | Ask a question against indexed repo |
| `POST` | `/knowledge/upload` | Upload & index a PDF or text document |
| `POST` | `/knowledge/query` | Query your personal knowledge base |

Interactive API docs available at [http://localhost:8000/docs](http://localhost:8000/docs) (FastAPI auto-generated Swagger UI).

---

## 🔒 Security Notes

- Passwords are **never stored in plaintext** — bcrypt hashing with automatic salt
- All protected routes require a valid JWT bearer token
- Per-user DB queries prevent cross-user data leakage
- `SECRET_KEY` should be moved to environment variable in production (currently hardcoded placeholder)
- Email credentials are read exclusively from `.env` — never committed

---

## 🗺️ Roadmap

- [ ] Streaming AI responses (Server-Sent Events)
- [ ] Multi-file knowledge base management UI
- [ ] Google Calendar integration for meeting task auto-scheduling
- [ ] Webhook support for real-time email push (replace IMAP polling)
- [ ] Docker Compose setup for one-command deployment
- [ ] PostgreSQL migration for production scalability

---

## 📄 License

MIT — free to use, fork, and build upon.

---

<p align="center">Built with FastAPI · Next.js · OpenAI · ChromaDB</p>
