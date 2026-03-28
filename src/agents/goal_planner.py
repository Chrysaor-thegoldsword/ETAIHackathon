from __future__ import annotations

from typing import Any

from .financial_utils import (
    clamp,
    format_inr,
    infer_goal_amount,
    months_from_text,
    sip_for_future_target,
    split_goal_statements,
    annualized_return_for_horizon,
)


def _build_goal_items(raw_text: str, default_months: int, default_amount: float, bucket: str) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    for statement in split_goal_statements(raw_text):
        target_amount = infer_goal_amount(statement, default_amount)
        horizon_months = months_from_text(statement, default_months)
        assumed_return = annualized_return_for_horizon(horizon_months)
        required_monthly = sip_for_future_target(target_amount, assumed_return, horizon_months)
        goals.append(
            {
                "bucket": bucket,
                "name": statement,
                "target_amount": round(target_amount, 2),
                "horizon_months": horizon_months,
                "expected_return_assumption": round(assumed_return * 100, 1),
                "required_monthly_investment": round(required_monthly, 2),
                "milestone": (
                    f"Build towards {format_inr(target_amount)} over {horizon_months} months "
                    f"with a disciplined monthly SIP."
                ),
            }
        )
    return goals


def plan_goals(profile: dict[str, Any]) -> dict[str, Any]:
    monthly_income = float(profile.get("monthly_income", 0) or 0)
    monthly_expenses = float(profile.get("monthly_expenses", 0) or 0)
    contingency_buffer = max(monthly_expenses * 0.1, 5_000.0 if monthly_expenses else 0.0)
    monthly_surplus = max(monthly_income - monthly_expenses, 0.0)
    investable_surplus = max(monthly_income - monthly_expenses - contingency_buffer, 0.0)

    short_goals = _build_goal_items(
        str(profile.get("short_term_goals", "")),
        default_months=24,
        default_amount=500_000.0,
        bucket="Short term",
    )
    long_goals = _build_goal_items(
        str(profile.get("long_term_goals", "")),
        default_months=120,
        default_amount=5_000_000.0,
        bucket="Long term",
    )
    all_goals = short_goals + long_goals

    required_monthly = sum(goal["required_monthly_investment"] for goal in all_goals)
    funding_ratio = clamp(investable_surplus / required_monthly if required_monthly else 1.0, 0.0, 2.0)

    for goal in all_goals:
        recommended = goal["required_monthly_investment"] * min(funding_ratio, 1.0)
        goal["recommended_monthly_investment"] = round(recommended, 2)
        goal["status"] = (
            "On track" if investable_surplus >= required_monthly
            else "Partially funded" if recommended > 0
            else "Needs reprioritization"
        )

    return {
        "monthly_surplus": round(monthly_surplus, 2),
        "contingency_buffer": round(contingency_buffer, 2),
        "investable_surplus": round(investable_surplus, 2),
        "required_monthly_for_goals": round(required_monthly, 2),
        "funding_ratio": round(funding_ratio, 2),
        "short_term": short_goals,
        "long_term": long_goals,
        "all_goals": all_goals,
        "summary": (
            "Current surplus can comfortably fund the stated goals."
            if investable_surplus >= required_monthly
            else "Current surplus is below the full requirement, so the plan phases goals and tax moves."
        ),
    }
