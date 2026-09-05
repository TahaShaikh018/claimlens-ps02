import pytest
from src.schemas import ClaimPayload, SubmittedDocument
from src.contradiction_engine import ContradictionEngine

@pytest.fixture
def contradiction_engine():
    return ContradictionEngine()

def test_date_contradiction(contradiction_engine):
    claim = ClaimPayload(
        claim_id="TEST-002",
        case_name="Date Contradiction Test",
        claim_type="Accidental Damage",
        vehicle_type="Car",
        vehicle_model="Hyundai i20",
        registration_number="MH-02-CB-9876",
        insured_declared_value=600000.0,
        incident_date="2026-08-10",
        report_date="2026-08-15",
        incident_location="Mumbai",
        claimed_amount=40000.0,
        customer_description="Side collision",
        submitted_documents=[
            SubmittedDocument(
                doc_type="Claim Form",
                doc_id="CF1",
                fields={"incident_date": "2026-08-10", "claimed_amount": 40000.0}
            ),
            SubmittedDocument(
                doc_type="Repair Estimate",
                doc_id="RE1",
                fields={"incident_date": "2026-08-20", "estimated_cost": 40000.0} # Contradicts 10 Aug!
            )
        ]
    )
    contradictions = contradiction_engine.analyze_contradictions(claim)
    assert len(contradictions) >= 1
    date_c = [c for c in contradictions if c.field_name == "incident_date"]
    assert len(date_c) == 1
    assert date_c[0].value_a == "2026-08-10"
    assert date_c[0].value_b == "2026-08-20"

def test_amount_mismatch(contradiction_engine):
    claim = ClaimPayload(
        claim_id="TEST-003",
        case_name="Amount Mismatch Test",
        claim_type="Accidental Damage",
        vehicle_type="Car",
        vehicle_model="Honda City",
        registration_number="KA-01-MJ-4321",
        insured_declared_value=800000.0,
        incident_date="2026-08-25",
        report_date="2026-08-27",
        incident_location="Bengaluru",
        claimed_amount=45000.0,
        customer_description="Rear collision",
        submitted_documents=[
            SubmittedDocument(
                doc_type="Claim Form",
                doc_id="CF1",
                fields={"claimed_amount": 45000.0}
            ),
            SubmittedDocument(
                doc_type="Repair Estimate",
                doc_id="RE1",
                fields={"estimated_cost": 85000.0} # Differ by > 1,000
            )
        ]
    )
    contradictions = contradiction_engine.analyze_contradictions(claim)
    amt_c = [c for c in contradictions if "claimed_amount" in c.field_name]
    assert len(amt_c) == 1
