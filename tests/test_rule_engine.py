import pytest
from src.schemas import ClaimPayload, SubmittedDocument
from src.rule_engine import DeterministicRuleEngine

@pytest.fixture
def rule_engine():
    return DeterministicRuleEngine()

@pytest.fixture
def base_claim():
    return ClaimPayload(
        claim_id="TEST-001",
        case_name="Test Claim",
        claim_type="Accidental Damage",
        vehicle_type="Car",
        vehicle_model="Honda City",
        registration_number="KA-01-AB-1234",
        insured_declared_value=500000.0,
        incident_date="2026-08-01",
        report_date="2026-08-05",
        incident_location="Bengaluru",
        claimed_amount=30000.0,
        customer_description="Collision with wall",
        submitted_documents=[
            SubmittedDocument(doc_type="Claim Form", doc_id="CF1", fields={"incident_date": "2026-08-01"}),
            SubmittedDocument(doc_type="Repair Estimate", doc_id="RE1", fields={"estimated_cost": 30000.0}),
            SubmittedDocument(doc_type="Registration Certificate", doc_id="RC1", fields={}),
            SubmittedDocument(doc_type="Driving License", doc_id="DL1", fields={})
        ]
    )

def test_reporting_window_pass(rule_engine, base_claim):
    # 4 days elapsed <= 7 days for accident claim
    chk = rule_engine.evaluate_reporting_window(base_claim)
    assert chk.passed is True
    assert "4 day(s)" in chk.details

def test_reporting_window_exceeded(rule_engine, base_claim):
    # 10 days elapsed > 7 days
    base_claim.report_date = "2026-08-11"
    chk = rule_engine.evaluate_reporting_window(base_claim)
    assert chk.passed is False
    assert "EXCEEDED" in chk.details

def test_theft_reporting_window(rule_engine, base_claim):
    base_claim.claim_type = "Vehicle Theft"
    base_claim.incident_date = "2026-08-01"
    base_claim.report_date = "2026-08-05" # 4 days > 1 day limit
    chk = rule_engine.evaluate_reporting_window(base_claim)
    assert chk.passed is False

def test_required_documents_pass(rule_engine, base_claim):
    chk, missing = rule_engine.evaluate_required_documents(base_claim)
    assert chk.passed is True
    assert len(missing) == 0

def test_required_documents_missing_fir(rule_engine, base_claim):
    base_claim.claim_type = "Vehicle Theft"
    chk, missing = rule_engine.evaluate_required_documents(base_claim)
    assert chk.passed is False
    assert "Police FIR" in missing

def test_idv_limit_check(rule_engine, base_claim):
    base_claim.claimed_amount = 600000.0 # Exceeds IDV of 500,000
    chk = rule_engine.evaluate_idv_limits(base_claim)
    assert chk.passed is False
    assert "exceeds IDV cap" in chk.details

def test_deductible_calculation(rule_engine, base_claim):
    res = rule_engine.calculate_deductible(base_claim)
    assert res["deductible_amount"] == 2000.0
    assert res["estimated_net_payout"] == 28000.0
