"""Unit tests for IT Domain Classification, Out-of-Scope Detection, and Intelligent Query Rewriting."""

import pytest
from src.llm.domain_classifier import (
    DomainClassifier,
    DomainClassification,
    ITDomainCategory,
    OUT_OF_SCOPE_MESSAGE,
)
from src.llm.query_rewriter import QueryRewriter
from src.agents.graph import run_support_agent


def test_out_of_scope_political_and_general_trivia():
    """Verify non-IT questions are identified as OUT_OF_SCOPE."""
    classifier = DomainClassifier()

    out_of_scope_queries = [
        "who is the cm of andhra",
        "Who is the Prime Minister?",
        "Tell me a joke.",
        "What is the best tourist place?",
        "Explain cricket rules.",
        "Write a poem.",
        "What is the capital of France?",
        "Give me a recipe for chocolate cake",
    ]

    for q in out_of_scope_queries:
        res = classifier.classify(q)
        assert res.is_it_related is False, f"Query '{q}' should not be IT related"
        assert res.category == ITDomainCategory.OUT_OF_SCOPE.value
        assert res.intent == "OUT_OF_SCOPE"


def test_in_scope_it_domain_classification():
    """Verify standard and informal IT problems are classified into correct domains."""
    classifier = DomainClassifier()

    # Hardware & power failure (including typo / informal English)
    res_hw = classifier.classify("my system was swirched of due to hard ware problem while iam doing work")
    assert res_hw.is_it_related is True
    assert res_hw.category in [ITDomainCategory.HARDWARE.value, ITDomainCategory.OPERATING_SYSTEM.value]

    # Account and Authentication
    res_auth = classifier.classify("I am not able to enter my account because of bad password lockout")
    assert res_auth.is_it_related is True
    assert res_auth.category == ITDomainCategory.ACCOUNT_AUTHENTICATION.value

    # Network and Connectivity
    res_net = classifier.classify("Cisco AnyConnect VPN connection fails at 85% TLS handshake")
    assert res_net.is_it_related is True
    assert res_net.category in [ITDomainCategory.NETWORK_CONNECTIVITY.value, ITDomainCategory.VPN.value]

    # Email and Collaboration
    res_email = classifier.classify("Mail is not going in Outlook and Outbox is frozen")
    assert res_email.is_it_related is True
    assert res_email.category == ITDomainCategory.EMAIL_COLLABORATION.value

    # Access and Permissions
    res_perm = classifier.classify("Access denied when trying to open shared folder \\filesvr01")
    assert res_perm.is_it_related is True
    assert res_perm.category == ITDomainCategory.ACCESS_PERMISSIONS.value

    # Cybersecurity
    res_sec = classifier.classify("Received a suspicious phishing email asking for corporate credentials")
    assert res_sec.is_it_related is True
    assert res_sec.category == ITDomainCategory.CYBERSECURITY.value


def test_intelligent_query_rewriting():
    """Verify informal employee phrasing is translated to rich technical diagnostic queries."""
    rewriter = QueryRewriter()
    classifier = DomainClassifier()

    # 1. Hardware unexpected shutdown
    q1 = "my system was swirched of due to hard ware problem while iam doing work"
    c1 = classifier.classify(q1)
    rw1 = rewriter.rewrite(q1, c1)
    assert any(term in rw1.lower() for term in ["hardware", "shutdown", "power"])

    # 2. Account lockout
    q2 = "I am not able to enter my account"
    c2 = classifier.classify(q2)
    rw2 = rewriter.rewrite(q2, c2)
    assert any(term in rw2.lower() for term in ["account", "authentication", "login", "lockout"])

    # 3. Email sending
    q3 = "Mail is not going"
    c3 = classifier.classify(q3)
    rw3 = rewriter.rewrite(q3, c3)
    assert any(term in rw3.lower() for term in ["outlook", "email", "exchange", "outbox"])

    # 4. Teams audio
    q4 = "Teams voice is not working"
    c4 = classifier.classify(q4)
    rw4 = rewriter.rewrite(q4, c4)
    assert any(term in rw4.lower() for term in ["teams", "audio", "microphone"])


def test_end_to_end_agent_out_of_scope_guardrail():
    """Verify the agent immediately rejects 'who is the cm of andhra' with standard message."""
    res = run_support_agent(message="who is the cm of andhra", session_id="test_oos_session")
    assert res.get("query_type") == "out_of_scope"
    assert res.get("is_out_of_scope") is True
    assert OUT_OF_SCOPE_MESSAGE in res.get("generated_answer", "")
    assert len(res.get("retrieved_documents", [])) == 0


def test_end_to_end_agent_hardware_shutdown_diagnosis():
    """Verify 'my system was swirched of due to hard ware problem' returns hardware steps, NOT Authenticator steps."""
    res = run_support_agent(
        message="my system was swirched of due to hard ware problem while iam doing work",
        session_id="test_hw_session",
    )
    answer = res.get("generated_answer", "")
    assert res.get("is_out_of_scope") is not True

    # Must contain hardware troubleshooting terms
    assert any(term in answer.lower() for term in ["power", "thermal", "hardware", "diagnostics", "battery", "drain"])

    # MUST NOT contain Microsoft Authenticator or MFA steps!
    assert "microsoft authenticator" not in answer.lower()
    assert "duo mobile" not in answer.lower()

