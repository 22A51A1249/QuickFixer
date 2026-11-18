"""Comprehensive Evaluation Dataset and Verification Suite for ApexIT RAG Pipeline.

Validates:
1. Strict Out-of-Scope Detection (16 non-IT queries).
2. Domain Classification across all 13 supported IT categories (42 IT queries).
3. All 20 mandatory test cases specified in the Master Bug Fix prompt.
4. Screenshot failure regression tests (Andhra CM, Hardware shutdown).
5. Category isolation (no VPN or printer instructions in unexpected shutdown).
6. Relevance score calibration (no 35%/36% false citations).
"""

import pytest
from src.llm.domain_classifier import (
    DomainClassifier,
    DomainClassification,
    ITDomainCategory,
    OUT_OF_SCOPE_MESSAGE,
)
from src.llm.query_rewriter import QueryRewriter
from src.llm.response_validator import ResponseValidator
from src.agents.graph import run_support_agent
from src.rag.retriever import KnowledgeRetriever


# =============================================================================
# EVALUATION DATASET: 16 NON-IT UNRELATED QUERIES
# =============================================================================
UNRELATED_QUERIES = [
    "pm of india",
    "who is the president of India",
    "tell me a joke",
    "who is the cm of andhra",
    "What is the best tourist place?",
    "Explain cricket rules.",
    "Write a poem.",
    "What is the capital of France?",
    "Give me a recipe for chocolate cake",
    "Who won the FIFA World Cup 2022?",
    "What is the weather in New York?",
    "Who is the chief minister of Tamil Nadu?",
    "Tell me a bedtime story about dragons",
    "What is the population of Tokyo?",
    "Suggest some good Hollywood movies",
    "How to bake sourdough bread at home",
]


# =============================================================================
# EVALUATION DATASET: 42 DIVERSE ENTERPRISE IT SUPPORT QUERIES
# =============================================================================
IT_SUPPORT_QUERIES = [
    # Operating System & Unexpected Shutdown (Mandatory Cases 4, 5, 6 & Screenshot 2)
    ("my laptop suddenly switched off", ITDomainCategory.OPERATING_SYSTEM.value),
    ("my laptop freezes frequently", ITDomainCategory.OPERATING_SYSTEM.value),
    ("my laptop shows a blue screen", ITDomainCategory.OPERATING_SYSTEM.value),
    ("while iam working the system was stuck suddenly and switched off", ITDomainCategory.OPERATING_SYSTEM.value),
    ("my system was swirched of due to hard ware problem while iam doing work", ITDomainCategory.OPERATING_SYSTEM.value),
    ("Windows 11 Kernel-Power event 41 critical crash", ITDomainCategory.OPERATING_SYSTEM.value),
    ("BSOD stop code IRQL_NOT_LESS_OR_EQUAL on boot", ITDomainCategory.OPERATING_SYSTEM.value),

    # Account and Authentication (Mandatory Cases 7, 8, 9, 10)
    ("I cannot log in to Windows", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),
    ("my company account is locked", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),
    ("my password is not working", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),
    ("I am not receiving an OTP", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),
    ("Need temporary access pass for Microsoft Authenticator", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),
    ("Self-service password reset SSPR portal error", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),
    ("Okta SSO single sign on login failed", ITDomainCategory.ACCOUNT_AUTHENTICATION.value),

    # Email and Collaboration (Mandatory Cases 11, 16)
    ("Outlook is not sending emails", ITDomainCategory.EMAIL_COLLABORATION.value),
    ("my Teams microphone is not working", ITDomainCategory.EMAIL_COLLABORATION.value),
    ("Outlook crashing when opening shared mailbox", ITDomainCategory.EMAIL_COLLABORATION.value),
    ("Microsoft Teams audio device not detected", ITDomainCategory.EMAIL_COLLABORATION.value),
    ("Cannot sync Exchange calendar on Outlook", ITDomainCategory.EMAIL_COLLABORATION.value),
    ("Outbox is stuck and outgoing mail is not going", ITDomainCategory.EMAIL_COLLABORATION.value),

    # Hardware & Peripherals (Mandatory Cases 12, 15)
    ("my printer is offline", ITDomainCategory.HARDWARE.value),
    ("my laptop is overheating", ITDomainCategory.HARDWARE.value),
    ("Print jobs stuck in print spooler queue on printsvr01", ITDomainCategory.HARDWARE.value),
    ("External monitor not detected through USB-C dock", ITDomainCategory.HARDWARE.value),
    ("Paper jam in network printer tray 2", ITDomainCategory.HARDWARE.value),
    ("DisplayLink docking station not displaying video", ITDomainCategory.HARDWARE.value),

    # VPN (Mandatory Case 13)
    ("VPN is not connecting", ITDomainCategory.VPN.value),
    ("Cisco AnyConnect secure gateway connection timed out at 85%", ITDomainCategory.VPN.value),
    ("GlobalProtect VPN TLS handshake error", ITDomainCategory.VPN.value),
    ("VPN drops every 10 minutes when working from home", ITDomainCategory.VPN.value),

    # Network Connectivity (Mandatory Cases 14, 19)
    ("my Wi-Fi keeps disconnecting", ITDomainCategory.NETWORK_CONNECTIVITY.value),
    ("DNS server is not responding", ITDomainCategory.NETWORK_CONNECTIVITY.value),
    ("Ethernet cable connected but no internet access", ITDomainCategory.NETWORK_CONNECTIVITY.value),
    ("Cannot renew DHCP IP address lease on corporate network", ITDomainCategory.NETWORK_CONNECTIVITY.value),

    # Software and Application (Mandatory Case 17)
    ("my application crashes", ITDomainCategory.SOFTWARE_APPLICATION.value),
    ("Docker desktop installation fails with privilege error", ITDomainCategory.SOFTWARE_APPLICATION.value),
    ("Company portal software install error 0x80070005", ITDomainCategory.SOFTWARE_APPLICATION.value),
    ("Request temporary administrator rights via EPM", ITDomainCategory.SOFTWARE_APPLICATION.value),

    # Cybersecurity (Mandatory Case 18)
    ("I received a suspicious login alert", ITDomainCategory.CYBERSECURITY.value),
    ("Phishing email received asking to verify credentials", ITDomainCategory.CYBERSECURITY.value),
    ("BitLocker recovery key required on Windows startup", ITDomainCategory.CYBERSECURITY.value),

    # Access and Permissions (Mandatory Case 20)
    ("my shared folder says access denied", ITDomainCategory.ACCESS_PERMISSIONS.value),
    (r"Cannot access network file share \\filesvr01\shared", ITDomainCategory.ACCESS_PERMISSIONS.value),
    ("Permission denied when opening department SharePoint folder", ITDomainCategory.ACCESS_PERMISSIONS.value),
]


