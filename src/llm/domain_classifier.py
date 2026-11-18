"""Strict IT Scope and Domain Classification System for QuickFixer.

Provides semantic classification into 13 supported IT categories and out-of-scope detection:
- ACCOUNT_AUTHENTICATION
- NETWORK_CONNECTIVITY
- VPN
- EMAIL_COLLABORATION
- SOFTWARE_APPLICATION
- HARDWARE
- OPERATING_SYSTEM
- CYBERSECURITY
- ACCESS_PERMISSIONS
- CLOUD_SERVICES
- DATABASE
- OTHER_IT_SUPPORT
- OUT_OF_SCOPE
- NEEDS_CLARIFICATION

Uses Google Gemini LLM with Pydantic structured output, backed by a comprehensive
offline semantic classifier for deterministic guardrails.
"""

from __future__ import annotations

import re
import json
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


OUT_OF_SCOPE_MESSAGE = (
    "Your question does not appear to be related to IT support or a technical system issue. "
    "Please describe your IT problem again, and I'll help you troubleshoot it."
)


class ITDomainCategory(str, Enum):
    """Supported IT domain categories and scope boundaries."""
    ACCOUNT_AUTHENTICATION = "ACCOUNT_AUTHENTICATION"
    NETWORK_CONNECTIVITY = "NETWORK_CONNECTIVITY"
    VPN = "VPN"
    EMAIL_COLLABORATION = "EMAIL_COLLABORATION"
    SOFTWARE_APPLICATION = "SOFTWARE_APPLICATION"
    HARDWARE = "HARDWARE"
    OPERATING_SYSTEM = "OPERATING_SYSTEM"
    CYBERSECURITY = "CYBERSECURITY"
    ACCESS_PERMISSIONS = "ACCESS_PERMISSIONS"
    CLOUD_SERVICES = "CLOUD_SERVICES"
    DATABASE = "DATABASE"
    OTHER_IT_SUPPORT = "OTHER_IT_SUPPORT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class DomainClassification(BaseModel):
    """Structured Pydantic response for query semantic classification."""
    is_it_related: bool = True
    category: str = ITDomainCategory.OTHER_IT_SUPPORT.value
    subcategory: Optional[str] = None
    intent: str = "TROUBLESHOOTING"  # TROUBLESHOOTING, TICKET_CREATION, TICKET_STATUS, SECURITY_INCIDENT, GENERAL_INQUIRY, OUT_OF_SCOPE
    confidence: float = 0.95
    reason: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
    clarification_questions: List[str] = Field(default_factory=list)


