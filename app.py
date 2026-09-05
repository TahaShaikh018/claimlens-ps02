import uvicorn
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ClaimLens - Motor Insurance Claims Evidence Review Assistant",
    description="PS02 Motor Insurance Claims Review System",
    version="1.0.0"
)

# Ensure frontend directory exists
os.makedirs("frontend", exist_ok=True)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>ClaimLens Motor Claims Evidence Review Assistant</h1><p>Frontend loading...</p>"

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "track_id": "PS02",
        "validation_key": "PS02",
        "service": "ClaimLens Motor Insurance Evidence Review Assistant"
    }

if __name__ == "__main__":
    print("Starting ClaimLens App on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
