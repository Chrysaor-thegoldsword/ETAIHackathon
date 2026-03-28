from __future__ import annotations

from datetime import date
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from .financial_utils import currency_or_na, format_inr


def generate_report(profile: Any, analysis: dict[str, Any]) -> dict[str, Any]:
    profile_dict = profile.to_dict() if hasattr(profile, "to_dict") else dict(profile)
    health = analysis.get("health_score", {})
    goals = analysis.get("goals", {})
    tax = analysis.get("tax", {})
    portfolio = analysis.get("portfolio", {})

    summary = (
        f"Financial wellbeing is currently {health.get('band', 'under review')} at "
        f"{health.get('total', 'NA')} out of 100. "
        f"The recommended tax regime is {str(tax.get('recommended_regime', 'unsure')).title()} "
        f"and the investable monthly surplus stands near {currency_or_na(goals.get('investable_surplus', 0))}."
    )

    return {
        "date": date.today().isoformat(),
        "summary": summary,
        "profile": profile_dict,
        "analysis": analysis,
        "sections": [
            {
                "title": "Snapshot",
                "lines": [
                    f"Monthly income: {currency_or_na(profile_dict.get('monthly_income', 0))}",
                    f"Monthly expenses: {currency_or_na(profile_dict.get('monthly_expenses', 0))}",
                    f"Emergency fund: {currency_or_na(profile_dict.get('emergency_fund', 0))}",
                    f"Current investments: {currency_or_na(profile_dict.get('current_investments', 0))}",
                    f"Outstanding liabilities: {currency_or_na(profile_dict.get('liabilities', 0))}",
                ],
            },
            {
                "title": "Health score",
                "lines": [
                    f"Overall score: {health.get('total', 'NA')} / 100",
                    f"Band: {health.get('band', 'NA')}",
                    *[f"{name}: {value}" for name, value in health.get("breakdown", {}).items()],
                ],
            },
            {
                "title": "Goal plan",
                "lines": [
                    f"Investable monthly surplus: {currency_or_na(goals.get('investable_surplus', 0))}",
                    f"Required monthly savings for stated goals: {currency_or_na(goals.get('required_monthly_for_goals', 0))}",
                    goals.get("summary", "Goal summary unavailable."),
                ],
            },
            {
                "title": "Tax plan",
                "lines": [
                    f"Recommended regime: {str(tax.get('recommended_regime', 'NA')).title()}",
                    f"Estimated old regime tax: {currency_or_na(tax.get('old_regime_tax', 0))}",
                    f"Estimated new regime tax: {currency_or_na(tax.get('new_regime_tax', 0))}",
                    f"Potential savings from switching: {currency_or_na(tax.get('tax_savings_if_switch', 0))}",
                ],
            },
            {
                "title": "Portfolio path",
                "lines": [
                    portfolio.get("strategy_note", "Portfolio note unavailable."),
                    *[
                        f"{asset}: {share}% or about {format_inr(portfolio.get('monthly_plan', {}).get(asset, 0))} per month"
                        for asset, share in portfolio.get("allocation", {}).items()
                    ],
                ],
            },
        ],
        "sources": tax.get("sources", [])
        + [
            {
                "label": choice["source_label"],
                "url": choice["source_url"],
            }
            for choice in portfolio.get("top_choices", [])
        ],
        "disclaimer": (
            "This hackathon prototype is an educational planning assistant and not a SEBI-registered investment adviser."
        ),
    }


def build_pdf_report(report: dict[str, Any], output_path: str) -> None:
    pdf = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 48
    y = height - 50

    def write_block(text: str, font: str = "Helvetica", size: int = 10, gap: int = 15) -> None:
        nonlocal y
        pdf.setFont(font, size)
        wrapped = simpleSplit(text, font, size, width - 2 * margin)
        for line in wrapped:
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont(font, size)
            pdf.drawString(margin, y, line)
            y -= gap

    pdf.setTitle("ET Money Mentor Report")
    write_block("ET Money Mentor", font="Helvetica-Bold", size=18, gap=22)
    write_block(f"Generated on {report.get('date', '')}", size=10, gap=18)
    write_block(report.get("summary", ""), size=11, gap=17)
    y -= 8

    for section in report.get("sections", []):
        write_block(section.get("title", ""), font="Helvetica-Bold", size=13, gap=18)
        for line in section.get("lines", []):
            write_block(f"- {line}")
        y -= 6

    red_flags = report.get("analysis", {}).get("health_score", {}).get("red_flags", [])
    if red_flags:
        write_block("Red flags", font="Helvetica-Bold", size=13, gap=18)
        for flag in red_flags:
            write_block(f"- {flag}")
        y -= 6

    goal_items = report.get("analysis", {}).get("goals", {}).get("all_goals", [])
    if goal_items:
        write_block("Milestones", font="Helvetica-Bold", size=13, gap=18)
        for item in goal_items:
            line = (
                f"{item.get('name')} | target {currency_or_na(item.get('target_amount', 0))} | "
                f"monthly {currency_or_na(item.get('recommended_monthly_investment', 0))}"
            )
            write_block(f"- {line}")
        y -= 6

    choices = report.get("analysis", {}).get("portfolio", {}).get("top_choices", [])
    if choices:
        write_block("Suggested instruments", font="Helvetica-Bold", size=13, gap=18)
        for choice in choices:
            line = (
                f"{choice.get('name')} | {choice.get('asset_class')} | "
                f"{choice.get('credit_quality')} | {choice.get('expected_return')}"
            )
            write_block(f"- {line}")
        y -= 6

    sources = report.get("sources", [])
    if sources:
        write_block("Reference sources", font="Helvetica-Bold", size=13, gap=18)
        for source in sources[:8]:
            write_block(f"- {source.get('label')}: {source.get('url')}", size=9, gap=14)

    y -= 8
    write_block(report.get("disclaimer", ""), font="Helvetica-Oblique", size=9, gap=14)
    pdf.save()