# =============================================================================
# TEST SUITE: 1. STRICT OUT-OF-SCOPE DETECTION (16 QUERIES)
# =============================================================================
@pytest.mark.parametrize("query", UNRELATED_QUERIES)
def test_out_of_scope_rejection(query):
    """Verify that every non-IT query is strictly rejected as OUT_OF_SCOPE."""
    classifier = DomainClassifier()
    classification = classifier.classify(query)

    assert classification.is_it_related is False, f"'{query}' should not be IT related"
    assert classification.category == ITDomainCategory.OUT_OF_SCOPE.value
    assert classification.intent == "OUT_OF_SCOPE"


# =============================================================================
# TEST SUITE: 2. DOMAIN CLASSIFICATION ACCURACY (42 IT QUERIES)
# =============================================================================
@pytest.mark.parametrize("query,expected_category", IT_SUPPORT_QUERIES)
def test_it_domain_classification(query, expected_category):
    """Verify that every IT support query maps accurately to its domain category."""
    classifier = DomainClassifier()
    classification = classifier.classify(query)

    assert classification.is_it_related is True, f"'{query}' must be identified as IT related"
    assert classification.category == expected_category, (
        f"Query: '{query}'. Expected category '{expected_category}', got '{classification.category}'"
    )


# =============================================================================
# TEST SUITE: 3. MANDATORY BUG FIX 1: 'pm of india' REJECTION
# =============================================================================
def test_bug_1_pm_of_india_rejection():
    """Verify Bug 1: 'pm of india' is strictly rejected with the exact prompt message."""
    res = run_support_agent(message="pm of india", session_id="test_pm_session")

    assert res.get("query_type") == "out_of_scope"
    assert res.get("is_out_of_scope") is True
    assert OUT_OF_SCOPE_MESSAGE in res.get("generated_answer", "")

    # Must NOT contain VPN or troubleshooting instructions
    answer_lower = res.get("generated_answer", "").lower()
    assert "vpn" not in answer_lower
    assert "cisco" not in answer_lower
    assert "gateway" not in answer_lower
    assert len(res.get("retrieved_documents", [])) == 0


