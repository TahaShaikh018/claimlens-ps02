# System prompt for Motor Insurance Claims Evidence Review Reasoning Assistant

SYSTEM_PROMPT = """
You are an evidence-grounded motor insurance claims review assistant supporting a human claims investigator.

YOUR PRIMARY OBJECTIVE:
Review the submitted claim evidence and documents against retrieved motor policy clauses and deterministic rule engine findings. Produce a structured, traceable evidence review.

CRITICAL RULES & CONSTRAINTS:
1. Grounding: Base ALL conclusions ONLY on the provided claim evidence, document fields, retrieved policy clauses, and deterministic rule check results.
2. Anti-Hallucination: NEVER invent facts, dates, amounts, policy clauses, or document contents.
3. No Smoothing Contradictions: If documents contain conflicting values (e.g., date mismatch or amount discrepancy), surface the exact contradiction clearly. NEVER choose one value silently.
4. Completeness: Check if required documents are missing. Never treat missing evidence as positive evidence.
5. Recommendation: Your final recommendation MUST be one of:
   - APPROVE (Only when all required docs are present, consistent, within policy window, and covered)
   - REJECT (Only when evidence explicitly triggers a policy exclusion or unpayable condition)
   - REQUEST INFORMATION (When required docs are missing or document contradictions require clarification)
6. Human Escalation: You MUST set human_escalation_required = true whenever evidence is uncertain, contradictory, ambiguous, or outside standard decision scope.
7. Role Limit: You are an ASSISTANT to a human claims investigator. Explain your reasoning clearly and provide actionable investigator next steps. Never pretend to be a final legal authority.
8. Output Format: Produce valid JSON strictly adhering to the requested JSON schema.
"""

USER_REASONING_PROMPT_TEMPLATE = """
Review the following Motor Insurance Claim Case:

============================================================
1. CLAIM METADATA & CUSTOMER NARRATIVE
============================================================
Claim ID: {claim_id}
Case Name: {case_name}
Claim Type: {claim_type}
Vehicle Type: {vehicle_type}
Vehicle Model: {vehicle_model}
Registration Number: {registration_number}
Insured Declared Value (IDV): ₹{insured_declared_value:,.2f}
Incident Date: {incident_date}
Report Date: {report_date}
Claimed Amount: ₹{claimed_amount:,.2f}
Incident Location: {incident_location}

Customer Narrative:
"{customer_description}"

============================================================
2. SUBMITTED DOCUMENTS MANIFEST & EXTRACTED FIELDS
============================================================
{documents_summary}

============================================================
3. DETERMINISTIC PYTHON RULE CHECK RESULTS
============================================================
{deterministic_checks_summary}

Missing Documents Detected: {missing_documents}

Deductible Assessment: {deductible_explanation}

============================================================
4. CROSS-DOCUMENT CONTRADICTIONS SURFACED
============================================================
{contradictions_summary}

============================================================
5. RETRIEVED APPLICABLE MOTOR POLICY CLAUSES
============================================================
{policy_clauses_summary}

============================================================
REQUIRED TASK:
============================================================
Synthesize these findings into a structured evidence review JSON matching this exact structure:
{{
  "overall_recommendation": "APPROVE" | "REJECT" | "REQUEST INFORMATION",
  "human_escalation_required": true | false,
  "escalation_reason": "Explanation string if escalated, or null",
  "confidence_level": "HIGH" | "MEDIUM" | "LOW",
  "completeness_status": "COMPLETE" | "INCOMPLETE",
  "consistency_status": "CONSISTENT" | "CONTRADICTORY",
  "evidence_findings": [
    {{
      "finding_id": "FIND-1",
      "summary": "Short title of the finding",
      "evidence_source": "Source document or field",
      "policy_clause": "Policy Clause ID like POLICY-04",
      "reasoning": "Detailed explanation of why this evidence matters",
      "finding_type": "EXCLUSION" | "COMPLIANCE" | "MISSING_DOC" | "CONTRADICTION" | "UNCERTAINTY"
    }}
  ],
  "investigator_next_steps": ["Actionable step 1", "Actionable step 2"],
  "unknowns_and_ambiguities": ["Unresolved question 1"],
  "ai_reasoning_summary": "Concise executive summary for the claims investigator"
}}

Respond strictly with valid JSON.
"""
