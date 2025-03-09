from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Financial Search Engine API",
    description="API for a financial search engine that integrates multiple financial data APIs with OpenAI's LLM",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Financial Search Engine API"}

# Import and include routers
from app.api.routes import search, stock, financials

app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(stock.router, prefix="/api", tags=["stock"])
app.include_router(financials.router, prefix="/api", tags=["financials"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 