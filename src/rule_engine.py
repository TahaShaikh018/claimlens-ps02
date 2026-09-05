from datetime import datetime
from typing import List, Dict, Any, Tuple
from src.schemas import ClaimPayload, DeterministicCheck

class DeterministicRuleEngine:
    """
    Executes strict Python deterministic rule checks separate from LLM reasoning.
    Covers: date differences, reporting windows, document completeness, IDV limits, deductibles.
    """
    
    @staticmethod
    def parse_date(date_str: str) -> datetime:
        """Parses YYYY-MM-DD format date safely."""
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                pass
        raise ValueError(f"Unable to parse date string: {date_str}")

    def evaluate_reporting_window(self, claim: ClaimPayload) -> DeterministicCheck:
        """Evaluates whether claim was reported within allowed policy window (POLICY-05)."""
        try:
            inc_dt = self.parse_date(claim.incident_date)
            rep_dt = self.parse_date(claim.report_date)
            days_elapsed = (rep_dt - inc_dt).days
            
            # Determine threshold
            if "theft" in claim.claim_type.lower():
                max_allowed_days = 1
                clause_id = "POLICY-05"
            else:
                max_allowed_days = 7
                clause_id = "POLICY-05"
                
            if days_elapsed < 0:
                return DeterministicCheck(
                    check_name="Claim Reporting Window Check",
                    passed=False,
                    details=f"Invalid date sequence: Report date ({claim.report_date}) precedes incident date ({claim.incident_date}).",
                    policy_clause_id=clause_id,
                    source_fields=["Claim Form -> incident_date", "Claim Form -> report_date"]
                )
                
            passed = days_elapsed <= max_allowed_days
            details = (
                f"Claim reported in {days_elapsed} day(s) after incident. "
                f"Allowed maximum window for '{claim.claim_type}' is {max_allowed_days} day(s)."
            )
            if not passed:
                details += f" EXCEEDED allowed reporting window by {days_elapsed - max_allowed_days} day(s)."
                
            return DeterministicCheck(
                check_name="Claim Reporting Window Check",
                passed=passed,
                details=details,
                policy_clause_id=clause_id,
                source_fields=["Claim Form -> incident_date", "Claim Form -> report_date"]
            )
        except Exception as e:
            return DeterministicCheck(
                check_name="Claim Reporting Window Check",
                passed=False,
                details=f"Error evaluating date fields: {str(e)}",
                policy_clause_id="POLICY-05",
                source_fields=["Claim Form -> incident_date", "Claim Form -> report_date"]
            )

    def evaluate_required_documents(self, claim: ClaimPayload) -> Tuple[DeterministicCheck, List[str]]:
        """Evaluates submitted document completeness against POLICY-06 and POLICY-03."""
        submitted_types = set(doc.doc_type.strip() for doc in claim.submitted_documents)
        
        is_theft = "theft" in claim.claim_type.lower()
        
        if is_theft:
            required = ["Claim Form", "Police FIR", "Registration Certificate", "Driving License"]
            clause_id = "POLICY-03"
        else:
            required = ["Claim Form", "Repair Estimate", "Registration Certificate", "Driving License"]
            clause_id = "POLICY-06"
            
        missing = []
        for req in required:
            # Check loose match for Police FIR (e.g. "FIR", "Police FIR", "First Information Report")
            if req == "Police FIR":
                if not any("fir" in dt.lower() for dt in submitted_types):
                    missing.append("Police FIR")
            elif req == "Repair Estimate":
                if not any("repair" in dt.lower() or "estimate" in dt.lower() or "invoice" in dt.lower() for dt in submitted_types):
                    missing.append("Repair Estimate")
            elif req not in submitted_types:
                missing.append(req)
                
        passed = len(missing) == 0
        if passed:
            details = f"All {len(required)} mandatory documents present for {claim.claim_type} claim."
        else:
            details = f"Missing {len(missing)} required document(s): {', '.join(missing)}. Policy requires: {', '.join(required)}."
            
        check = DeterministicCheck(
            check_name="Document Completeness Check",
            passed=passed,
            details=details,
            policy_clause_id=clause_id,
            source_fields=["Submitted Documents Manifest"]
        )
        return check, missing

    def evaluate_idv_limits(self, claim: ClaimPayload) -> DeterministicCheck:
        """Evaluates claimed amount against Insured Declared Value (IDV) and CTL thresholds (POLICY-07)."""
        claimed = claim.claimed_amount
        idv = claim.insured_declared_value
        
        if idv <= 0:
            return DeterministicCheck(
                check_name="Insured Declared Value (IDV) Check",
                passed=False,
                details="Invalid Insured Declared Value specified (₹0 or negative).",
                policy_clause_id="POLICY-07",
                source_fields=["Policy Schedule -> insured_declared_value"]
            )
            
        ratio = claimed / idv
        pct = round(ratio * 100, 1)
        
        if claimed > idv:
            return DeterministicCheck(
                check_name="Insured Declared Value (IDV) Limit Check",
                passed=False,
                details=f"Claimed amount ₹{claimed:,.2f} exceeds IDV cap ₹{idv:,.2f} ({pct}% of IDV). Maximum payable is capped at IDV.",
                policy_clause_id="POLICY-07",
                source_fields=["Claim Form -> claimed_amount", "Policy Schedule -> insured_declared_value"]
            )
        elif ratio >= 0.75:
            return DeterministicCheck(
                check_name="Constructive Total Loss (CTL) Threshold Check",
                passed=True,
                details=f"Claimed amount ₹{claimed:,.2f} is {pct}% of IDV (₹{idv:,.2f}). Triggers Constructive Total Loss (CTL) assessment (>75% IDV).",
                policy_clause_id="POLICY-07",
                source_fields=["Repair Estimate -> estimated_cost", "Policy Schedule -> insured_declared_value"]
            )
        else:
            return DeterministicCheck(
                check_name="Insured Declared Value (IDV) Limit Check",
                passed=True,
                details=f"Claimed amount ₹{claimed:,.2f} is within IDV limit ₹{idv:,.2f} ({pct}% of IDV).",
                policy_clause_id="POLICY-07",
                source_fields=["Claim Form -> claimed_amount", "Policy Schedule -> insured_declared_value"]
            )

    def calculate_deductible(self, claim: ClaimPayload) -> Dict[str, Any]:
        """Calculates compulsory deductible per POLICY-08."""
        is_two_wheeler = "two" in claim.vehicle_type.lower() or "bike" in claim.vehicle_type.lower() or "motorcycle" in claim.vehicle_type.lower()
        deductible_amount = 1000.0 if is_two_wheeler else 2000.0
        
        estimated_payout = max(0.0, min(claim.claimed_amount, claim.insured_declared_value) - deductible_amount)
        
        return {
            "policy_clause_id": "POLICY-08",
            "vehicle_type": claim.vehicle_type,
            "deductible_amount": deductible_amount,
            "claimed_amount": claim.claimed_amount,
            "estimated_net_payout": estimated_payout,
            "explanation": f"Compulsory excess of ₹{deductible_amount:,.2f} applies for {claim.vehicle_type} per POLICY-08."
        }

    def run_all_checks(self, claim: ClaimPayload) -> Tuple[List[DeterministicCheck], List[str], Dict[str, Any]]:
        """Runs all deterministic Python checks and returns structured results."""
        checks = []
        
        # 1. Reporting window
        chk_window = self.evaluate_reporting_window(claim)
        checks.append(chk_window)
        
        # 2. Required docs
        chk_docs, missing_docs = self.evaluate_required_documents(claim)
        checks.append(chk_docs)
        
        # 3. IDV limit
        chk_idv = self.evaluate_idv_limits(claim)
        checks.append(chk_idv)
        
        # 4. Deductible info
        deductible_info = self.calculate_deductible(claim)
        
        return checks, missing_docs, deductible_info
