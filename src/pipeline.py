import json
import os
from typing import Dict, Any, List
from src.config import config
from src.schemas import ClaimPayload, ClaimReviewResponse
from src.rule_engine import DeterministicRuleEngine
from src.contradiction_engine import ContradictionEngine
from src.policy_rag import PolicyRAG
from src.genai_reasoner import GenAIReasoner

class ClaimsPipeline:
    """
    End-to-End Orchestrator for Motor Insurance Claims Evidence Review.
    Integrates:
    - Data loading / parsing
    - Deterministic Rule Engine
    - Contradiction Engine
    - Local Policy RAG Vector Store
    - Gemini GenAI Reasoner
    """
    
    def __init__(self):
        self.rule_engine = DeterministicRuleEngine()
        self.contradiction_engine = ContradictionEngine()
        self.policy_rag = PolicyRAG()
        self.genai_reasoner = GenAIReasoner()

    def list_available_claims(self) -> List[Dict[str, Any]]:
        """Returns manifest of pre-configured test claims in data/claims/."""
        claims_summary = []
        claims_dir = config.CLAIMS_DIR
        
        if not os.path.exists(claims_dir):
            return claims_summary
            
        for filename in sorted(os.listdir(claims_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(claims_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        claims_summary.append({
                            "claim_id": data.get("claim_id"),
                            "case_name": data.get("case_name"),
                            "claim_type": data.get("claim_type"),
                            "filename": filename
                        })
                except Exception:
                    pass
        return claims_summary

    def load_claim_from_file(self, filename_or_id: str) -> ClaimPayload:
        """Loads claim JSON by filename or claim_id."""
        claims_dir = config.CLAIMS_DIR
        
        # Check direct filename
        target_path = os.path.join(claims_dir, filename_or_id)
        if not os.path.exists(target_path):
            # Check by claim_id match
            found = False
            for f in os.listdir(claims_dir):
                if f.endswith(".json"):
                    p = os.path.join(claims_dir, f)
                    with open(p, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        if data.get("claim_id") == filename_or_id:
                            target_path = p
                            found = True
                            break
            if not found:
                raise FileNotFoundError(f"Claim '{filename_or_id}' not found in {claims_dir}.")
                
        with open(target_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            return ClaimPayload(**raw_data)

    def process_claim(self, claim: ClaimPayload) -> ClaimReviewResponse:
        """Runs the complete evidence review pipeline on a ClaimPayload."""
        
        # 1. Deterministic Rule Engine
        deterministic_checks, missing_docs, deductible_info = self.rule_engine.run_all_checks(claim)
        
        # 2. Contradiction Detection Engine
        contradictions = self.contradiction_engine.analyze_contradictions(claim)
        
        # 3. Policy RAG Retrieval
        rag_query = f"{claim.claim_type} {claim.vehicle_type} {claim.customer_description}"
        retrieved_clauses = self.policy_rag.retrieve_relevant_clauses(rag_query, top_k=4)
        
        # 4. GenAI Grounded Reasoner
        review_response = self.genai_reasoner.review_claim_with_gemini(
            claim=claim,
            deterministic_checks=deterministic_checks,
            missing_docs=missing_docs,
            deductible_info=deductible_info,
            contradictions=contradictions,
            retrieved_clauses=retrieved_clauses
        )
        
        return review_response
