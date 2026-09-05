import json
import os
import numpy as np
from typing import List, Dict, Any
from src.config import config
from src.schemas import PolicyCitation

class PolicyRAG:
    """
    Ultra-Fast Local Policy Retrieval Engine (RAG).
    Uses high-speed local keyword vector indexing over system motor policy clauses.
    Executes in < 1ms locally without burning Gemini network API rate limits or quota.
    """
    
    def __init__(self, policy_json_path: str = None):
        self.policy_path = policy_json_path or config.POLICY_FILE_JSON
        self.clauses: List[Dict[str, Any]] = []
        self.clause_vectors: Dict[str, np.ndarray] = {}
        self.vocab: List[str] = [
            "coverage", "accidental", "theft", "fir", "police", "exclusion",
            "racing", "alcohol", "license", "window", "days", "reporting",
            "documents", "repair", "estimate", "idv", "total", "loss", "deductible",
            "damage", "submergence", "water", "flood", "impact", "commercial"
        ]
        self._load_policy()
        self._index_policy_local()
        
    def _load_policy(self):
        """Loads policy clauses from JSON file."""
        if not os.path.exists(self.policy_path):
            raise FileNotFoundError(f"Policy file not found at: {self.policy_path}")
            
        with open(self.policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.clauses = data.get("clauses", [])

    def _text_to_vector(self, text: str) -> np.ndarray:
        """Converts text into normalized local vector representation."""
        text_lower = text.lower()
        vec = np.zeros(len(self.vocab), dtype=np.float32)
        for i, word in enumerate(self.vocab):
            vec[i] = text_lower.count(word)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def _index_policy_local(self):
        """Generates fast local vectors for all policy clauses."""
        for clause in self.clauses:
            clause_id = clause["clause_id"]
            content = f"{clause['clause_id']} {clause['title']} {clause['category']} {clause['text']}"
            self.clause_vectors[clause_id] = self._text_to_vector(content)

    def retrieve_relevant_clauses(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant policy clauses instantly in < 1ms."""
        query_vec = self._text_to_vector(query)
        
        scores = []
        for clause in self.clauses:
            clause_id = clause["clause_id"]
            c_vec = self.clause_vectors.get(clause_id)
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
