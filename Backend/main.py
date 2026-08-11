from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Multi-Agent Research Assistant API",
    description="Backend API for the Multi-Agent Research Assistant",
    version="1.0.0",
)

# CORS configuration - allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Multi-Agent Research Assistant API is running"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
