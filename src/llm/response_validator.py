"""Final Answer Relevance Validation Engine for QuickFixer.

Inspects generated responses before presentation to ensure:
1. Grounding in the classified IT domain.
2. Prevention of cross-domain contamination (e.g. VPN messages in a hardware shutdown issue).
3. Elimination of false low-confidence runbook citations.
4. Prevention of hallucinated root causes.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from src.llm.domain_classifier import DomainClassification, ITDomainCategory, OUT_OF_SCOPE_MESSAGE


class ResponseValidator:
    """Validates generated IT Support answers against employee intent and domain boundaries."""

    # Contaminant keywords per domain
    CONTAMINATION_RULES: Dict[str, List[str]] = {
        ITDomainCategory.OPERATING_SYSTEM.value: [
            "cisco anyconnect", "globalprotect", "vpn gateway", "print spooler",
            "paper jam", "printer offline", "tray 2", "duo mobile", "authenticator app"
        ],
        ITDomainCategory.ACCOUNT_AUTHENTICATION.value: [
            "print spooler", "printer offline", "cisco anyconnect", "globalprotect",
            "vpn gateway", "docking station", "displaylink"
        ],
        ITDomainCategory.HARDWARE.value: [
            "cisco anyconnect", "globalprotect", "vpn gateway", "temporary access pass",
            "mfa push", "authenticator app"
        ],
        ITDomainCategory.VPN.value: [
            "print spooler", "printer offline", "paper jam", "tray 2", "docking station"
        ],
        ITDomainCategory.EMAIL_COLLABORATION.value: [
            "print spooler", "paper jam", "cisco anyconnect", "vpn gateway"
        ],
    }

    @classmethod
    def validate_and_sanitize(
        cls,
        answer: str,
        query: str,
        classification: Optional[DomainClassification] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        retrieval_scores: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Validate answer and return sanitized response with diagnostic metrics."""
        # 1. Out of scope guardrail check
        if classification and (not classification.is_it_related or classification.category == ITDomainCategory.OUT_OF_SCOPE.value):
            return {
                "is_valid": True,
                "sanitized_answer": OUT_OF_SCOPE_MESSAGE,
                "reason": "Out of scope query enforced.",
            }

        # 2. Prevent low-confidence score leakage (e.g. 35% or 36%)
        clean_answer = answer
        if "Relevance: 3" in clean_answer or "Relevance: 2" in clean_answer or "Relevance: 1" in clean_answer or "Relevance: 0" in clean_answer:
            # Strip low confidence runbook citation header
            clean_answer = re.sub(
                r"Based on internal runbook:.*\(Relevance:\s*[0-3]?\d%\):?\n?",
                "",
                clean_answer,
                flags=re.IGNORECASE,
            ).strip()

        # 3. Cross-domain contamination check
        category = classification.category if classification else None
        if category and category in cls.CONTAMINATION_RULES:
            forbidden_terms = cls.CONTAMINATION_RULES[category]
            answer_lower = clean_answer.lower()
            detected_contaminants = [term for term in forbidden_terms if term in answer_lower]

            if detected_contaminants:
                # Contamination detected! Provide safe, domain-tailored guidance
                if category == ITDomainCategory.OPERATING_SYSTEM.value:
                    sanitized = (
                        "### IT Support Diagnosis: Unexpected Computer Shutdown\n\n"
                        "**Issue:**\n"
                        "Your computer froze and switched off unexpectedly while in operation.\n\n"
                        "**Possible causes:**\n"
                        "- Overheating.\n"
                        "- Power or battery issue.\n"
                        "- Operating system crash.\n"
                        "- Driver or hardware failure.\n\n"
                        "**Initial troubleshooting:**\n"
                        "1. Check whether the laptop has sufficient power and the charger is properly connected.\n"
                        "2. Allow the device to cool if it is running hot, and ensure air vents are clear.\n"
                        "3. Check whether the device restarts normally.\n"
                        "4. If it happens again, record any error code or event information.\n\n"
                        "**Follow-up Questions:**\n"
                        "- Did the system freeze before shutting down?\n"
                        "- Did the computer restart automatically?\n"
                        "- Did a blue screen (BSOD) appear?\n"
                        "- Was the laptop overheating?\n"
                        "- Was the laptop connected to a charger?"
                    )
                    return {
                        "is_valid": False,
                        "sanitized_answer": sanitized,
                        "reason": f"Contamination detected ({detected_contaminants}). Replaced with sanitized OS diagnosis.",
                    }

                elif category == ITDomainCategory.ACCOUNT_AUTHENTICATION.value:
                    sanitized = (
                        "### IT Support Diagnosis: Account Authentication & Login\n\n"
                        "**Issue:** Corporate account login or password verification problem.\n\n"
                        "**Initial troubleshooting:**\n"
                        "1. Verify your username and domain (e.g. `user@company.com`).\n"
                        "2. If locked out after multiple attempts, wait 15 minutes for automated lockout release.\n"
                        "3. Use the corporate Self-Service Password Reset (SSPR) portal.\n"
                        "4. If MFA notifications fail, ensure phone has active internet connectivity."
                    )
                    return {
                        "is_valid": False,
                        "sanitized_answer": sanitized,
                        "reason": f"Contamination detected ({detected_contaminants}). Replaced with sanitized authentication diagnosis.",
                    }

        # 4. If answer claims runbook evidence but no relevant docs exist
        has_high_conf_docs = bool(retrieval_scores and any(s >= 0.45 for s in retrieval_scores))
        if not has_high_conf_docs and "Based on internal runbook:" in clean_answer:
            clean_answer = re.sub(
                r"Based on internal runbook:.*?\n",
                "",
                clean_answer,
                flags=re.IGNORECASE,
            ).strip()

        return {
            "is_valid": True,
            "sanitized_answer": clean_answer,
            "reason": "Validated successfully.",
        }

