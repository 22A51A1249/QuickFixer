"""Offline diagnostic and triage engine.
Provides rule-based NLP, knowledge synthesis, and structured triage
when external LLM APIs are offline or unconfigured.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple, Optional
from src.models.ticket import TicketCategory, TicketPriority, TriageResult
from src.rag.document_loader import DocumentChunk


class OfflineDiagnosticEngine:
    """Intelligent fallback engine for diagnosis, RAG answer synthesis, and triage."""

    CATEGORY_KEYWORDS = {
        TicketCategory.NETWORK: [
            "vpn", "anyconnect", "globalprotect", "wifi", "wi-fi", "internet",
            "dns", "ip address", "dhcp", "subnet", "ping", "ethernet", "connection timed out"
        ],
        TicketCategory.ACCOUNT: [
            "password", "mfa", "authenticator", "otp", "token", "locked out",
            "login failed", "sso", "okta", "entra", "temporary access pass", "reset password"
        ],
        TicketCategory.EMAIL: [
            "outlook", "mailbox", "teams", "exchange", "ost", "pst",
            "shared mailbox", "cached exchange", "email", "meeting"
        ],
        TicketCategory.HARDWARE: [
            "printer", "print spooler", "monitor", "dock", "docking station",
            "displaylink", "hdmi", "usb-c", "keyboard", "mouse", "paper jam", "offline"
        ],
        TicketCategory.SOFTWARE: [
            "docker", "install", "admin rights", "privilege", "company portal",
            "license", "intune", "visual studio", "crash", "version"
        ],
        TicketCategory.SECURITY: [
            "phishing", "suspicious email", "malware", "virus", "bitlocker",
            "recovery key", "ransomware", "unauthorized", "security alert"
        ],
    }

    PRIORITY_CRITICAL_KEYWORDS = [
        "entire team", "company wide", "production down", "ransomware", "security incident",
        "breach", "locked out of everything", "emergency", "vip", "system down"
    ]
    PRIORITY_HIGH_KEYWORDS = [
        "cannot work", "blocked", "urgent", "asap", "crash", "bsod", "blue screen",
        "timeout", "deadline", "multiple users", "critical error", "locked out", "lockout",
        "locked", "mfa failed", "access denied"
    ]
    PRIORITY_LOW_KEYWORDS = [
        "how do i", "question", "inquiry", "request access", "when possible",
        "information", "setup guide", "recommendation"
    ]

    def classify_query_intent(self, query: str) -> str:
        """Rule-based query intent classification for offline mode."""
        q = query.lower()
        if re.search(r"\btick-\d+\b", q) or any(w in q for w in ["status of", "check ticket", "ticket status"]):
            return "ticket_status"
        if any(w in q for w in ["phishing", "ransomware", "malware", "virus", "hacked", "security alert", "suspicious email"]):
            return "security_incident"
        if re.search(r"\b(create|open|raise|submit|escalate|log)\b.*\b(ticket|incident|case)\b", q):
            return "ticket_creation"
        if any(w in q for w in ["what is the policy", "office hours", "how do i request", "guideline"]):
            return "general_inquiry"
        return "troubleshooting"

    def synthesize_response(
        self,
        user_query: str,
        retrieved_chunks: List[Tuple[DocumentChunk, float]],
        category: Optional[str] = None,
    ) -> str:
        """Synthesize an actionable IT Support solution based on top RAG chunks or domain knowledge."""
        q_lower = user_query.lower()

        # Check for low-confidence or empty retrieval
        top_chunk = retrieved_chunks[0][0] if retrieved_chunks else None
        top_score = retrieved_chunks[0][1] if retrieved_chunks else 0.0

        # 1. Unexpected Computer Shutdown / System Freeze (BUG 2 & Section 10 Rule 1)
        is_unexpected_shutdown = (
            any(w in q_lower for w in [
                "swirched of", "switched off", "power off", "shut down", "shutdown",
                "stuck suddenly", "laptop suddenly switched off", "system was stuck"
            ])
            or (category == "OPERATING_SYSTEM" and any(w in q_lower for w in ["freeze", "stuck", "switched", "shut", "crash", "power"]))
        )
        if is_unexpected_shutdown:
            runbook_header = f"Based on internal runbook: **{top_chunk.title}** (Relevance: {top_score:.0%}):\n\n" if (top_chunk and top_score >= 0.45) else ""
            return (
                "### IT Support Diagnosis: Unexpected Computer Shutdown & System Freeze\n\n"
                f"{runbook_header}"
                "**Identified Issue:**\n"
                "Your computer froze and switched off unexpectedly during operation.\n\n"
                "**Diagnostic Questions to Help Identify the Root Cause:**\n"
                "- Did the system freeze or become unresponsive before shutting down?\n"
                "- Did the computer restart automatically, or did it stay powered off?\n"
                "- Did a blue screen (BSOD) or error code appear?\n"
                "- Was the laptop overheating or was the cooling fan spinning loudly?\n"
                "- Was the laptop connected to a charger during the shutdown?\n\n"
                "**Recommended Remediation Steps:**\n"
                "1. **Power & Battery Verification:** Check whether the laptop has sufficient power and is connected to an authorized charger. Verify charging LED status.\n"
                "2. **Thermal Safety Inspection:** Allow the device to cool down for 15 minutes if it felt hot. Ensure ventilation grills and fan exhausts are clear.\n"
                "3. **Power On Test:** Check whether the device powers on and restarts normally.\n"
                "4. **Event Log & Crash Analysis:** Open Event Viewer (`eventvwr.msc`) and inspect Windows Logs > System for Event ID 41 (Kernel-Power) or minidump crash files.\n\n"
                "> [!NOTE]\n"
                "> If the device fails to restart, continuously shuts down, or shows thermal warnings, click **'Escalate to Ticket'** to assign a hardware technician immediately."
            )

        # If retrieval score is below 0.45 or chunks are missing, generate domain-tailored diagnosis
        if not retrieved_chunks or top_score < 0.45:
            # 2. Account / Authentication / Password / Lockout
            if any(w in q_lower for w in ["login", "password", "mfa", "locked", "cannot enter", "account", "authenticator", "sso"]) or category == "ACCOUNT_AUTHENTICATION":
                return (
                    "### IT Support Diagnosis: Account Authentication & Password\n\n"
                    "**Issue:**\n"
                    "Corporate account authentication, password verification, or lockout issue.\n\n"
                    "**Possible causes:**\n"
                    "- Expired corporate password.\n"
                    "- Active Directory account lockout from repeated failed attempts.\n"
                    "- MFA authenticator push notifications out of sync.\n\n"
                    "**Initial troubleshooting:**\n"
                    "1. Visit the Self-Service Password Reset (SSPR) portal at `https://passwordreset.microsoftonline.com`.\n"
                    "2. If locked out, wait 15 minutes for the automated security counter to reset.\n"
                    "3. Ensure your mobile phone has active internet connectivity to receive MFA notifications.\n"
                    "4. If phone was replaced, contact IT Service Desk for an emergency Temporary Access Pass (TAP).\n\n"
                    "> [!NOTE]\n"
                    "> If still unable to login, click **'Escalate to Ticket'** for identity verification and account unlock."
                )

            # 3. Email & Outlook
            elif any(w in q_lower for w in ["outlook", "email", "mail", "teams"]) or category == "EMAIL_COLLABORATION":
                return (
                    "### IT Support Diagnosis: Email & Collaboration\n\n"
                    "**Issue:**\n"
                    "Outlook email sending/receiving or Microsoft 365 collaboration application issue.\n\n"
                    "**Initial troubleshooting:**\n"
                    "1. Open Outlook in Safe Mode: press `Win + R`, type `outlook.exe /safe` and press Enter.\n"
                    "2. Check status bar in Outlook to verify connection to Microsoft Exchange.\n"
                    "3. Verify webmail access via browser at `https://outlook.office.com`.\n"
                    "4. If Teams audio fails, check Windows Settings -> Privacy -> Microphone permissions.\n\n"
                    "> [!NOTE]\n"
                    "> If the issue persists, click **'Escalate to Ticket'** to have a technician inspect your mailbox profile."
                )

            # 4. VPN
            elif any(w in q_lower for w in ["vpn", "anyconnect", "globalprotect"]) or category == "VPN":
                return (
                    "### IT Support Diagnosis: VPN Connection\n\n"
                    "**Issue:**\n"
                    "Cisco AnyConnect or GlobalProtect VPN tunnel connection failure.\n\n"
                    "**Initial troubleshooting:**\n"
                    "1. Disconnect and verify your public internet connection works in a browser.\n"
                    "2. Open Command Prompt as Administrator and flush DNS: `ipconfig /flushdns`.\n"
                    "3. Re-enter your corporate VPN gateway address and complete MFA prompt within 30 seconds.\n"
                    "4. If gateway times out, reboot your home Wi-Fi router.\n\n"
                    "> [!NOTE]\n"
                    "> If connection still fails, click **'Escalate to Ticket'** for network operations review."
                )

            # 5. Network / Wi-Fi
            elif any(w in q_lower for w in ["wifi", "wi-fi", "internet", "dns", "network"]) or category == "NETWORK_CONNECTIVITY":
                return (
                    "### IT Support Diagnosis: Network Connectivity & Wi-Fi\n\n"
                    "**Issue:**\n"
                    "Wireless network disconnection, IP address lease error, or DNS failure.\n\n"
                    "**Initial troubleshooting:**\n"
                    "1. Toggle Wi-Fi adapter off and on, or reconnect to corporate SSID.\n"
                    "2. Open Command Prompt as Administrator and run:\n"
                    "   ```cmd\n"
                    "   ipconfig /release\n"
                    "   ipconfig /renew\n"
                    "   ipconfig /flushdns\n"
                    "   ```\n"
                    "3. Restart the workstation to reset the TCP/IP stack.\n\n"
                    "> [!NOTE]\n"
                    "> If Wi-Fi still disconnects, click **'Escalate to Ticket'** for network specialist assistance."
                )

            # 6. Default General IT Support Guidance (Section 11)
            return (
                "I understand your IT issue, but I couldn't find a matching procedure in the company knowledge base. "
                "I can offer general troubleshooting guidance or help create an IT support ticket.\n\n"
                "**General Guidance:**\n"
                "1. Please verify device power, physical cable connections, and network reachability.\n"
                "2. Restart the affected application or reboot the workstation to clear transient system locks.\n"
                "3. Record any specific error codes, screenshots, or timestamps.\n"
                "4. Click **'Escalate to Ticket'** below to dispatch this directly to an IT Support Specialist."
            )

        # High-confidence chunk match: extract steps strictly from the top matching runbook
        steps: List[str] = []
        commands: List[str] = []
        primary_source = top_chunk.source

        for chunk, _ in retrieved_chunks:
            # Strictly prevent mixing steps across different runbook sources!
            if chunk.source != primary_source:
                continue

            lines = chunk.text.split("\n")
            in_code_block = False
            for line in lines:
                s_line = line.strip()
                if s_line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block and s_line:
                    commands.append(s_line)
                elif re.match(r"^(\d+\.|\-|\*)\s+", s_line):
                    clean_step = re.sub(r"^(\d+\.|\-|\*)\s+", "", s_line)
                    if len(clean_step) > 15 and clean_step not in steps:
                        steps.append(clean_step)

        # Assemble formatted response
        response_parts = [
            f"### IT Support Diagnosis & Recommended Fix\n",
            f"Based on internal runbook: **{top_chunk.title}** (Relevance: {top_score:.0%}):\n",
        ]

        if steps:
            response_parts.append("**Recommended Remediation Steps:**")
            for idx, step in enumerate(steps[:4], start=1):
                response_parts.append(f"{idx}. {step}")
            response_parts.append("")

        if commands:
            response_parts.append("**Suggested Command(s) to Run (Administrator Prompt):**")
            response_parts.append("```cmd\n" + "\n".join(commands[:4]) + "\n```\n")

        # Context-specific closing tip
        response_parts.append(
            "> [!NOTE]\n"
            "> After performing these steps, please restart the impacted application or network adapter. "
            "If the issue persists, click **'Escalate to Ticket'** to assign a technician immediately."
        )

        return "\n".join(response_parts)

    def triage_description(self, description: str) -> TriageResult:
        """Classify category, determine priority, and extract key entities using rules."""
        desc_lower = description.lower()

        # 1. Determine Category
        matched_category = TicketCategory.OTHER
        max_matches = 0

        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in desc_lower)
            if matches > max_matches:
                max_matches = matches
                matched_category = cat

        # 2. Determine Priority
        if any(kw in desc_lower for kw in self.PRIORITY_CRITICAL_KEYWORDS):
            priority = TicketPriority.CRITICAL
        elif any(kw in desc_lower for kw in self.PRIORITY_HIGH_KEYWORDS):
            priority = TicketPriority.HIGH
        elif any(kw in desc_lower for kw in self.PRIORITY_LOW_KEYWORDS):
            priority = TicketPriority.LOW
        else:
            priority = TicketPriority.MEDIUM

        # 3. Extract Key Entities
        entities = []
        entity_patterns = [
            r"0x[0-9a-fA-F]+",  # Hex error codes
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP addresses
            r"\b(Cisco|AnyConnect|GlobalProtect|Outlook|Teams|Docker|BitLocker|Intune|Windows \d+|macOS)\b",  # Known tech
        ]
        for pattern in entity_patterns:
            matches = re.findall(pattern, description, flags=re.IGNORECASE)
            for m in matches:
                if isinstance(m, str) and m not in entities:
                    entities.append(m)

        # 4. Immediate Actions based on Category
        action_map = {
            TicketCategory.NETWORK: [
                "Verify gateway reachability via ICMP ping",
                "Flush local DNS resolver and renew DHCP lease",
                "Check for MTU mismatch or IPv6 tunneling conflicts",
            ],
            TicketCategory.ACCOUNT: [
                "Verify user identity through HR / Manager channel",
                "Check Active Directory / Entra ID for bad password lock count",
                "Issue Temporary Access Pass (TAP) if authenticator is lost",
            ],
            TicketCategory.EMAIL: [
                "Test Outlook launch in Safe Mode (`outlook.exe /safe`)",
                "Disable cached exchange mode for large shared mailboxes",
                "Rebuild local OST cache file",
            ],
            TicketCategory.HARDWARE: [
                "Verify physical Ethernet/Power cable and link LEDs",
                "Restart Print Spooler service on print server",
                "Power cycle docking station and reset display driver (`Win+Ctrl+Shift+B`)",
            ],
            TicketCategory.SOFTWARE: [
                "Check software eligibility in Company Portal catalog",
                "Request manager approval for local admin elevation",
                "Verify system requirements and available disk space",
            ],
            TicketCategory.SECURITY: [
                "Isolate impacted endpoint from corporate LAN / Wi-Fi immediately",
                "Collect full email headers and submit to SOC sandbox",
                "Verify BitLocker recovery key via Intune identity portal",
            ],
            TicketCategory.OTHER: [
                "Contact user to collect logs and reproduction steps",
                "Assign to Tier 1 Service Desk queue",
            ],
        }

        # Team mapping
        team_map = {
            TicketCategory.NETWORK: "NetOps Infrastructure",
            TicketCategory.ACCOUNT: "Identity & Access Management (IAM)",
            TicketCategory.EMAIL: "Messaging & Collaboration",
            TicketCategory.HARDWARE: "Deskside & Hardware Support",
            TicketCategory.SOFTWARE: "Endpoint Management",
            TicketCategory.SECURITY: "Security Operations Center (SOC)",
            TicketCategory.OTHER: "Tier 1 Service Desk",
        }

        # Concise summary title
        first_line = description.strip().split("\n")[0][:80]
        summary = first_line if len(first_line) > 10 else f"{matched_category.value} Incident"

        return TriageResult(
            category=matched_category,
            priority=priority,
            summary=summary,
            confidence=0.88 if max_matches > 0 else 0.70,
            key_entities=entities[:5],
            immediate_actions=action_map.get(matched_category, ["Investigate user report"]),
            recommended_team=team_map.get(matched_category, "Tier 1 Service Desk"),
        )
