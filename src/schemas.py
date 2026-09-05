from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentField(BaseModel):
    name: str
    value: Any
    source_document: str

class SubmittedDocument(BaseModel):
    doc_type: str
    doc_id: str
    fields: Dict[str, Any] = Field(default_factory=dict)

class ClaimPayload(BaseModel):
    claim_id: str
    case_name: str
    claim_type: str  # "Accidental Damage" or "Vehicle Theft"
    vehicle_type: str  # "Car" or "Two-Wheeler"
    vehicle_model: str
    registration_number: str
    insured_declared_value: float
    incident_date: str
    report_date: str
    incident_location: str
    claimed_amount: float
    customer_description: str
    submitted_documents: List[SubmittedDocument]

class PolicyCitation(BaseModel):
    clause_id: str
    title: str
    category: str
    text: str
    applicability_reason: str
    supports_claim: bool

class DeterministicCheck(BaseModel):
    check_name: str
    passed: bool
    details: str
    policy_clause_id: str
    source_fields: List[str]

class ContradictionItem(BaseModel):
    field_name: str
    value_a: str
    source_a: str
    value_b: str
    source_b: str
    impact_explanation: str
    recommended_action: str

class EvidenceFinding(BaseModel):
    finding_id: str
    summary: str
    evidence_source: str  # e.g., "Claim Form -> incident_date"
    policy_clause: str    # e.g., "POLICY-05"
    reasoning: str
    finding_type: str     # "COMPLIANCE", "CONTRADICTION", "MISSING_DOC", "EXCLUSION", "UNCERTAINTY"

class ClaimReviewResponse(BaseModel):
    claim_id: str
    case_name: str
    overall_recommendation: str  # "APPROVE", "REJECT", "REQUEST INFORMATION"
    human_escalation_required: bool
    escalation_reason: Optional[str] = None
    confidence_level: str  # "HIGH", "MEDIUM", "LOW"
    completeness_status: str  # "COMPLETE", "INCOMPLETE"
    consistency_status: str     # "CONSISTENT", "CONTRADICTORY"
    
    missing_documents: List[str] = Field(default_factory=list)
    deterministic_checks: List[DeterministicCheck] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    applicable_policy_clauses: List[PolicyCitation] = Field(default_factory=list)
    evidence_findings: List[EvidenceFinding] = Field(default_factory=list)
    
    investigator_next_steps: List[str] = Field(default_factory=list)
    unknowns_and_ambiguities: List[str] = Field(default_factory=list)
    ai_reasoning_summary: str
    ai_mode: str  # "GEMINI_POWERED" or "DETERMINISTIC_FALLBACK"