class DomainClassifier:
    """Classifies user queries into enterprise IT domains and detects out-of-scope prompts."""

    # Explicit out-of-scope topic triggers (politics, trivia, entertainment, sports, creative writing, cooking, etc.)
    OUT_OF_SCOPE_TRIGGERS: List[str] = [
        r"\b(priminister|primeminister|priministed|prime\s*minister|chief\s*minister|president|minister|politician|parliament|governor|king|queen|election|elections|politics|political)\b",
        r"\b(narendra\s*modi|modi|rahul\s*gandhi|trump|biden)\b",
        r"\b(pm|cm)\s+(of|problem|election|speech|candidate|issue)\b",
        r"\b(pm|cm)\b(?!\s+(prompt|ticket|queue))",
        r"\bwho\s+is\s+(the\s+)?(cm|pm|president|prime minister|chief minister|governor|king|queen)\b",
        r"\bwho\s+(was|is)\s+(the\s+)?(president|prime minister)\b",
        r"\bwho\s+won\s+(the\s+)?(match|election|world cup|ipl|game)\b",
        r"\b(cricket|football|basketball|tennis|ipl|fifa)\b",
        r"\b(tourist|tourism|vacation|holiday)\s+(place|spot|destination)\b",
        r"\bbest\s+place\s+to\s+visit\b",
        r"\btell\s+me\s+a\s+joke\b",
        r"\bwrite\s+a\s+(poem|story|song|essay)\b",
        r"\brecipe\s+for\b",
        r"\bhow\s+to\s+cook\b",
        r"\bcapital\s+of\b",
        r"\bweather\s+in\b",
        r"\b(movie|cinema|actor|actress|celebrity|horoscope)\b",
        r"\bmeaning\s+of\s+life\b",
    ]

    # Category heuristic keywords for offline semantic matching
    CATEGORY_PATTERNS: Dict[ITDomainCategory, List[str]] = {
        ITDomainCategory.VPN: [
            "vpn", "anyconnect", "cisco vpn", "globalprotect", "openvpn", "wireguard",
            "vpn connection", "vpn timed out", "vpn drops", "secure gateway"
        ],
        ITDomainCategory.NETWORK_CONNECTIVITY: [
            "wifi", "wi-fi", "wireless", "internet", "dns", "dns server", "ip address",
            "dhcp", "subnet", "ping", "ethernet", "lan", "connection timed out",
            "network slow", "cannot connect to network", "no internet", "gateway not responding",
            "packet loss", "router"
        ],
        ITDomainCategory.ACCOUNT_AUTHENTICATION: [
            "login", "log in", "sign in", "signin", "password", "passcode", "mfa", "2fa",
            "authenticator", "otp", "token", "locked out", "lockout", "account locked",
            "account is locked", "is locked", "temporary access pass", "reset password",
            "change password", "sso", "okta", "entra", "active directory", "credentials",
            "bad password", "cannot enter my account", "not able to enter", "not receiving an otp",
            "otp not arriving", "auth failed"
        ],
        ITDomainCategory.EMAIL_COLLABORATION: [
            "outlook", "email", "e-mail", "mail", "mailbox", "teams", "microsoft teams",
            "exchange", "ost", "pst", "shared mailbox", "cached exchange", "calendar",
            "meeting invite", "mail not going", "cannot send email", "outlook is not sending",
            "teams voice", "teams microphone", "teams audio", "teams call", "office 365", "m365"
        ],
        ITDomainCategory.OPERATING_SYSTEM: [
            "system stuck", "stuck suddenly", "switched off", "suddenly switched off",
            "swirched of", "shut down", "shutdown", "laptop freezes", "freezes frequently",
            "blue screen", "bsod", "system crash", "critical crash", "kernel-power", "kernel power",
            "kernel panic", "kernel", "event 41", "event id 41", "crash dump", "minidump",
            "windows error", "driver", "system slow", "slow performance", "reboot loop",
            "windows update", "sfc /scannow", "dism", "task manager", "high cpu", "operating system"
        ],
        ITDomainCategory.HARDWARE: [
            "printer", "print spooler", "printer offline", "paper jam", "monitor", "dock",
            "docking station", "keyboard", "mouse", "camera", "webcam", "microphone",
            "mic not working", "headset", "speaker", "usb-c", "hdmi", "charger", "overheating",
            "laptop is overheating", "fan noise", "physical defect", "battery swollen"
        ],
        ITDomainCategory.SOFTWARE_APPLICATION: [
            "docker", "install", "installation", "admin rights", "administrator rights",
            "epm", "privilege", "company portal", "license", "licensing", "intune",
            "visual studio", "application crashes", "app crash", "browser error", "chrome",
            "edge", "application error", "software update"
        ],
        ITDomainCategory.CYBERSECURITY: [
            "phishing", "suspicious email", "malware", "virus", "ransomware", "trojan",
            "bitlocker", "recovery key", "unauthorized access", "suspicious login",
            "suspicious login alert", "security alert", "security warning", "hacked", "breach"
        ],
        ITDomainCategory.ACCESS_PERMISSIONS: [
            "shared folder", "shared folder says access denied", "access denied",
            "file share", "network file share", "network share", "file access",
            "permission denied", "sharepoint", "onedrive", "access request",
            "folder access", "restricted folder", "security group"
        ],
        ITDomainCategory.CLOUD_SERVICES: [
            "aws", "azure", "gcp", "cloud", "s3 bucket", "ec2", "virtual machine",
            "cloud portal", "kubernetes", "cloud deployment"
        ],
        ITDomainCategory.DATABASE: [
            "database", "sql", "sqlite", "postgres", "mysql", "mongodb", "db connection",
            "query timeout", "table lock", "database down"
        ],
    }

    def __init__(self, gemini_client: Optional[Any] = None):
        self.gemini_client = gemini_client

    def classify(self, query: str) -> DomainClassification:
        """Classify a query using Gemini if available, or strict offline semantic rules."""
        cleaned = query.strip()
        if not cleaned:
            return DomainClassification(
                is_it_related=False,
                category=ITDomainCategory.OUT_OF_SCOPE.value,
                intent="OUT_OF_SCOPE",
                confidence=1.0,
                reason="Empty query",
            )

        # 1. Fast, deterministic out-of-scope regex check
        if self._is_explicitly_out_of_scope(cleaned):
            return DomainClassification(
                is_it_related=False,
                category=ITDomainCategory.OUT_OF_SCOPE.value,
                intent="OUT_OF_SCOPE",
                confidence=0.99,
                reason="The question is unrelated to enterprise IT support",
            )

        # 2. Try Gemini LLM for structured semantic classification if configured
        if self.gemini_client and getattr(self.gemini_client, "is_configured", lambda: False)():
            llm_result = self._classify_with_gemini(cleaned)
            if llm_result:
                return llm_result

        # 3. Offline semantic classification fallback
        return self._classify_offline(cleaned)

    def _is_explicitly_out_of_scope(self, query: str) -> bool:
        """Check for unambiguous non-IT queries."""
        q_lower = query.lower()
        for pattern in self.OUT_OF_SCOPE_TRIGGERS:
            if re.search(pattern, q_lower):
                return True
        return False

    def _classify_with_gemini(self, query: str) -> Optional[DomainClassification]:
        """Invoke Gemini Chat model with structured Pydantic JSON output."""
        try:
            prompt = (
                "You are QuickFix AI's strict IT Scope & Domain Classifier. "
                "Analyze the user's message and determine whether it is an IT support/technical issue. "
                "Classify it into one of the following categories:\n"
                "- ACCOUNT_AUTHENTICATION (Windows login, password, MFA, OTP, SSO, lockout)\n"
                "- NETWORK_CONNECTIVITY (Wi-Fi, internet, DNS, slow network)\n"
                "- VPN (AnyConnect, GlobalProtect, VPN tunnel)\n"
                "- EMAIL_COLLABORATION (Outlook, email sending/receiving, Teams, calendar)\n"
                "- SOFTWARE_APPLICATION (App crashes, installation, license, browser errors)\n"
                "- HARDWARE (Laptops, printers, monitors, docks, peripherals, overheating)\n"
                "- OPERATING_SYSTEM (Windows errors, blue screen BSOD, unexpected computer shutdown, freezing)\n"
                "- CYBERSECURITY (Phishing, malware, suspicious login, unauthorized access, BitLocker)\n"
                "- ACCESS_PERMISSIONS (Shared folder, access denied, permissions request)\n"
                "- CLOUD_SERVICES (Azure, AWS, Cloud VMs)\n"
                "- DATABASE (SQL, database connectivity)\n"
                "- OTHER_IT_SUPPORT (General corporate IT questions)\n"
                "- OUT_OF_SCOPE (Non-IT queries: politics, weather, recipes, trivia, jokes, poems, sports, general chat)\n\n"
                "IMPORTANT RULES:\n"
                "1. If the question is about unexpected shutdown, freezing, or blue screen: category is OPERATING_SYSTEM, subcategory is UNEXPECTED_SHUTDOWN, needs_clarification is true.\n"
                "2. If the question is non-IT (e.g. 'pm of india', 'who is the president of India', 'tell me a joke'): is_it_related is false, category is OUT_OF_SCOPE.\n"
                "3. Cybersecurity issues (phishing, malware, suspicious login) are strictly IT-related.\n\n"
                f"USER QUERY: \"{query}\"\n\n"
                "Respond with pure valid JSON matching this schema:\n"
                "{\n"
                '  "is_it_related": boolean,\n'
                '  "category": string,\n'
                '  "subcategory": string or null,\n'
                '  "intent": "TROUBLESHOOTING" | "TICKET_CREATION" | "TICKET_STATUS" | "SECURITY_INCIDENT" | "GENERAL_INQUIRY" | "OUT_OF_SCOPE",\n'
                '  "confidence": float between 0.0 and 1.0,\n'
                '  "reason": string,\n'
                '  "entities": { "application": string, "device": string, "error_code": string },\n'
                '  "needs_clarification": boolean,\n'
                '  "clarification_prompt": string or null,\n'
                '  "clarification_questions": [string]\n'
                "}"
            )
            raw = self.gemini_client.generate_json(prompt)
            if raw and isinstance(raw, dict):
                return DomainClassification(**raw)
        except Exception:
            pass
        return None

    def _classify_offline(self, query: str) -> DomainClassification:
        """Robust offline rule-based semantic classification."""
        q_lower = query.lower()

        # Check for Ticket Status intent
        if re.search(r"\btick-\d+\b", q_lower) or any(w in q_lower for w in ["status of", "check ticket", "ticket status"]):
            ticket_id_match = re.search(r"tick-\d+", q_lower, re.IGNORECASE)
            ticket_id = ticket_id_match.group(0).upper() if ticket_id_match else None
            return DomainClassification(
                is_it_related=True,
                category=ITDomainCategory.OTHER_IT_SUPPORT.value,
                intent="TICKET_STATUS",
                confidence=0.99,
                entities={"ticket_id": ticket_id} if ticket_id else {},
            )

        # Check for explicit Ticket Creation intent
        is_ticket_creation = bool(re.search(r"\b(create|open|raise|submit|escalate|log)\b.*\b(ticket|incident|case)\b", q_lower))

        # Check for Security Incident
        if any(w in q_lower for w in ["phishing", "ransomware", "malware", "virus", "hacked", "security alert", "suspicious email", "suspicious login"]):
            return DomainClassification(
                is_it_related=True,
                category=ITDomainCategory.CYBERSECURITY.value,
                subcategory="SECURITY_INCIDENT",
                intent="SECURITY_INCIDENT",
                confidence=0.98,
                entities={"threat_type": "security_incident"},
            )

        # Check for Unexpected Computer Shutdown / System Freeze (BUG 2)
        shutdown_indicators = [
            "swirched of", "switched off", "power off", "stuck suddenly and switched off",
            "suddenly switched off", "suddenly shut down", "laptop suddenly switched off",
            "freezes frequently", "blue screen", "bsod", "system crash", "critical crash",
            "kernel-power", "kernel power", "event 41", "event id 41"
        ]
        if any(term in q_lower for term in shutdown_indicators) or (("stuck" in q_lower or "froze" in q_lower or "freeze" in q_lower) and ("off" in q_lower or "shut" in q_lower)):
            return DomainClassification(
                is_it_related=True,
                category=ITDomainCategory.OPERATING_SYSTEM.value,
                subcategory="UNEXPECTED_SHUTDOWN",
                intent="TROUBLESHOOTING",
                confidence=0.96,
                needs_clarification=True,
                clarification_prompt="Your computer experienced an unexpected shutdown. Please help clarify:",
                clarification_questions=[
                    "Did the system freeze or become unresponsive before shutting down?",
                    "Did the computer restart automatically, or did it stay powered off?",
                    "Did a blue screen (BSOD) or error code appear?",
                    "Was the laptop running hot / fan spinning loudly (overheating)?",
                    "Was the device connected to its AC power charger during the shutdown?",
                ],
                entities={"device": "Workstation", "issue_type": "unexpected_shutdown"},
            )

        # Check for VPN specifically before general network
        if any(w in q_lower for w in self.CATEGORY_PATTERNS[ITDomainCategory.VPN]):
            return DomainClassification(
                is_it_related=True,
                category=ITDomainCategory.VPN.value,
                subcategory="VPN_CONNECTIVITY",
                intent="TICKET_CREATION" if is_ticket_creation else "TROUBLESHOOTING",
                confidence=0.95,
                entities={"application": "VPN"},
            )

        # Score matching categories
        category_scores: Dict[ITDomainCategory, int] = {}
        for cat, keywords in self.CATEGORY_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in q_lower)
            if matches > 0:
                category_scores[cat] = matches

        # Detect extracted entities
        entities: Dict[str, Any] = {}
        if "windows" in q_lower:
            entities["os"] = "Windows"
        if "mac" in q_lower or "macos" in q_lower:
            entities["os"] = "macOS"
        if "outlook" in q_lower:
            entities["application"] = "Outlook"
        elif "teams" in q_lower:
            entities["application"] = "Microsoft Teams"
        elif "docker" in q_lower:
            entities["application"] = "Docker"
        elif "printer" in q_lower:
            entities["device"] = "Printer"
        elif "laptop" in q_lower:
            entities["device"] = "Laptop"

        if category_scores:
            best_cat = max(category_scores.items(), key=lambda x: x[1])[0]
            intent = "TICKET_CREATION" if is_ticket_creation else "TROUBLESHOOTING"
            return DomainClassification(
                is_it_related=True,
                category=best_cat.value,
                intent=intent,
                confidence=0.92,
                entities=entities,
            )

        # Check for vague / ambiguous problem queries that need clarification
        vague_patterns = [
            r"^(i\s+have\s+(a\s+|some\s+)?)?problen?ms?\.?$",
            r"^(i\s+have\s+(an?\s+|some\s+)?)?issues?\.?$",
            r"^(i\s+(am\s+)?(facing|getting|having)\s+(a\s+|some\s+)?)?problen?ms?\.?$",
            r"^(i\s+(am\s+)?(facing|getting|having)\s+(an?\s+|some\s+)?)?issues?\.?$",
            r"^(my\s+)?(system|computer|pc|laptop|device|it)\s+(has\s+(a\s+|some\s+)?)?(problen?ms?|issues?)\.?$",
            r"^(system|computer|laptop|it|technical)\s+problen?ms?\.?$",
            r"^(getting|facing|got)\s+(an?\s+)?error\.?$",
            r"^(it\s+is\s+|it's\s+)?not\s+working\.?$",
            r"^(help|help\s+me|assist\s+me|need\s+help|support)\.?$",
            r"^(something\s+is\s+)?(wrong|broken)\.?$",
        ]
        tokens = [t for t in re.findall(r"\w+", q_lower) if t not in {"i", "a", "an", "the", "have", "my", "is", "am", "with", "in"}]
        is_vague = any(re.search(pat, q_lower) for pat in vague_patterns) or (
            len(tokens) <= 3 and any(w in tokens for w in ["problem", "problenm", "issue", "issues", "error", "help"])
        )
        if is_vague:
            return DomainClassification(
                is_it_related=True,
                category=ITDomainCategory.NEEDS_CLARIFICATION.value,
                intent="NEEDS_CLARIFICATION",
                confidence=0.98,
                needs_clarification=True,
                clarification_prompt="Could you please specify which type of IT problem you are facing?",
                clarification_questions=[
                    "Windows Login, Password, or MFA Authenticator issue?",
                    "Network, Wi-Fi, or Internet connection issue?",
                    "Cisco AnyConnect or GlobalProtect VPN issue?",
                    "Outlook email sending/receiving or Microsoft Teams issue?",
                    "Operating System crash, Blue Screen (BSOD), or unexpected shutdown?",
                    "Printer, external monitor, or docking station issue?",
                    "Application crash or software installation failure?",
                    "Shared network folder or SharePoint access permissions?",
                ],
                reason="User stated a generic problem without specifying symptoms, application, or device.",
            )

        # Check if generic IT question or truly out of scope
        generic_it_words = [
            "computer", "system", "pc", "device", "server", "port", "error", "issue",
            "problem", "not working", "fails", "failed", "crash", "frozen", "slow",
            "restart", "reboot", "admin", "it support", "service desk", "helpdesk",
            "setup", "configure", "install", "update", "cable", "software"
        ]
        if any(w in q_lower for w in generic_it_words):
            return DomainClassification(
                is_it_related=True,
                category=ITDomainCategory.OTHER_IT_SUPPORT.value,
                intent="TROUBLESHOOTING",
                confidence=0.75,
                entities=entities,
            )

        # Default to OUT_OF_SCOPE for non-IT questions
        return DomainClassification(
            is_it_related=False,
            category=ITDomainCategory.OUT_OF_SCOPE.value,
            intent="OUT_OF_SCOPE",
            confidence=0.95,
            reason="The question is unrelated to enterprise IT support",
        )
