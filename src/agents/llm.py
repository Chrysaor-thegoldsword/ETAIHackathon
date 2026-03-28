from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI

    _OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

NEGATIVE_WORDS = {"no", "none", "nil", "na", "n/a", "nope", "zero"}
RISK_WORDS = {"conservative", "balanced", "aggressive"}
TAX_WORDS = {"old", "new", "unsure", "old regime", "new regime", "not sure"}


def _load_local_env() -> None:
    if os.getenv("GROQ_API_KEY"):
        return

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and not os.getenv(key):
                os.environ[key] = value
    except Exception:
        logger.exception("Failed to load .env file")


_load_local_env()


FIELD_DESCRIPTIONS = {
    "name": "User's preferred name",
    "age": "User age in years",
    "city": "Current city",
    "occupation": "Income setup such as salaried, business, freelance, or mixed",
    "monthly_income": "Average monthly income across all sources",
    "monthly_expenses": "Average monthly spending",
    "emergency_fund": "Liquid emergency savings or cash buffer",
    "current_investments": "Current investments and rough amounts",
    "liabilities": "Loans, EMIs, or credit card balances",
    "insurance_cover": "Life and health insurance cover",
    "dependents": "Number of financial dependents",
    "risk_appetite": "Conservative, balanced, or aggressive",
    "tax_regime": "Current tax regime: old, new, or unsure",
    "tax_saving_investments": "Annual tax-saving investments like EPF, PPF, ELSS, NPS",
    "short_term_goals": "Goals within 1 to 3 years",
    "long_term_goals": "Long-term goals such as retirement, education, or home purchase",
}


def llm_available() -> bool:
    return _OPENAI_AVAILABLE and bool(os.getenv("GROQ_API_KEY"))


def _client() -> OpenAI:
    if not _OPENAI_AVAILABLE:
        raise RuntimeError("openai package is not installed")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def _model() -> str:
    return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _call_chat(messages: list[dict[str, str]]) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=_model(),
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def generate_intro(profile_context: dict[str, Any], pending_field: str | None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are ET Money Mentor, a warm AI financial advisor for India. "
                "Write the opening message for the conversation. "
                "Briefly explain that you will understand the user's financial situation, answer in-scope questions, "
                "and build a score, tax view, portfolio path, and report. "
                "End by asking the next missing question naturally. Plain text only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Pending field: {pending_field}\n"
                f"Pending field meaning: {FIELD_DESCRIPTIONS.get(pending_field or '', pending_field or '')}\n"
                f"Known profile: {profile_context}"
            ),
        },
    ]
    return _call_chat(messages).strip()


def ask_next_question(field_name: str, profile_context: dict[str, Any]) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are ET Money Mentor, a warm AI financial advisor. "
                "Ask exactly one short, natural onboarding question to collect the next missing field. "
                "Return only the question text. No bullets. No markdown. Under 22 words."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Next field: {field_name}\n"
                f"Field meaning: {FIELD_DESCRIPTIONS.get(field_name, field_name)}\n"
                f"Known profile: {profile_context}"
            ),
        },
    ]
    return _call_chat(messages).strip().splitlines()[0].strip().strip('"')


def analyze_turn(
    message: str,
    pending_field: str | None,
    profile_context: dict[str, Any],
    analysis_context: dict[str, Any] | None = None,
    conversation_done: bool = False,
) -> dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are ET Money Mentor, a scope-limited AI personal finance advisor for India. "
                "Analyze one user turn. "
                "You may extract structured profile updates from the message. "
                "You may answer questions that are inside scope: personal finance planning, budgeting, investing, tax planning, insurance, goals, the app's score, report, portfolio, and how the bot works. "
                "If the question is outside scope, say so briefly and politely. "
                "Do not fabricate profile updates when the message is unclear. "
                "If the user has answered the pending field, always extract it even if the reply is short like 25, Bangalore, salaried, new, none, nil, no, or balanced. "
                "If the user message contains multiple fields, extract all of them. "
                "If the user says there are no goals or no liabilities, still extract that as a valid update. "
                "Keep acknowledgement empty unless it adds real value. "
                "Do not restate the next question in the answer because the application will handle that. "
                "Return strict JSON with keys: "
                "updates (array of objects with field and value), "
                "question_type (none|in_scope|out_of_scope), "
                "answer (string), "
                "acknowledgement (string)."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Conversation complete: {conversation_done}\n"
                f"Pending field: {pending_field}\n"
                f"Allowed fields: {FIELD_DESCRIPTIONS}\n"
                f"Current profile: {profile_context}\n"
                f"Current analysis: {analysis_context or {}}\n"
                f"User message: {message}"
            ),
        },
    ]
    result = _extract_json(_call_chat(messages))
    result.setdefault("updates", [])
    result.setdefault("question_type", "none")
    result.setdefault("answer", "")
    result.setdefault("acknowledgement", "")
    return _post_process_turn(
        result=result,
        message=message,
        pending_field=pending_field,
    )