# =============================================================================
# TEST SUITE: 4. MANDATORY BUG FIX 2: UNEXPECTED SHUTDOWN & CLARIFICATION
# =============================================================================
def test_bug_2_unexpected_shutdown_and_clarification():
    """Verify Bug 2: 'while iam working the system was stuck suddenly and switched off'
    is classified as OPERATING_SYSTEM / UNEXPECTED_SHUTDOWN and asks relevant questions.
    """
    query = "while iam working the system was stuck suddenly and switched off"
    res = run_support_agent(message=query, session_id="test_shutdown_session")

    answer = res.get("generated_answer", "")
    assert res.get("is_out_of_scope") is not True

    # Must contain unexpected shutdown diagnosis
    assert "Unexpected Computer Shutdown" in answer or "Operating System" in answer or "shutdown" in answer.lower()

    # Must contain relevant clarification questions
    assert any(term in answer.lower() for term in ["freeze", "stuck"])
    assert any(term in answer.lower() for term in ["restart", "power"])
    assert any(term in answer.lower() for term in ["blue screen", "bsod"])
    assert any(term in answer.lower() for term in ["overheating", "hot", "thermal"])
    assert any(term in answer.lower() for term in ["charger", "power"])

    # MUST NOT retrieve printer or VPN troubleshooting documents!
    for doc in res.get("retrieved_documents", []):
        assert "printer" not in doc.get("source", "").lower()
        assert "vpn" not in doc.get("source", "").lower()

    # Response must NOT contain printer commands or VPN error messages!
    answer_lower = answer.lower()
    assert "print spooler" not in answer_lower
    assert "del /q /f /s" not in answer_lower
    assert "cisco anyconnect" not in answer_lower


# =============================================================================
# TEST SUITE: 5. MANDATORY BUG FIX 3: NO 35%/36% LOW-CONFIDENCE FALSE CITATIONS
# =============================================================================
def test_bug_3_no_low_confidence_citations_displayed():
    """Verify Bug 3: Relevance values such as 35% or 36% are never displayed as confirmed runbooks."""
    retriever = KnowledgeRetriever()

    # Query with no direct match in internal runbooks
    unmatched_query = "How to install custom Ruby on Rails gem on Alpine Linux"
    chunks = retriever.retrieve(unmatched_query, top_k=3)

    # Any returned chunks must meet calibrated threshold (>= 0.45)
    for chunk, score in chunks:
        assert score >= 0.45, f"Chunk {chunk.title} returned with uncalibrated low score {score}"

    res = run_support_agent(message=unmatched_query, session_id="test_unmatched_session")
    answer = res.get("generated_answer", "")

    # Must not display uncalibrated low-confidence headers
    assert "Relevance: 3" not in answer
    assert "Relevance: 2" not in answer
    assert "Relevance: 1" not in answer
    assert "Relevance: 0" not in answer


# =============================================================================
# TEST SUITE: 6. MANDATORY BUG FIX 4: NO CROSS-DOMAIN CONTAMINATION
# =============================================================================
def test_bug_4_no_cross_domain_step_mixing():
    """Verify Bug 4: Steps from unrelated runbooks (printer, VPN, MFA) are never mixed into OS responses."""
    res = run_support_agent(
        message="my laptop suddenly switched off",
        session_id="test_no_mixing_session",
    )
    answer_lower = res.get("generated_answer", "").lower()

    # Strictly no printer spooler commands or VPN gateway instructions
    assert "print spooler" not in answer_lower
    assert "spool\\printers" not in answer_lower
    assert "cisco anyconnect" not in answer_lower
    assert "tls handshake" not in answer_lower
    assert "authenticator app" not in answer_lower


# =============================================================================
# TEST SUITE: 7. SCREENSHOT REGRESSION TESTS
# =============================================================================
def test_screenshot_1_regression_andhra_cm():
    """Regression test for Screenshot 1: 'who is the cm of andhra' must be rejected."""
    res = run_support_agent(message="who is the cm of andhra", session_id="test_andhra_cm")
    assert res.get("is_out_of_scope") is True
    assert OUT_OF_SCOPE_MESSAGE in res.get("generated_answer", "")
    assert len(res.get("retrieved_documents", [])) == 0


def test_screenshot_2_regression_hardware_shutdown():
    """Regression test for Screenshot 2: 'my system was swirched of due to hard ware problem'
    must NOT return Authenticator app or MFA push steps!
    """
    res = run_support_agent(
        message="my system was swirched of due to hard ware problem while iam doing work",
        session_id="test_hw_shutdown",
    )
    answer_lower = res.get("generated_answer", "").lower()
    assert "authenticator app" not in answer_lower
    assert "duo mobile" not in answer_lower
    assert "relevance: 36%" not in answer_lower
    assert any(term in answer_lower for term in ["power", "thermal", "hardware", "diagnostics", "battery", "drain"])
