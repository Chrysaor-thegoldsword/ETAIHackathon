from __future__ import annotations

CATALOG = [
    {
        "name": "Nifty 50 index fund or ETF",
        "asset_class": "Core equity",
        "risk_profiles": {"balanced", "aggressive"},
        "credit_quality": "Market-linked",
        "expected_return": "10% to 12% long-term",
        "tax_note": "Equity taxation applies after holding-period thresholds.",
        "source_label": "ICICI Direct equity research hub",
        "source_url": "https://www.icicidirect.com/research/equity/",
        "why": "Low-cost large-cap core suitable for long horizons.",
    },
    {
        "name": "Flexi-cap mutual fund shortlist",
        "asset_class": "Diversified equity",
        "risk_profiles": {"balanced", "aggressive"},
        "credit_quality": "Market-linked",
        "expected_return": "11% to 13% long-term",
        "tax_note": "Useful for wealth creation and optional SIP scaling.",
        "source_label": "HDFC Securities mutual fund research",
        "source_url": "https://www.hdfcsec.com/research/mutualfund",
        "why": "Allows fund manager flexibility across market caps.",
    },
    {
        "name": "Bharat Bond ETF / target maturity debt fund",
        "asset_class": "Debt",
        "risk_profiles": {"conservative", "balanced"},
        "credit_quality": "AAA PSU basket",
        "expected_return": "7% to 8% indicative accrual range",
        "tax_note": "Works for known-goal timelines and debt allocation.",
        "source_label": "NSE Bharat Bond reference",
        "source_url": "https://www.nseindia.com/event-details-listing-ceremony-bharat-bond-etf",
        "why": "Useful when the goal year is known and credit quality matters.",
    },
    {
        "name": "Floating Rate Savings Bonds 2020",
        "asset_class": "Government-backed debt",
        "risk_profiles": {"conservative", "balanced"},
        "credit_quality": "Sovereign",
        "expected_return": "Coupon resets with NSC-linked spread",
        "tax_note": "Interest is taxable, so use after comparing post-tax return.",
        "source_label": "RBI floating-rate bond reset note",
        "source_url": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=57044",
        "why": "Good for capital preservation buckets and rate-reset exposure.",
    },
    {
        "name": "Gold ETF allocation sleeve",
        "asset_class": "Gold",
        "risk_profiles": {"conservative", "balanced", "aggressive"},
        "credit_quality": "Commodity-backed",
        "expected_return": "Hedge asset, not primary growth engine",
        "tax_note": "Useful as a hedge, usually capped to a small allocation.",
        "source_label": "AMFI NAV knowledge center",
        "source_url": "https://www.amfiindia.com/investor-corner/knowledge-center/net-asset-value.html",
        "why": "Adds diversification during inflation or geopolitical shocks.",
    },
    {
        "name": "Blue-chip direct equity satellite basket",
        "asset_class": "Direct equity",
        "risk_profiles": {"aggressive"},
        "credit_quality": "Market-linked",
        "expected_return": "Higher upside with higher drawdown risk",
        "tax_note": "Keep this sleeve small and research-backed.",
        "source_label": "ICICI Direct research coverage",
        "source_url": "https://www.icicidirect.com/research/equity/",
        "why": "Optional alpha sleeve for users comfortable with volatility.",
    },
]


def recommend_portfolio(
    profile: dict[str, object],
    goals: dict[str, object],
    tax: dict[str, object],
) -> dict[str, object]:
    risk = str(profile.get("risk_appetite", "balanced"))
    age = int(profile.get("age", 30) or 30)
    liabilities = float(profile.get("liabilities", 0) or 0)
    annual_income = float(profile.get("monthly_income", 0) or 0) * 12.0
    near_term_goals = len(goals.get("short_term", []))
    investable_surplus = float(goals.get("investable_surplus", 0) or 0)

    if risk == "aggressive":
        equity = 68
        debt = 17
        gold = 10
        cash = 5
    elif risk == "conservative":
        equity = 35
        debt = 45
        gold = 10
        cash = 10
    else:
        equity = 52
        debt = 28
        gold = 10
        cash = 10

    age_adjustment = max(age - 35, 0) // 10 * 4
    equity -= age_adjustment
    debt += age_adjustment

    if annual_income and liabilities / annual_income > 0.5:
        equity -= 6
        debt += 3
        cash += 3

    if near_term_goals:
        equity -= 4
        debt += 2
        cash += 2

    allocation = {
        "Equity": max(equity, 25),
        "Debt": max(debt, 20),
        "Gold": gold,
        "Cash": cash,
    }

    total = sum(allocation.values())
    normalized_allocation = {
        key: round((value / total) * 100, 1) for key, value in allocation.items()
    }

    monthly_plan = {
        key: round(investable_surplus * percentage / 100.0, 2)
        for key, percentage in normalized_allocation.items()
    }

    top_choices = [item for item in CATALOG if risk in item["risk_profiles"]][:5]
    if len(top_choices) < 5:
        seen = {item["name"] for item in top_choices}
        for item in CATALOG:
            if item["name"] not in seen:
                top_choices.append(item)
            if len(top_choices) == 5:
                break

    safe_choices = []
    for item in top_choices:
        safe_choices.append(
            {
                key: value
                for key, value in item.items()
                if key != "risk_profiles"
            }
        )

    return {
        "allocation": normalized_allocation,
        "monthly_plan": monthly_plan,
        "top_choices": safe_choices,
        "strategy_note": (
            f"The {risk} allocation keeps enough debt and cash for near-term commitments while "
            f"letting equity do the heavy lifting for long-term compounding."
        ),
        "tax_overlay": (
            "If the old regime is better, fill tax-saving buckets first; otherwise prioritize low-cost, liquid products."
            if tax.get("recommended_regime") == "old"
            else "New regime advantage suggests keeping the portfolio simple and cost-efficient."
        ),
    }