def generate_reprompt(message: str, pending_field: str | None, profile_context: dict[str, Any]) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are ET Money Mentor, a warm AI financial advisor. "
                "The user's last message did not clearly map to the missing structured field. "
                "Respond briefly, without repeating prior confirmations, and then ask the next relevant question again. Plain text only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Last user message: {message}\n"
                f"Pending field: {pending_field}\n"
                f"Pending field meaning: {FIELD_DESCRIPTIONS.get(pending_field or '', pending_field or '')}\n"
                f"Known profile: {profile_context}"
            ),
        },
    ]
    return _call_chat(messages).strip()


def summarize_analysis(profile: dict[str, Any], analysis: dict[str, Any]) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are ET Money Mentor, an AI financial advisor. "
                "Write a concise post-analysis response in plain text. "
                "Mention the financial wellbeing score, tax recommendation, and that the user can cross-question you. "
                "Keep it under 90 words."
            ),
        },
        {
            "role": "user",
            "content": f"Profile: {profile}\nAnalysis: {analysis}",
        },
    ]
    return _call_chat(messages).strip()


def _post_process_turn(result: dict[str, Any], message: str, pending_field: str | None) -> dict[str, Any]:
    updates = result.get("updates") or []
    normalized_updates: list[dict[str, str]] = []
    seen_fields: set[str] = set()
    lowered = message.strip().lower()

    for update in updates:
        field = str(update.get("field", "") or "").strip()
        value = str(update.get("value", "") or "").strip()
        if field and value and field not in seen_fields:
            normalized_updates.append({"field": field, "value": value})
            seen_fields.add(field)

    heuristic_updates = _heuristic_updates(message, pending_field)
    for update in heuristic_updates:
        field = update["field"]
        if field not in seen_fields:
            normalized_updates.append(update)
            seen_fields.add(field)

    if (
        pending_field
        and pending_field not in seen_fields
        and lowered
        and not lowered.endswith("?")
    ):
        if pending_field in {"occupation", "tax_regime", "risk_appetite", "tax_saving_investments", "short_term_goals", "long_term_goals", "liabilities", "dependents"}:
            normalized_updates.append({"field": pending_field, "value": message})
            seen_fields.add(pending_field)

    result["updates"] = normalized_updates

    if normalized_updates and result.get("question_type") == "none":
        result["acknowledgement"] = str(result.get("acknowledgement", "") or "").strip()

    return result


def _heuristic_updates(message: str, pending_field: str | None) -> list[dict[str, str]]:
    text = message.strip()
    lowered = text.lower().strip()
    updates: list[dict[str, str]] = []

    if not text or lowered.endswith("?"):
        return updates

    income_match = re.search(
        r"(?:monthly\s+income|income)\s*(?:is|=|:)?\s*([^,;]+)",
        lowered,
    )
    expense_match = re.search(
        r"(?:monthly\s+expenses|expenses|expense)\s*(?:is|are|=|:)?\s*([^,;]+)",
        lowered,
    )
    if income_match:
        updates.append({"field": "monthly_income", "value": income_match.group(1).strip()})
    if expense_match:
        updates.append({"field": "monthly_expenses", "value": expense_match.group(1).strip()})

    if pending_field and not updates:
        if pending_field == "dependents":
            if lowered in NEGATIVE_WORDS or "no depend" in lowered:
                updates.append({"field": pending_field, "value": "0"})
            elif re.search(r"\d+", lowered):
                updates.append({"field": pending_field, "value": text})
        elif pending_field == "liabilities":
            if lowered in NEGATIVE_WORDS or "no loan" in lowered or "no debt" in lowered or "no emi" in lowered:
                updates.append({"field": pending_field, "value": "0"})
            else:
                updates.append({"field": pending_field, "value": text})
        elif pending_field in {"short_term_goals", "long_term_goals"}:
            if lowered in NEGATIVE_WORDS or "no goal" in lowered or lowered == "no change":
                updates.append({"field": pending_field, "value": "none"})
            else:
                updates.append({"field": pending_field, "value": text})
        elif pending_field == "tax_regime":
            if lowered in TAX_WORDS:
                updates.append({"field": pending_field, "value": text})
        elif pending_field == "risk_appetite":
            if lowered in RISK_WORDS:
                updates.append({"field": pending_field, "value": text})
        elif pending_field == "occupation":
            if any(word in lowered for word in {"salaried", "salary", "business", "freelance", "mixed", "self-employed", "self employed"}):
                updates.append({"field": pending_field, "value": text})
        else:
            updates.append({"field": pending_field, "value": text})

    return updates
