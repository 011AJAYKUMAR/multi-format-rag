import os
import shutil
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.services.parser import DocumentParser
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService

app = FastAPI(title="Multi-Format RAG API", version="1.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vector_service = VectorStoreService()
rag_service = RAGService()

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

METADATA_FILE = "uploaded_files.json"

def load_tracked_files():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tracked_files(files_dict):
    with open(METADATA_FILE, "w") as f:
        json.dump(files_dict, f, indent=4)

class ChatRequest(BaseModel):
    question: str
    selected_sources: Optional[List[str]] = None

@app.get("/files")
def list_files():
    """Returns list of uploaded files from persistent storage."""
    tracked = load_tracked_files()
    return [{"filename": name, "chunks": data["chunks"]} for name, data in tracked.items()]

@app.delete("/files/{filename}")
def delete_file(filename: str):
    """Deletes a file from Weaviate and tracking metadata."""
    try:
        # Remove vectors from Weaviate
        vector_service.delete_documents_by_source(filename)
        
        # Remove from local metadata tracker
        tracked = load_tracked_files()
        if filename in tracked:
            del tracked[filename]
            save_tracked_files(tracked)
            
        return {"status": "success", "message": f"Deleted {filename} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a multi-format document, parses it, chunks text, and stores vectors in Weaviate."""
    temp_file_path = ""
    try:
        file_ext = os.path.splitext(file.filename)[1]
        temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save uploaded file locally
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Parse text based on format
        extracted_text = DocumentParser.parse_file(temp_file_path, file_ext)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded file.")
            
        # Split text into chunks
        chunks = DocumentParser.get_text_chunks(extracted_text)
        
        # Store in Weaviate with metadata
        metadata = {"source": file.filename}
        vector_service.add_documents_to_store(chunks, metadata)
        
        # Track file persistently
        tracked = load_tracked_files()
        tracked[file.filename] = {"chunks": len(chunks)}
        save_tracked_files(tracked)
        
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_created": len(chunks),
            "message": f"Successfully processed and indexed {file.filename}!"
        }
        
    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_docs(request: ChatRequest):
    """Answers user questions based on indexed documents using RAG with optional source filtering."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")
            
        result = rag_service.answer_question(request.question, request.selected_sources)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-chat")
async def reset_chat():
    """Resets conversational memory."""
    rag_service.clear_history()
    return {"status": "success", "message": "Chat history cleared."}

@app.get("/")
def health_check():
    return {"status": "running", "message": "Multi-Format RAG API is up and active!"}