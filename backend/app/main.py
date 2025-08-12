from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import videos, auth

app = FastAPI(title="FormAI API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(videos.router, prefix="/videos", tags=["Videos"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
