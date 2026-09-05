import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    POLICY_FILE_JSON: str = os.path.join(DATA_DIR, "policy", "motor_policy.json")
    POLICY_FILE_MD: str = os.path.join(DATA_DIR, "policy", "motor_policy.md")
    CLAIMS_DIR: str = os.path.join(DATA_DIR, "claims")

config = Config()
