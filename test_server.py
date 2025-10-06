"""
Minimal FastAPI server to test Railway deployment
This isolates potential import issues in bot.py
"""

import os
from fastapi import FastAPI

# Initialize FastAPI
app = FastAPI(title="Test Server")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Test server is working!", "port": os.getenv("PORT", "unknown")}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "test": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)