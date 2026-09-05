import pytest
from src.pipeline import ClaimsPipeline

@pytest.fixture
def pipeline():
    return ClaimsPipeline()

def test_pipeline_case1_approvable(pipeline):
    claim = pipeline.load_claim_from_file("case1_approvable.json")
    review = pipeline.process_claim(claim)
    assert review.overall_recommendation == "APPROVE"
    assert review.completeness_status == "COMPLETE"
    assert review.consistency_status == "CONSISTENT"
    assert review.human_escalation_required is False

def test_pipeline_case2_contradiction(pipeline):
    claim = pipeline.load_claim_from_file("case2_contradiction.json")
    review = pipeline.process_claim(claim)
    assert review.overall_recommendation == "REQUEST INFORMATION"
    assert review.consistency_status == "CONTRADICTORY"
    assert len(review.contradictions) > 0

def test_pipeline_case3_missing_doc(pipeline):
    claim = pipeline.load_claim_from_file("case3_missing_doc.json")
    review = pipeline.process_claim(claim)
    assert review.overall_recommendation == "REQUEST INFORMATION"
    assert review.completeness_status == "INCOMPLETE"
    assert "Police FIR" in review.missing_documents

def test_pipeline_case4_exclusion(pipeline):
    claim = pipeline.load_claim_from_file("case4_exclusion.json")
    review = pipeline.process_claim(claim)
    assert review.overall_recommendation == "REJECT"

def test_pipeline_case5_uncertain(pipeline):
    claim = pipeline.load_claim_from_file("case5_uncertain.json")
    review = pipeline.process_claim(claim)
    assert review.human_escalation_required is True
