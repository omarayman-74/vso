"""FastAPI application for Eshtri Aqar Chatbot."""
# Fix for ChromaDB on Render/Linux (needs SQLite >= 3.35)
import os
if os.getenv("RENDER"):
    try:
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass


from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

from config import settings
from services.chat_service import chat_service
from services.database_service import db_service


# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="AI-powered real estate chatbot with RAG and SQL capabilities"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    detected_language: str = "en"
    sql_logs: list = []


# Routes
@app.get("/")
async def root():
    """Serve the frontend."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return {
        "status": "healthy",
        "service": settings.app_title,
        "version": settings.app_version
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process chat message and return response.
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Process message
        result = chat_service.process_message(
            session_id=request.session_id,
            message=request.message.strip()
        )
        
        return ChatResponse(
            response=result["response"],
            detected_language=result.get("detected_language", "en"),
            sql_logs=result.get("sql_logs", [])
        )
        
    except Exception as e:
        print(f"[ERROR] Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear-session")
async def clear_session(session_id: str = "default"):
    """Clear chat session."""
    try:
        chat_service.clear_session(session_id)
        return {"status": "success", "message": "Session cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-db")
async def test_database():
    """Test database connection."""
    success = db_service.test_connection()
    if success:
        return {"status": "success", "message": "Database connection successful"}
    else:
        raise HTTPException(status_code=500, detail="Database connection failed")


# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    # Also serve static files at root for assets
    @app.get("/style.css")
    async def serve_css():
        return FileResponse("static/style.css")
    
    @app.get("/script.js")
    async def serve_js():
        return FileResponse("static/script.js")
    
    @app.get("/favicon.png")
    async def serve_favicon():
        return FileResponse("static/favicon.png")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("=" * 60)
    print(f"{settings.app_title} v{settings.app_version}")
    print("=" * 60)
    print(f"Database connection will be tested on first request...")
    # db_service.test_connection()  # Commented out to prevent blocking startup
    print(f"RAG service initialized (Lazy Loading Enabled)")
    print("=" * 60)
    print("Application ready!")
    print("=" * 60)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True
    )
