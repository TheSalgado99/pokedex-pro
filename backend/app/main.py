# backend/app/main.py

# --- Standard Library Imports ---
from contextlib import asynccontextmanager

# --- Third Party Imports ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware

# --- Local Imports ---
# models module needs to be imported so SQLModel registers the tables
from . import models
from .db import init_db           # Import the DB initialization function from db.py
from .routers import router_sets, router_cards # Import the specific routers from routers.py

# ============================================
# FastAPI Lifespan Context Manager
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager: calls database initialization on startup.
    """
    print("Main: Application startup: Running lifespan tasks...")
    await init_db() # Call the init function from db.py
    yield
    print("Main: Application shutdown.")

# ============================================
# FastAPI Application Instance
# ============================================
print("Main: Creating FastAPI app instance...")
app = FastAPI(
    title="PokéndeX Pro API",
    description="API for Pokémon TCG collection management, profitability analysis, and card scanning.",
    version="0.1.0",
    lifespan=lifespan # Register the lifespan handler
)
print("Main: FastAPI app instance created.")

# ============================================
# CORS (Cross-Origin Resource Sharing) Middleware
# ============================================
# This MUST be added AFTER the FastAPI app instance is created
print("Main: Configuring CORS middleware...")
origins = [
    "http://localhost:5173", # Default Vite dev server port for React frontend
    "http://127.0.0.1:5173", # Explicit IP for localhost
    "http://localhost:3000", # Common port for create-react-app (just in case)
    # Add the URL of your deployed frontend app here later, e.g., "https://your-pokendex-pro.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # List of origins allowed to make requests
    allow_credentials=True,      # Allow cookies to be included in requests
    allow_methods=["*"],         # Allow all standard HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],         # Allow all headers
)
print(f"Main: CORS middleware configured for origins: {origins}")

# ============================================
# API Endpoints (Root and Routers)
# ============================================

# --- Root Endpoint ---
@app.get("/", tags=["General"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the PokéndeX Pro API"}

# --- Include API Routers ---
# Include the routers defined in routers.py AFTER middleware is added
print("Main: Including API routers...")
app.include_router(router_sets)    # Includes all endpoints from router_sets (prefix /sets)
app.include_router(router_cards)   # Includes all endpoints from router_cards (prefix /cards)
# Add other routers here as you create them
print("Main: API routers included.")