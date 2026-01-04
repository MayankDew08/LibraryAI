from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth, admin_books, student_books, student_generation, borrow, rag, otp
import os
import logging
import cProfile
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger('profiler')

# Get profile directory from environment variable, fallback to default
PROFILE_DIR = os.environ.get('PROFILE_DIR', os.path.join(os.path.dirname(__file__), "profiles"))
os.makedirs(PROFILE_DIR, exist_ok=True)

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

# cProfile middleware for RAG query performance profiling only
@app.middleware("http")
async def profile_requests(request: Request, call_next):
    """Profile only RAG query requests using cProfile for detailed performance analysis"""
    
    # Only profile RAG query requests
    import re
    if not (request.method == "POST" and re.match(r"/rag/books/\d+/query$", request.url.path)):
        # For non-RAG requests, just pass through without profiling
        return await call_next(request)
    
    # Profile RAG query requests
    time_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = request.url.path.replace("/", "_").strip("_") or "root"
    profile_path = os.path.join(PROFILE_DIR, f"profile_{path}_{time_stamp}.prof")
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    response = await call_next(request)
    
    profiler.disable()
    profiler.dump_stats(profile_path)
    logger.info(f"RAG Query Profile saved: {profile_path}")
    
    return response

# Mount static files directory
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(admin_books.router)
app.include_router(student_books.router)
app.include_router(student_generation.router)
app.include_router(borrow.router)
app.include_router(rag.router)
app.include_router(otp.router)


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
