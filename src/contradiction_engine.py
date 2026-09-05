from typing import List, Dict, Any
from src.schemas import ClaimPayload, ContradictionItem

class ContradictionEngine:
    """
    Cross-document analysis engine. Compares field values across Claim Form,
    Repair Estimate, FIR, RC, DL, and Customer Narrative.
    Rule: Contradictions MUST be surfaced directly and NEVER smoothed over.
    """
    
    def analyze_contradictions(self, claim: ClaimPayload) -> List[ContradictionItem]:
        contradictions: List[ContradictionItem] = []
        
        # Build document field map for fast cross-document comparison
        doc_map: Dict[str, Dict[str, Any]] = {}
        for doc in claim.submitted_documents:
            doc_map[doc.doc_type] = doc.fields
            
        claim_form = doc_map.get("Claim Form", {})
        repair_est = doc_map.get("Repair Estimate", {})
        rc_doc = doc_map.get("Registration Certificate", {})
        dl_doc = doc_map.get("Driving License", {})
        
        # 1. Date Contradiction (Claim Form incident_date vs Repair Estimate incident_date)
        cf_inc_date = claim_form.get("incident_date", claim.incident_date)
        re_inc_date = repair_est.get("incident_date")
        
        if re_inc_date and cf_inc_date and re_inc_date.strip() != cf_inc_date.strip():
            contradictions.append(ContradictionItem(
                field_name="incident_date",
                value_a=str(cf_inc_date),
                source_a="Claim Form -> incident_date",
                value_b=str(re_inc_date),
                source_b="Repair Estimate -> incident_date",
                impact_explanation="Date discrepancy prevents reliable evaluation of the policy claim reporting window (POLICY-05).",
                recommended_action="REQUEST CLARIFICATION from insured and garage regarding exact incident date."
            ))
            
        # 2. Amount Mismatch (Claim Form claimed_amount vs Repair Estimate estimated_cost)
        cf_amount = claim_form.get("claimed_amount", claim.claimed_amount)
        re_amount = repair_est.get("estimated_cost")
        
        if re_amount is not None and cf_amount is not None:
            try:
                cf_val = float(cf_amount)
                re_val = float(re_amount)
                if abs(cf_val - re_val) > 1000:
                    contradictions.append(ContradictionItem(
                        field_name="claimed_amount vs repair_estimate",
                        value_a=f"₹{cf_val:,.2f}",
                        source_a="Claim Form -> claimed_amount",
                        value_b=f"₹{re_val:,.2f}",
                        source_b="Repair Estimate -> estimated_cost",
                        impact_explanation=f"Claim form amount differs from garage repair estimate by ₹{abs(cf_val - re_val):,.2f}.",
                        recommended_action="REQUEST ITEMIZED BREAKDOWN from repair garage to reconcile claimed cost."
                    ))
            except (ValueError, TypeError):
                pass

        # 3. Vehicle Variant Mismatch (Claim Form vs Repair Estimate vs RC)
        cf_model = str(claim_form.get("vehicle_model", claim.vehicle_model)).strip()
        re_model = str(repair_est.get("vehicle_model", "")).strip()
        rc_model = str(rc_doc.get("vehicle_model", "")).strip()
        
        if re_model and cf_model and re_model.lower() != cf_model.lower():
            contradictions.append(ContradictionItem(
                field_name="vehicle_model / variant",
                value_a=cf_model,
                source_a="Claim Form -> vehicle_model",
                value_b=re_model,
                source_b="Repair Estimate -> vehicle_model",
                impact_explanation="Sub-variant discrepancy between claim form and garage estimate could impact IDV assessment and part eligibility.",
                recommended_action="VERIFY vehicle Registration Certificate (RC) to confirm exact factory variant."
            ))
            
        # 4. Registration Number Mismatch
        cf_reg = str(claim_form.get("registration_number", claim.registration_number)).replace("-", "").replace(" ", "").upper()
        re_reg = str(repair_est.get("registration_number", "")).replace("-", "").replace(" ", "").upper()
        rc_reg = str(rc_doc.get("registration_number", "")).replace("-", "").replace(" ", "").upper()
        
        if re_reg and cf_reg and re_reg != cf_reg:
            contradictions.append(ContradictionItem(
                field_name="registration_number",
                value_a=claim_form.get("registration_number", claim.registration_number),
                source_a="Claim Form -> registration_number",
                value_b=repair_est.get("registration_number"),
                source_b="Repair Estimate -> registration_number",
                impact_explanation="Registration number mismatch between claim form and garage estimate indicates potential document mix-up.",
                recommended_action="HALT PROCESSING and request verified copy of repair estimate with correct vehicle registration."
            ))

        # 5. Narrative Cause vs Repair Estimate Parts Contradiction
        desc_lower = claim.customer_description.lower()
        if repair_est and ("water" in desc_lower or "submergence" in desc_lower or "flood" in desc_lower):
            parts = repair_est.get("parts_list", [])
            parts_str = " ".join([str(p).lower() for p in parts])
            if "axle" in parts_str or "impact" in parts_str or "chassis" in parts_str or "bumper" in parts_str:
                contradictions.append(ContradictionItem(
                    field_name="incident_cause vs mechanical_damage",
                    value_a="Submergence / Hydrolock / Flood stalling",
                    source_a="Customer Narrative -> description",
                    value_b=f"Impact parts: {', '.join(parts[:3])}",
                    source_b="Repair Estimate -> parts_list",
                    impact_explanation="Customer describes pure water submergence/stalling, but repair estimate includes structural impact damage (axle/chassis bend) inconsistent with stagnant water.",
                    recommended_action="ESCALATE TO FIELD SURVEYOR for physical inspection of collision marks."
                ))
                
        return contradictions
