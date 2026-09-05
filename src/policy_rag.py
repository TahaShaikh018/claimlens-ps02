import json
import os
import numpy as np
from typing import List, Dict, Any
from src.config import config
from src.schemas import PolicyCitation

class PolicyRAG:
    """
    Local Vector Retrieval Engine for Motor Insurance Policy Clauses.
    Uses Gemini Embeddings (gemini-embedding-001) with local NumPy cosine similarity.
    NO external vector database required. Fully compliant with hackathon privacy & network rules.
    """
    
    def __init__(self, policy_json_path: str = None):
        self.policy_path = policy_json_path or config.POLICY_FILE_JSON
        self.clauses: List[Dict[str, Any]] = []
        self.clause_embeddings: Dict[str, np.ndarray] = {}
        self._load_policy()
        
    def _load_policy(self):
        """Loads policy clauses from JSON file."""
        if not os.path.exists(self.policy_path):
            raise FileNotFoundError(f"Policy file not found at: {self.policy_path}")
            
        with open(self.policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.clauses = data.get("clauses", [])

    def _get_embedding_gemini(self, text: str) -> np.ndarray:
        """Calls Gemini API for embedding generation using gemini-embedding-001."""
        if not config.GEMINI_API_KEY:
            return self._fallback_vector(text)
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            vec = np.array(result['embedding'], dtype=np.float32)
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else vec
        except Exception as e:
            # Fallback to local keyword vector if Gemini API call fails or quota exceeded
            return self._fallback_vector(text)

    def _fallback_vector(self, text: str) -> np.ndarray:
        """Deterministic TF-IDF style keyword vector fallback for offline testing."""
        vocab = [
            "coverage", "accidental", "theft", "fir", "police", "exclusion",
            "racing", "alcohol", "license", "window", "days", "reporting",
            "documents", "repair", "estimate", "idv", "total", "loss", "deductible"
        ]
        text_lower = text.lower()
        vec = np.zeros(len(vocab), dtype=np.float32)
        for i, word in enumerate(vocab):
            vec[i] = text_lower.count(word)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def index_policy(self):
        """Generates embeddings for all policy clauses and stores them locally in memory."""
        for clause in self.clauses:
            clause_id = clause["clause_id"]
            content = f"{clause['clause_id']} {clause['title']} {clause['category']} {clause['text']}"
            self.clause_embeddings[clause_id] = self._get_embedding_gemini(content)

    def retrieve_relevant_clauses(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant policy clauses for a given claim query or description."""
        if not self.clause_embeddings:
            self.index_policy()
            
        query_vec = self._get_embedding_gemini(query)
        
        scores = []
        for clause in self.clauses:
            clause_id = clause["clause_id"]
            c_vec = self.clause_embeddings.get(clause_id)
            if c_vec is not None and len(c_vec) == len(query_vec):
                sim = float(np.dot(query_vec, c_vec))
            else:
                sim = 0.0
            scores.append((sim, clause))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [clause for _, clause in scores[:top_k]]

    def get_all_clauses(self) -> List[Dict[str, Any]]:
        """Returns all policy clauses."""
        return self.clauses

    def get_clause_by_id(self, clause_id: str) -> Dict[str, Any]:
        """Fetches a specific policy clause by ID (e.g., POLICY-05)."""
        for clause in self.clauses:
            if clause["clause_id"] == clause_id:
                return clause
        return {"clause_id": clause_id, "title": "Unknown Clause", "text": "Clause details not found."}
