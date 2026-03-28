from __future__ import annotations

import re
from typing import Any


MONEY_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(crores?|crore|cr|lakhs?|lakh|lacs?|lac|k|thousand)?"
)
TIME_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?|mos?)")


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_text(value: Any) -> str:
    text = clean_text(value).lower()
    return (
        text.replace("rs.", "")
        .replace("rs", "")
        .replace("inr", "")
        .replace("rupees", "")
        .replace("rupee", "")
        .replace("\u20b9", "")
        .replace(",", "")
    )


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else default


def _money_multiplier(unit: str | None) -> float:
    if not unit:
        return 1.0
    normalized = unit.lower()
    if normalized in {"k", "thousand"}:
        return 1_000.0
    if normalized in {"lac", "lacs", "lakh", "lakhs"}:
        return 100_000.0
    if normalized in {"cr", "crore", "crores"}:
        return 10_000_000.0
    return 1.0


def parse_money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_text(value)
    if text in {"", "none", "nil", "na", "n/a", "no", "not sure"}:
        return 0.0

    matches = list(MONEY_PATTERN.finditer(text))
    if not matches:
        return 0.0

    total = 0.0
    for match in matches:
        total += float(match.group(1)) * _money_multiplier(match.group(2))

    return total


def parse_monthly_amount(value: Any) -> float:
    amount = parse_money(value)
    text = normalize_text(value)
    if any(token in text for token in {"annual", "annually", "year", "yearly", "annum", "p.a", "pa"}):
        return amount / 12.0
    return amount


def parse_annual_amount(value: Any) -> float:
    amount = parse_money(value)
    text = normalize_text(value)
    if any(token in text for token in {"month", "monthly", "/m"}):
        return amount * 12.0
    return amount


def parse_tax_regime(value: Any) -> str:
    text = normalize_text(value)
    if "old" in text:
        return "old"
    if "new" in text:
        return "new"
    return "unsure"


def parse_risk_appetite(value: Any) -> str:
    text = normalize_text(value)
    if any(token in text for token in {"aggressive", "high", "growth", "very high"}):
        return "aggressive"
    if any(token in text for token in {"conservative", "low", "safe", "capital protection"}):
        return "conservative"
    return "balanced"


def format_inr(amount: float) -> str:
    return f"Rs {amount:,.0f}"


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def infer_investment_categories(text: Any) -> list[str]:
    lowered = normalize_text(text)
    keyword_map = {
        "equity": {"stock", "stocks", "equity", "shares"},
        "mutual funds": {"mf", "mutual fund", "mutual funds", "sip", "elss", "index fund"},
        "debt": {"bond", "bonds", "fd", "debt", "ppf", "epf", "nps", "g-sec", "gsec"},
        "gold": {"gold", "sgb", "gold etf"},
        "real estate": {"house", "property", "real estate", "plot"},
        "cash": {"cash", "savings", "bank"},
    }
    categories: list[str] = []
    for name, keywords in keyword_map.items():
        if any(keyword in lowered for keyword in keywords):
            categories.append(name)
    return categories


def months_from_text(text: str, default_months: int) -> int:
    match = TIME_PATTERN.search(normalize_text(text))
    if not match:
        return default_months
    value = float(match.group(1))
    unit = match.group(2)
    if unit.startswith("year") or unit.startswith("yr"):
        return max(int(round(value * 12)), 1)
    return max(int(round(value)), 1)


def sip_for_future_target(target_amount: float, annual_return: float, months: int) -> float:
    if months <= 0:
        return target_amount
    monthly_rate = annual_return / 12.0
    if monthly_rate == 0:
        return target_amount / months
    factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
    return target_amount / factor if factor else target_amount / months


def infer_goal_amount(description: str, default_amount: float) -> float:
    amount = parse_money(description)
    if amount > 0:
        return amount

    text = normalize_text(description)
    heuristics = {
        "car": 1_000_000.0,
        "bike": 200_000.0,
        "vacation": 300_000.0,
        "travel": 300_000.0,
        "wedding": 2_000_000.0,
        "house": 5_000_000.0,
        "home": 5_000_000.0,
        "education": 3_000_000.0,
        "college": 3_000_000.0,
        "retirement": 40_000_000.0,
        "wealth": 10_000_000.0,
        "business": 2_500_000.0,
    }
    for keyword, inferred in heuristics.items():
        if keyword in text:
            return inferred
    return default_amount


def split_goal_statements(text: Any) -> list[str]:
    raw = clean_text(text)
    if not raw:
        return []
    parts = re.split(r"[;\n]+", raw)
    cleaned = [part.strip(" .") for part in parts if part.strip()]
    return cleaned if cleaned else [raw]


def annualized_return_for_horizon(months: int) -> float:
    if months <= 36:
        return 0.07
    if months <= 84:
        return 0.10
    return 0.11


def score_band(score: float) -> str:
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Stable"
    if score >= 40:
        return "Watchlist"
    return "At risk"


def currency_or_na(amount: float) -> str:
    return format_inr(amount) if amount else "NA"
