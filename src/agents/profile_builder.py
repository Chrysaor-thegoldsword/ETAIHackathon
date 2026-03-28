from __future__ import annotations

from typing import Any

from .financial_utils import (
    clean_text,
    parse_annual_amount,
    parse_int,
    parse_monthly_amount,
    parse_risk_appetite,
    parse_tax_regime,
)


FIELD_PARSERS = {
    "age": lambda value: parse_int(value, 0),
    "dependents": lambda value: parse_int(value, 0),
    "monthly_income": parse_monthly_amount,
    "monthly_expenses": parse_monthly_amount,
    "emergency_fund": parse_annual_amount,
    "current_investments": parse_annual_amount,
    "liabilities": parse_annual_amount,
    "insurance_cover": parse_annual_amount,
    "tax_saving_investments": parse_annual_amount,
    "tax_regime": parse_tax_regime,
    "risk_appetite": parse_risk_appetite,
}

EMPTY_GOAL_VALUES = {
    "",
    "no",
    "none",
    "nil",
    "na",
    "n/a",
    "no goals",
    "no goal",
    "no short-term goals",
    "no short term goals",
    "no long-term goals",
    "no long term goals",
    "no change",
}


class UserProfile:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {
            "uploaded_documents": [],
        }

    def set_value(self, key: str, value: Any) -> None:
        if key == "uploaded_documents":
            current = list(self.data.get("uploaded_documents", []))
            if isinstance(value, list):
                current.extend(value)
            else:
                current.append(value)
            self.data[key] = current
            return

        if key == "current_investments":
            self.data["current_investments_text"] = clean_text(value)
        if key == "liabilities":
            self.data["liabilities_text"] = clean_text(value)
        if key == "monthly_income":
            self.data["monthly_income_text"] = clean_text(value)

        if key in {"short_term_goals", "long_term_goals"}:
            cleaned_goal = clean_text(value).lower()
            self.data[key] = "" if cleaned_goal in EMPTY_GOAL_VALUES else clean_text(value)
            return

        parser = FIELD_PARSERS.get(key)
        self.data[key] = parser(value) if parser else clean_text(value)

    def update_profile(self, fields: dict[str, Any]) -> None:
        for key, value in fields.items():
            self.set_value(key, value)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.data)
