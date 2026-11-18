"""Intelligent Query Rewriting Engine for QuickFixer.

Translates informal, conversational, or typo-ridden employee technical reports
into high-precision technical diagnostic search queries for FAISS RAG retrieval.
"""

from __future__ import annotations

import re
from typing import Optional, Any
from src.llm.domain_classifier import DomainClassification, ITDomainCategory


class QueryRewriter:
    """Transforms informal IT issue descriptions into structured technical search queries."""

    # Heuristic domain expansion templates for offline / fast path
    OFFLINE_REWRITE_RULES = [
        (
            r"(swirched of|switched off|power off|shut down|shutdown|stuck suddenly and switched off|system got off suddenly)",
            "Computer system unexpected shutdown and power failure while in operation",
        ),
        (
            r"(freez|hanging|frozen|system is hanging)",
            "Computer freezing, performance degradation, and system unresponsiveness",
        ),
        (
            r"(blue screen|bsod)",
            "Windows blue screen BSOD crash stop error and kernel panic",
        ),
        (
            r"overheat",
            "Laptop hardware overheating, cooling fan issue, and thermal cut-off",
        ),
        (
            r"laptop.*(not opening|won'?t open|won'?t start|not starting|black screen|dead)",
            "Laptop hardware startup failure, battery depleted, AC adapter fault, or power delivery issue",
        ),
        (
            r"(not able to enter|cannot enter|can'?t enter|unable to login|cannot login|locked out).*(account|system|office|laptop|company)",
            "Corporate account authentication failure, Windows login error, password verification, and account lockout",
        ),
        (
            r"(otp|authenticator).*(not arriving|not receiving|not working)",
            "MFA multi-factor authenticator OTP challenge verification failure",
        ),
        (
            r"mail.*(not going|not sending|stuck|cannot send|failed to send)|outlook.*(not sending)",
            "Outlook email sending failure, Outbox queue hang, and Exchange server connection",
        ),
        (
            r"(teams).*(voice|audio|mic|microphone|sound|call|cannot hear).*(not working|broken|failing)?",
            "Microsoft Teams microphone and audio device failure and call peripheral troubleshooting",
        ),
        (
            r"(wifi|wi-fi|internet).*(not working|disconnected|dropping|slow|keeps disconnecting)",
            "Corporate Wi-Fi wireless connectivity drop, DHCP IP address renewal, and network adapter reset",
        ),
        (
            r"dns.*(not responding|server)",
            "DNS server resolution failure, local DNS cache flush, and gateway reachability",
        ),
        (
            r"(printer|printing).*(offline|stuck|queue|not printing)",
            "Network printer offline error, print spooler service freeze, and print queue purge",
        ),
        (
            r"vpn.*(timeout|fail|drop|disconnect|handshake|not connecting)",
            "Cisco AnyConnect or GlobalProtect VPN gateway timeout, TLS handshake failure, and tunnel reconnect",
        ),
        (
            r"(phishing|suspicious login|suspicious email|unauthorized access|malware)",
            "Suspicious login alert, unauthorized account access, and phishing security incident",
        ),
        (
            r"(shared folder|access denied|permission denied)",
            "Shared folder network access denied and Active Directory permission authorization",
        ),
        (
            r"(application crashes|app crash|software crash)",
            "Software application crash and process exception fault",
        ),
    ]

    def __init__(self, gemini_client: Optional[Any] = None):
        self.gemini_client = gemini_client

    def rewrite(self, query: str, classification: Optional[DomainClassification] = None) -> str:
        """Rewrite informal employee prompt into a technical search query."""
        cleaned = query.strip()
        if not cleaned:
            return ""

        # If query was detected as out of scope, do not rewrite
        if classification and not classification.is_it_related:
            return cleaned

        # 1. Try Gemini LLM for dynamic context-aware semantic query reformulation
        if self.gemini_client and getattr(self.gemini_client, "is_configured", lambda: False)():
            llm_rewritten = self._rewrite_with_gemini(cleaned, classification)
            if llm_rewritten:
                return llm_rewritten

        # 2. Offline rule-based semantic rewriting
        return self._rewrite_offline(cleaned, classification)

    def _rewrite_with_gemini(
        self, query: str, classification: Optional[DomainClassification] = None
    ) -> Optional[str]:
        """Invoke Gemini Chat model to produce high-precision technical search terms."""
        try:
            category_hint = f"Category: {classification.category}" if classification else ""
            prompt = (
                "You are an enterprise IT knowledge retrieval specialist. "
                "An employee reported a technical issue using informal or imprecise language. "
                "Rewrite the problem into a dense, high-precision technical search query "
                "containing standard diagnostic terms, error names, and remediation keywords for runbook retrieval.\n\n"
                f"{category_hint}\n"
                f"Original Employee Issue: \"{query}\"\n\n"
                "Provide ONLY the rewritten technical search query string. Do not include quotes, preamble, or markdown."
            )
            response = self.gemini_client.generate_response(
                user_message=prompt,
                conversation_history=[],
                rag_context="",
            )
            if response and response.strip():
                # Clean up any quotes or markdown
                clean = response.strip().replace('"', '').replace("'", "")
                if len(clean) > 10:
                    return clean
        except Exception:
            pass
        return None

    def _rewrite_offline(
        self, query: str, classification: Optional[DomainClassification] = None
    ) -> str:
        """Apply deterministic semantic expansion patterns."""
        q_lower = query.lower()

        # Check explicit regex rules
        for pattern, technical_query in self.OFFLINE_REWRITE_RULES:
            if re.search(pattern, q_lower):
                return technical_query

        # Fallback expansion based on classified category
        if classification and classification.category:
            cat = classification.category
            if cat == ITDomainCategory.HARDWARE.value:
                return f"{query} - Laptop workstation hardware fault, power supply, peripheral device, or physical component failure"
            elif cat == ITDomainCategory.ACCOUNT_AUTHENTICATION.value:
                return f"{query} - Account login failure, Active Directory lockout, password reset, and MFA authenticator verification"
            elif cat == ITDomainCategory.NETWORK_CONNECTIVITY.value:
                return f"{query} - Network connection failure, Wi-Fi or VPN gateway routing, IP configuration and DNS troubleshooting"
            elif cat == ITDomainCategory.EMAIL_COLLABORATION.value:
                return f"{query} - Microsoft Outlook, Exchange server connection, Teams collaboration and mailbox sync error"
            elif cat == ITDomainCategory.OPERATING_SYSTEM.value:
                return f"{query} - Windows OS stop error, BSOD crash dump, corrupted system files, and hardware memory diagnostics"
            elif cat == ITDomainCategory.CYBERSECURITY.value:
                return f"{query} - Security alert, suspicious phishing email, malware isolation, and BitLocker recovery"
            elif cat == ITDomainCategory.ACCESS_PERMISSIONS.value:
                return f"{query} - Shared folder access denied, NTFS file permissions, and Active Directory security group authorization"

        return query

