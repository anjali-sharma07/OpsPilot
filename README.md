# OpsPilot

OpsPilot is a lightweight document Q&A application that lets users upload PDFs, extract their contents, generate embeddings, and ask grounded questions over the uploaded documents.

## Project Overview

The project combines a FastAPI backend with a React frontend to deliver a simple RAG workflow:

1. Upload a PDF
2. Extract and chunk text
3. Generate embeddings and store them in ChromaDB
4. Retrieve relevant chunks for a user question
5. Generate a grounded answer with Groq
6. Preserve chat history in SQLite

## Features

- PDF upload and validation
- PDF text extraction
- Text chunking with overlap
- Embedding generation and local vector storage
- Semantic retrieval from uploaded documents
- Grounded answer generation with Groq
- Conversation memory per session
- Source attribution in responses
- Simple React UI for upload and chat

## Technology Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, Uvicorn
- AI/ML: sentence-transformers, ChromaDB, Groq
- PDF processing: PyMuPDF
- Frontend: React, Vite, Axios, Tailwind CSS

## Architecture Diagram

```text
User -> React UI -> FastAPI API
                    -> File Service
                    -> PDF Service
                    -> Chunking Service
                    -> Embedding Service -> ChromaDB
                    -> Retrieval Service
                    -> Groq Service
                    -> Conversation Service -> SQLite
```

## Folder Structure

```text
app/
  api/
  core/
  database/
  models/
  schemas/
  services/
src/
tests/
```

## API Endpoints

- POST /upload
  - Uploads a PDF and ingests it into the document store.
- POST /chat
  - Sends a question and returns an answer with sources.
- GET /health
  - Health check endpoint.

## Setup Instructions

### Backend

1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the environment example:
   ```bash
   copy .env.example .env
   ```
4. Fill in the required values in `.env`.
5. Start the backend:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

### Frontend

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the Vite dev server:
   ```bash
   npm run dev
   ```

## Environment Variables

```text
GROQ_API_KEY=
DATABASE_URL=sqlite:///./opspilot.db
CHROMA_DB_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
GROQ_MODEL=llama-3.3-70b-versatile
CHUNK_SIZE=800
CHUNK_OVERLAP=100
UPLOAD_DIRECTORY=./uploads
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Deployment Instructions

### Render (Backend)

1. Create a Render web service.
2. Connect this repository.
3. Use the included Render configuration in `render.yaml`.
4. Set the environment variables above.
5. Deploy.

### Vercel (Frontend)

1. Create a Vercel project.
2. Connect this repository.
3. Set `VITE_API_BASE_URL` to your backend URL.
4. Deploy.

## Chunking Strategy

Text is split into fixed-size chunks with overlap to preserve local context across chunk boundaries.

## Retrieval Strategy

The system embeds the user question and retrieves the most semantically relevant chunks from ChromaDB before generating an answer.

## Conversation Memory

Conversation history is stored in SQLite and reused for follow-up questions within the same session.

## Source Attribution

Each answer includes source metadata such as document name, chunk ID, page number, and similarity score where available.

## Known Limitations

- The current implementation uses a local ChromaDB store.
- PDF page numbering is basic and may need refinement for complex documents.
- The app is intended as a lightweight MVP rather than a large-scale enterprise system.

## Future Improvements

- Add authentication and authorization
- Support larger document collections and persistent cloud storage
- Improve chunk/page metadata accuracy
- Add observability and logging
- Expand evaluation and testing coverage
