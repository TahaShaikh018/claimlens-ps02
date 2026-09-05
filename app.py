import os
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

from src.schemas import ClaimPayload, ClaimReviewResponse
from src.pipeline import ClaimsPipeline
from src.config import config

load_dotenv()

app = FastAPI(
    title="ClaimLens - Motor Insurance Claims Evidence Review Assistant",
    description="PS02 Motor Insurance Claims Review System",
    version="1.0.0"
)

# Initialize Claims Pipeline
pipeline = ClaimsPipeline()

# Serve static frontend files
os.makedirs("frontend", exist_ok=True)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = os.path.join("frontend", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>ClaimLens Motor Claims Evidence Review Assistant</h1><p>Frontend file index.html missing.</p>"

@app.get("/api/health")
def health_check():
    has_key = bool(config.GEMINI_API_KEY)
    return {
        "status": "healthy",
        "track_id": "PS02",
        "validation_key": "PS02",
        "service": "ClaimLens Motor Insurance Evidence Review Assistant",
        "gemini_api_key_configured": has_key,
        "default_model": config.GEMINI_MODEL_NAME
    }

@app.get("/api/claims")
def list_claims():
    """Lists pre-loaded sample claims for demo."""
    return pipeline.list_available_claims()

@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: str):
    """Retrieves specific claim payload by ID."""
    try:
        claim = pipeline.load_claim_from_file(claim_id)
        return claim.dict()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")

@app.post("/api/review", response_model=ClaimReviewResponse)
def review_claim(payload: ClaimPayload = Body(...)):
    """Runs full evidence review pipeline on a claim payload."""
    try:
        review_result = pipeline.process_claim(payload)
        return review_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence review failed: {str(e)}")

@app.get("/api/policy")
def get_policy():
    """Returns all motor policy clauses."""
    return pipeline.policy_rag.get_all_clauses()

if __name__ == "__main__":
    print("============================================================")
    print("Starting ClaimLens App on http://localhost:8000")
    print("Track ID: PS02 | Motor Insurance Evidence Review Assistant")
    print("============================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000)
