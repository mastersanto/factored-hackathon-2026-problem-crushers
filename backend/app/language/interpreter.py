"""Interpreter: a customer message in any supported language -> the common, language-neutral Understanding
(English names). Constitution v1.1.0, research R1-R4.

The rules scan always runs on the original words. When a model is available it may read the message too, but
it cannot drop a safety signal the rules found, and it cannot close a possible fraud claim on its own.
"""
from __future__ import annotations

from datetime import datetime

from app.workflow.understanding import Understanding, understand as understand_rules


def interpret(text: str, *, stage: str, merchants: list[str], today: datetime, session_customer_id: str,
              llm=None) -> Understanding:
    expecting = {"choose": "choose", "confirm": "confirm", "statement": "statement"}.get(stage)
    rules_u = understand_rules(text, merchants, today, expecting, session_customer_id)
    if llm and stage not in ("statement", "contact_shared"):
        llm_u = llm.understand(text, stage, merchants, today)
        if llm_u:
            # Security flags from the deterministic scan are never dropped by the model.
            llm_u.other_customer_reference |= rules_u.other_customer_reference
            llm_u.injection_suspected |= rules_u.injection_suspected
            if stage == "confirm":
                # Closing as "it was mine" ends a possible fraud claim, so the model alone cannot do it:
                # a deterministic negation always files the claim, and closing needs both to agree.
                if rules_u.intent == "file_claim":
                    llm_u.intent = "file_claim"
                elif llm_u.intent == "confirm_mine" and rules_u.intent != "confirm_mine":
                    llm_u.intent = "reconfirm"
            return llm_u
    return rules_u
