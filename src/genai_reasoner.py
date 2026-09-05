import json
import re
from typing import Dict, Any, List
from src.config import config
from src.schemas import (
    ClaimPayload, ClaimReviewResponse, DeterministicCheck,
    ContradictionItem, PolicyCitation, EvidenceFinding
)
from prompts.policy_reasoning import SYSTEM_PROMPT, USER_REASONING_PROMPT_TEMPLATE

class GenAIReasoner:
    """
    Gemini GenAI Reasoning Engine.
    Executes grounded reasoning over claim evidence, retrieved policy clauses,
    and deterministic rule results. Includes strict JSON schema validation and graceful fallback.
    """
    
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_MODEL_NAME

    def _format_documents(self, documents: List[Any]) -> str:
        lines = []
        for doc in documents:
            lines.append(f"• Document Type: {doc.doc_type} (ID: {doc.doc_id})")
            for k, v in doc.fields.items():
                lines.append(f"   - {k}: {v}")
        return "\n".join(lines) if lines else "No documents submitted."

    def _format_checks(self, checks: List[DeterministicCheck]) -> str:
        lines = []
        for chk in checks:
            status = "PASSED" if chk.passed else "FAILED / TRIGGERED"
            lines.append(f"• [{status}] {chk.check_name} (Clause: {chk.policy_clause_id})")
            lines.append(f"   Details: {chk.details}")
            lines.append(f"   Sources: {', '.join(chk.source_fields)}")
        return "\n".join(lines)

    def _format_contradictions(self, contradictions: List[ContradictionItem]) -> str:
        if not contradictions:
            return "No document contradictions detected. All document fields agree."
        lines = []
        for c in contradictions:
            lines.append(f"• CONTRADICTION in '{c.field_name}':")
            lines.append(f"   Value A: '{c.value_a}' (Source: {c.source_a})")
            lines.append(f"   Value B: '{c.value_b}' (Source: {c.source_b})")
            lines.append(f"   Impact: {c.impact_explanation}")
            lines.append(f"   Action: {c.recommended_action}")
        return "\n".join(lines)

    def _format_clauses(self, clauses: List[Dict[str, Any]]) -> str:
        lines = []
        for c in clauses:
            lines.append(f"• [{c['clause_id']}] {c['title']} ({c.get('category', 'Policy Rule')})")
            lines.append(f"   Text: {c['text']}")
        return "\n".join(lines)

    def review_claim_with_gemini(
        self,
        claim: ClaimPayload,
        deterministic_checks: List[DeterministicCheck],
        missing_docs: List[str],
        deductible_info: Dict[str, Any],
        contradictions: List[ContradictionItem],
        retrieved_clauses: List[Dict[str, Any]]
    ) -> ClaimReviewResponse:
        """Invokes Gemini API for evidence reasoning or uses deterministic fallback if API is unavailable."""
        
        # Prepare context strings
        docs_summary = self._format_documents(claim.submitted_documents)
        checks_summary = self._format_checks(deterministic_checks)
        contradictions_summary = self._format_contradictions(contradictions)
        clauses_summary = self._format_clauses(retrieved_clauses)
        
        user_prompt = USER_REASONING_PROMPT_TEMPLATE.format(
            claim_id=claim.claim_id,
            case_name=claim.case_name,
            claim_type=claim.claim_type,
            vehicle_type=claim.vehicle_type,
            vehicle_model=claim.vehicle_model,
            registration_number=claim.registration_number,
            insured_declared_value=claim.insured_declared_value,
            incident_date=claim.incident_date,
            report_date=claim.report_date,
            claimed_amount=claim.claimed_amount,
            incident_location=claim.incident_location,
            customer_description=claim.customer_description,
            documents_summary=docs_summary,
            deterministic_checks_summary=checks_summary,
            missing_documents=", ".join(missing_docs) if missing_docs else "None",
            deductible_explanation=deductible_info.get("explanation", ""),
            contradictions_summary=contradictions_summary,
            policy_clauses_summary=clauses_summary
        )

        if not self.api_key:
            return self._fallback_synthesis(
                claim, deterministic_checks, missing_docs, deductible_info,
                contradictions, retrieved_clauses, reason="GEMINI_API_KEY environment variable is not set."
            )

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Try available models: gemini-1.5-flash, gemini-2.5-flash, gemini-1.5-pro
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"}
            )
            
            response = model.generate_content(user_prompt)
            raw_text = response.text.strip()
            
            # Extract JSON if enclosed in markdown backticks
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                raw_text = match.group(0)
                
            parsed = json.loads(raw_text)
            
            # Parse applicable policy citations
            citations = []
            for cl in retrieved_clauses:
                cid = cl.get("clause_id", "")
                citations.append(PolicyCitation(
                    clause_id=cid,
                    title=cl.get("title", ""),
                    category=cl.get("category", ""),
                    text=cl.get("text", ""),
                    applicability_reason=f"Retrieved policy clause applicable to {claim.claim_type}.",
                    supports_claim=not any(chk.policy_clause_id == cid and not chk.passed for chk in deterministic_checks)
                ))
                
            # Parse findings
            findings = []
            raw_findings = parsed.get("evidence_findings", [])
            for idx, rf in enumerate(raw_findings):
                if isinstance(rf, dict):
                    findings.append(EvidenceFinding(
                        finding_id=rf.get("finding_id", f"FINDING-{idx+1}"),
                        summary=rf.get("summary", "Finding summary"),
                        evidence_source=rf.get("evidence_source", "Claim Documents"),
                        policy_clause=rf.get("policy_clause", "POLICY-01"),
                        reasoning=rf.get("reasoning", "Evidence evaluation"),
                        finding_type=rf.get("finding_type", "COMPLIANCE")
                    ))
                    
            return ClaimReviewResponse(
                claim_id=claim.claim_id,
                case_name=claim.case_name,
                overall_recommendation=parsed.get("overall_recommendation", "REQUEST INFORMATION"),
                human_escalation_required=bool(parsed.get("human_escalation_required", False)),
                escalation_reason=parsed.get("escalation_reason"),
                confidence_level=parsed.get("confidence_level", "HIGH"),
                completeness_status=parsed.get("completeness_status", "INCOMPLETE" if missing_docs else "COMPLETE"),
                consistency_status=parsed.get("consistency_status", "CONTRADICTORY" if contradictions else "CONSISTENT"),
                missing_documents=missing_docs,
                deterministic_checks=deterministic_checks,
                contradictions=contradictions,
                applicable_policy_clauses=citations,
                evidence_findings=findings,
                investigator_next_steps=parsed.get("investigator_next_steps", ["Review claim details."]),
                unknowns_and_ambiguities=parsed.get("unknowns_and_ambiguities", []),
                ai_reasoning_summary=parsed.get("ai_reasoning_summary", "Gemini synthesis complete."),
                ai_mode="GEMINI_POWERED"
            )
            
        except Exception as e:
            return self._fallback_synthesis(
                claim, deterministic_checks, missing_docs, deductible_info,
                contradictions, retrieved_clauses, reason=f"Gemini API call failed: {str(e)}"
            )

    def _fallback_synthesis(
        self,
        claim: ClaimPayload,
        deterministic_checks: List[DeterministicCheck],
        missing_docs: List[str],
        deductible_info: Dict[str, Any],
        contradictions: List[ContradictionItem],
        retrieved_clauses: List[Dict[str, Any]],
        reason: str
    ) -> ClaimReviewResponse:
        """High-precision deterministic synthesis fallback when Gemini API is unavailable or errors out."""
        
        has_failed_checks = any(not chk.passed for chk in deterministic_checks if chk.policy_clause_id != "POLICY-06")
        has_contradictions = len(contradictions) > 0
        has_missing_docs = len(missing_docs) > 0
        
        # Check narrative for exclusions (racing, alcohol)
        desc_lower = claim.customer_description.lower()
        exclusion_triggered = any(kw in desc_lower for kw in ["racing", "track", "speed test", "drunk", "alcohol", "illegal"])
        
        # Check ambiguity for escalation
        is_ambiguous = "submergence" in desc_lower and any(c.field_name == "incident_cause vs mechanical_damage" for c in contradictions)
        
        if exclusion_triggered:
            rec = "REJECT"
            escalate = False
            esc_reason = None
            conf = "HIGH"
            summary = f"Claim REJECTED based on Policy Exclusion (POLICY-04). Narrative indicates vehicle was used for racing or unauthorized activities."
        elif has_contradictions:
            rec = "REQUEST INFORMATION"
            escalate = True
            esc_reason = f"Cross-document contradictions detected in {len(contradictions)} field(s)."
            conf = "MEDIUM" if not is_ambiguous else "LOW"
            summary = f"Claim requires additional information due to document contradictions in {[c.field_name for c in contradictions]}."
        elif has_missing_docs:
            rec = "REQUEST INFORMATION"
            escalate = True
            esc_reason = f"Mandatory policy document(s) missing: {', '.join(missing_docs)}."
            conf = "HIGH"
            summary = f"Claim INCOMPLETE. Missing required document(s): {', '.join(missing_docs)} per POLICY-06 / POLICY-03."
        elif has_failed_checks:
            rec = "REQUEST INFORMATION"
            escalate = True
            esc_reason = "Deterministic policy checks failed."
            conf = "MEDIUM"
            summary = "Policy check threshold failed."
        elif is_ambiguous:
            rec = "REQUEST INFORMATION"
            escalate = True
            esc_reason = "Ambiguous damage cause requires field surveyor investigation."
            conf = "LOW"
            summary = "Ambiguous cause of damage requires physical inspection."
        else:
            rec = "APPROVE"
            escalate = False
            esc_reason = None
            conf = "HIGH"
            summary = f"All required documents submitted, dates consistent, claim within reporting window, and incident covered under POLICY-02. Net estimated payout: ₹{deductible_info.get('estimated_net_payout', claim.claimed_amount):,.2f}."

        citations = [
            PolicyCitation(
                clause_id=c.get("clause_id", ""),
                title=c.get("title", ""),
                category=c.get("category", ""),
                text=c.get("text", ""),
                applicability_reason=f"Applicable to {claim.claim_type}.",
                supports_claim=rec == "APPROVE"
            ) for c in retrieved_clauses
        ]

        findings = []
        if has_missing_docs:
            findings.append(EvidenceFinding(
                finding_id="FIND-MISSING-01",
                summary=f"Missing Document: {', '.join(missing_docs)}",
                evidence_source="Submitted Documents Manifest",
                policy_clause="POLICY-06" if "theft" not in claim.claim_type.lower() else "POLICY-03",
                reasoning=f"Required document(s) not provided.",
                finding_type="MISSING_DOC"
            ))
        for c in contradictions:
            findings.append(EvidenceFinding(
                finding_id=f"FIND-CONTRA-{c.field_name}",
                summary=f"Contradiction in {c.field_name}",
                evidence_source=f"{c.source_a} vs {c.source_b}",
                policy_clause="POLICY-05",
                reasoning=c.impact_explanation,
                finding_type="CONTRADICTION"
            ))
        if rec == "APPROVE":
            findings.append(EvidenceFinding(
                finding_id="FIND-APP-01",
                summary="Full Compliance Verified",
                evidence_source="Claim Form & Repair Estimate",
                policy_clause="POLICY-02",
                reasoning="Incident within policy window, documents valid and consistent.",
                finding_type="COMPLIANCE"
            ))

        next_steps = []
        if rec == "APPROVE":
            next_steps = ["Proceed to claim settlement authorization.", "Issue deductible note to insured."]
        elif rec == "REJECT":
            next_steps = ["Issue formal rejection letter citing POLICY-04.", "Archive claim file."]
        else:
            next_steps = ["Contact insured for missing documents/clarification.", "Escalate claim file to field surveyor."]

        return ClaimReviewResponse(
            claim_id=claim.claim_id,
            case_name=claim.case_name,
            overall_recommendation=rec,
            human_escalation_required=escalate,
            escalation_reason=esc_reason,
            confidence_level=conf,
            completeness_status="INCOMPLETE" if has_missing_docs else "COMPLETE",
            consistency_status="CONTRADICTORY" if has_contradictions else "CONSISTENT",
            missing_documents=missing_docs,
            deterministic_checks=deterministic_checks,
            contradictions=contradictions,
            applicable_policy_clauses=citations,
            evidence_findings=findings,
            investigator_next_steps=next_steps,
            unknowns_and_ambiguities=[c.impact_explanation for c in contradictions],
            ai_reasoning_summary=f"{summary} [Note: Evaluated via Deterministic Engine ({reason})]",
            ai_mode="DETERMINISTIC_FALLBACK"
        )
