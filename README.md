# CV Query Engine

A fullstack application for querying CVs using advanced AI and vector search. The backend is built with FastAPI, Pinecone, and LangChain, while the frontend is built with React.

## Features
- Upload and query CVs/resumes
- Semantic search using Pinecone vector database
- AI-powered answers and structured data extraction
- Modern React frontend

## Project Structure
```
CV-Query-Engine-FastApi-Pinecone-LangChain-React/
  backend/    # FastAPI backend
  frontend/   # React frontend
```

## Backend (FastAPI)
### Prerequisites
- Python 3.11+
- (Recommended) Create a virtual environment

### Setup
```bash
cd backend
python -m venv env
# Activate the virtual environment:
# On Windows:
env\Scripts\activate
# On macOS/Linux:
source env/bin/activate
pip install -r requirements.txt
```

### Running the Backend
```bash
uvicorn main:app --reload
```

## Frontend (React)
### Prerequisites
- Node.js 18+

### Setup
```bash
cd frontend
npm install
```

### Running the Frontend
```bash
npm run dev
```

## Usage
1. Start the backend server.
2. Start the frontend dev server.
3. Access the app at [http://localhost:5173](http://localhost:5173) 

## Environment Variables
- Configure Pinecone, LangChain, and other secrets in the backend as needed.
