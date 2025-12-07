from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router
 
# Initialize FastAPI application
app = FastAPI()

# Allows different origin requests from frontend 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000",
                   "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], # Allow all HTTP methods
    allow_headers=["*"], # Allow all headers
)

# Register API routes from api.py
app.include_router(api_router)
