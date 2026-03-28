from __future__ import annotations

from .financial_utils import clamp, format_inr


NEW_REGIME_SLABS_FY_2025_26 = [
    (400_000, 0.00),
    (800_000, 0.05),
    (1_200_000, 0.10),
    (1_600_000, 0.15),
    (2_000_000, 0.20),
    (2_400_000, 0.25),
    (float("inf"), 0.30),
]

OLD_REGIME_SLABS = [
    (250_000, 0.00),
    (500_000, 0.05),
    (1_000_000, 0.20),
    (float("inf"), 0.30),
]


def _apply_slabs(taxable_income: float, slabs: list[tuple[float, float]]) -> float:
    tax = 0.0
    previous_limit = 0.0
    remaining = taxable_income
    for upper_limit, rate in slabs:
        if remaining <= 0:
            break
        slab_width = upper_limit - previous_limit
        taxable_slice = min(remaining, slab_width)
        tax += taxable_slice * rate
        remaining -= taxable_slice
        previous_limit = upper_limit
    return tax


def _with_cess(tax: float) -> float:
    return tax * 1.04


def compare_tax_regimes(profile: dict[str, object]) -> dict[str, object]:
    annual_income = float(profile.get("monthly_income", 0) or 0) * 12.0
    tax_saving = float(profile.get("tax_saving_investments", 0) or 0)
    occupation = str(profile.get("occupation", "")).lower()
    is_salary_like = "business" not in occupation and "freelance" not in occupation and "self" not in occupation

    old_standard_deduction = 50_000.0 if is_salary_like else 0.0
    new_standard_deduction = 75_000.0 if is_salary_like else 0.0

    eligible_80c = clamp(tax_saving, 0.0, 150_000.0)
    old_taxable_income = max(annual_income - old_standard_deduction - eligible_80c, 0.0)
    new_taxable_income = max(annual_income - new_standard_deduction, 0.0)

    old_tax = _apply_slabs(old_taxable_income, OLD_REGIME_SLABS)
    if old_taxable_income <= 500_000:
        old_tax = 0.0

    new_tax = _apply_slabs(new_taxable_income, NEW_REGIME_SLABS_FY_2025_26)
    if new_taxable_income <= 1_200_000:
        new_tax = 0.0

    old_tax = round(_with_cess(old_tax), 2)
    new_tax = round(_with_cess(new_tax), 2)

    recommended = "new" if new_tax < old_tax else "old"
    savings = abs(old_tax - new_tax)
    remaining_80c_room = max(150_000.0 - eligible_80c, 0.0)

    recommendations: list[str] = []
    if recommended == "old":
        if remaining_80c_room > 0:
            recommendations.append(
                f"You still have {format_inr(remaining_80c_room)} of 80C room that can be filled with EPF, PPF, ELSS, or principal repayment."
            )
        recommendations.append("Use tax-saving products only after your emergency buffer is in place.")
    else:
        recommendations.append("The new regime already wins on tax outgo, so prioritize simplicity and low-cost investing.")
        recommendations.append("Use NPS or insurance only if they fit the financial plan, not just for deductions.")

    return {
        "assessment_basis": "FY 2025-26 / AY 2026-27 assumptions",
        "annual_income": round(annual_income, 2),
        "old_regime_tax": old_tax,
        "new_regime_tax": new_tax,
        "recommended_regime": recommended,
        "user_selected_regime": profile.get("tax_regime", "unsure"),
        "tax_savings_if_switch": round(savings, 2),
        "remaining_80c_room": round(remaining_80c_room, 2),
        "recommendations": recommendations,
        "sources": [
            {
                "label": "PIB budget summary for FY 2025-26 tax slabs",
                "url": "https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2098352",
            },
            {
                "label": "Income Tax Department help for individuals",
                "url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1",
            },
        ],
    }
