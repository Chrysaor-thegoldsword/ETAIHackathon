from __future__ import annotations

from .financial_utils import clamp, infer_investment_categories, score_band


def compute_health_score(
    profile: dict[str, object],
    goals: dict[str, object] | None = None,
    tax: dict[str, object] | None = None,
) -> dict[str, object]:
    monthly_income = float(profile.get("monthly_income", 0) or 0)
    monthly_expenses = float(profile.get("monthly_expenses", 0) or 0)
    emergency_fund = float(profile.get("emergency_fund", 0) or 0)
    investments = float(profile.get("current_investments", 0) or 0)
    liabilities = float(profile.get("liabilities", 0) or 0)
    insurance_cover = float(profile.get("insurance_cover", 0) or 0)
    dependents = int(profile.get("dependents", 0) or 0)

    annual_income = monthly_income * 12.0
    savings_rate = (monthly_income - monthly_expenses) / monthly_income if monthly_income else 0.0
    emergency_months = emergency_fund / monthly_expenses if monthly_expenses else 0.0
    debt_to_income = liabilities / annual_income if annual_income else 0.0
    protection_multiple = insurance_cover / annual_income if annual_income else 0.0
    investment_multiple = investments / annual_income if annual_income else 0.0

    goal_info = goals or {}
    investable_surplus = float(goal_info.get("investable_surplus", 0) or 0)
    required_goal_sip = float(goal_info.get("required_monthly_for_goals", 0) or 0)
    funding_ratio = investable_surplus / required_goal_sip if required_goal_sip else 1.0

    tax_info = tax or {}
    tax_selected = str(profile.get("tax_regime", "unsure"))
    tax_recommended = str(tax_info.get("recommended_regime", "unsure"))
    tax_alignment = 1.0 if tax_selected == tax_recommended else 0.55 if tax_selected != "unsure" else 0.7

    categories = infer_investment_categories(profile.get("current_investments_text", ""))
    diversification_count = len(categories)

    component_scores = {
        "Cash flow": round(clamp((savings_rate / 0.35) * 20.0, 0.0, 20.0), 1),
        "Emergency cover": round(clamp((emergency_months / 6.0) * 15.0, 0.0, 15.0), 1),
        "Debt health": round(clamp((1 - debt_to_income) * 15.0, 0.0, 15.0), 1),
        "Protection": round(clamp((protection_multiple / (10 if dependents else 6)) * 10.0, 0.0, 10.0), 1),
        "Investing discipline": round(clamp((investment_multiple / 1.5) * 15.0, 0.0, 15.0), 1),
        "Goal readiness": round(clamp(funding_ratio * 15.0, 0.0, 15.0), 1),
        "Tax efficiency": round(clamp(tax_alignment * 10.0, 0.0, 10.0), 1),
        "Diversification": round(clamp((diversification_count / 4.0) * 10.0, 0.0, 10.0), 1),
    }

    red_flags: list[str] = []
    positives: list[str] = []

    if savings_rate < 0.15:
        red_flags.append("Monthly savings rate is thin; expenses and EMIs are crowding out future goals.")
    else:
        positives.append("Savings rate is supportive of long-term compounding.")

    if emergency_months < 3:
        red_flags.append("Emergency fund is below the 3-month comfort mark.")
    else:
        positives.append("Emergency runway covers at least a few months of expenses.")

    if debt_to_income > 0.6:
        red_flags.append("Outstanding liabilities are high relative to annual income.")

    if insurance_cover == 0 and dependents > 0:
        red_flags.append("Dependents exist but no insurance cover is recorded.")
    elif protection_multiple >= 8:
        positives.append("Insurance cover is meaningful versus annual income.")

    if funding_ratio < 1:
        red_flags.append("Current investable surplus does not fully fund all stated goals yet.")
    else:
        positives.append("Goals are broadly fundable at the current surplus level.")

    if tax_selected != "unsure" and tax_selected != tax_recommended:
        red_flags.append("Current tax regime may be suboptimal for FY 2025-26 assumptions.")

    total = round(sum(component_scores.values()), 1)

    return {
        "total": total,
        "band": score_band(total),
        "breakdown": component_scores,
        "metrics": {
            "savings_rate_pct": round(savings_rate * 100, 1),
            "emergency_months": round(emergency_months, 1),
            "debt_to_income": round(debt_to_income, 2),
            "insurance_multiple": round(protection_multiple, 1),
            "goal_funding_ratio": round(funding_ratio, 2),
        },
        "red_flags": red_flags,
        "positives": positives,
    }
