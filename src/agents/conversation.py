from __future__ import annotations

import uuid
from typing import Any

from .goal_planner import plan_goals
from .health_score import compute_health_score
from .llm import (
    analyze_turn,
    ask_next_question,
    generate_intro,
    generate_reprompt,
    llm_available,
    summarize_analysis,
)
from .portfolio_recommender import recommend_portfolio
from .profile_builder import UserProfile
from .report_generator import generate_report
from .tax_optimizer import compare_tax_regimes


QUESTION_FLOW = [
    "name",
    "age",
    "city",
    "occupation",
    "monthly_income",
    "monthly_expenses",
    "emergency_fund",
    "current_investments",
    "liabilities",
    "insurance_cover",
    "dependents",
    "risk_appetite",
    "tax_regime",
    "tax_saving_investments",
    "short_term_goals",
    "long_term_goals",
]


class ConversationSession:
    def __init__(self) -> None:
        self.session_id = str(uuid.uuid4())
        self.profile = UserProfile()
        self.step = 0
        self.analysis: dict[str, Any] = {}
        self.report: dict[str, Any] = {}
        self.done = False

    def _advance_to_next_question(self) -> None:
        while self.step < len(QUESTION_FLOW):
            key = QUESTION_FLOW[self.step]
            if key in self.profile.data:
                self.step += 1
                continue
            break

    def _pending_field(self) -> str | None:
        self._advance_to_next_question()
        if self.step >= len(QUESTION_FLOW):
            return None
        return QUESTION_FLOW[self.step]

    def current_prompt(self) -> str:
        pending = self._pending_field()
        if not pending:
            return ""
        return ask_next_question(pending, self.profile.to_dict())

    def refresh_analysis(self) -> None:
        if self.done:
            self._run_analysis()

    def _reset(self) -> None:
        self.profile = UserProfile()
        self.step = 0
        self.analysis = {}
        self.report = {}
        self.done = False

    def process_message(self, message: str | None) -> tuple[str, bool, dict[str, Any] | None, dict[str, Any] | None]:
        text = (message or "").strip()

        if not llm_available():
            return (
                "LLM configuration is required for this chatbot. Please set GROQ_API_KEY and restart the app.",
                self.done,
                self.analysis if self.done else None,
                self.report if self.done else None,
            )

        if any(token in text.lower() for token in {"start over", "restart", "reset"}):
            self._reset()
            return (
                generate_intro(self.profile.to_dict(), self._pending_field()),
                False,
                None,
                None,
            )

        if self.step == 0 and text.lower() in {"", "hi", "hello", "start", "let's begin", "lets begin"}:
            return generate_intro(self.profile.to_dict(), self._pending_field()), False, None, None

        turn = analyze_turn(
            message=text,
            pending_field=self._pending_field(),
            profile_context=self.profile.to_dict(),
            analysis_context=self.analysis if self.done else None,
            conversation_done=self.done,
        )

        updates = turn.get("updates", []) or []
        for update in updates:
            field = update.get("field")
            value = update.get("value")
            if field in QUESTION_FLOW and value not in {None, ""}:
                self.profile.set_value(field, value)

        self._advance_to_next_question()

        if self.done:
            answer = str(turn.get("answer", "") or "").strip()
            return (
                answer or summarize_analysis(self.profile.to_dict(), self.analysis),
                True,
                self.analysis,
                self.report,
            )

        pending = self._pending_field()
        if not pending:
            self._run_analysis()
            self.done = True
            return self._final_message(), True, self.analysis, self.report

        parts: list[str] = []
        acknowledgement = str(turn.get("acknowledgement", "") or "").strip()
        answer = str(turn.get("answer", "") or "").strip()
        question_type = str(turn.get("question_type", "none") or "none")

        if acknowledgement:
            parts.append(acknowledgement)

        if question_type in {"in_scope", "out_of_scope"} and answer:
            if updates:
                parts.append(answer)
                parts.append(self.current_prompt())
                return "\n\n".join(part for part in parts if part), False, None, None
            parts.append(answer)
            parts.append(self.current_prompt())
            return "\n\n".join(part for part in parts if part), False, None, None

        if updates:
            return self.current_prompt(), False, None, None

        return generate_reprompt(text, pending, self.profile.to_dict()), False, None, None

    def _run_analysis(self) -> None:
        profile_dict = self.profile.to_dict()
        goals = plan_goals(profile_dict)
        tax = compare_tax_regimes(profile_dict)
        health = compute_health_score(profile_dict, goals=goals, tax=tax)
        portfolio = recommend_portfolio(profile_dict, goals=goals, tax=tax)
        self.analysis = {
            "health_score": health,
            "goals": goals,
            "tax": tax,
            "portfolio": portfolio,
        }
        self.report = generate_report(self.profile, self.analysis)

    def progress(self) -> float:
        answered = 0
        for key in QUESTION_FLOW:
            if key in self.profile.data:
                answered += 1
        return round(answered / len(QUESTION_FLOW), 2)

    def _final_message(self) -> str:
        return summarize_analysis(self.profile.to_dict(), self.analysis)
