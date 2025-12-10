from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth, admin_books, student_books, borrow, rag
import os

app = FastAPI(
    title="Library Management System",
    description="Backend API for Library Management with AI-powered content generation and RAG chat",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(admin_books.router)
app.include_router(student_books.router)
app.include_router(borrow.router)
app.include_router(rag.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Library Management System API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "admin_books": "/admin/books",
            "student_books": "/student/books",
            "borrow": "/borrow",
            "rag": "/rag"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
