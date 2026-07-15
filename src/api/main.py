from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import system, companies, financials, analytics

app = FastAPI(
    title="Nifty100 Financial Intelligence API",
    description="Production-ready FastAPI backend for Nifty100 Financial Intelligence Platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(system.router)
app.include_router(companies.router)
app.include_router(financials.router)
app.include_router(analytics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
