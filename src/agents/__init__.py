"""Expose agent classes and functions for the ET Money Mentor system."""

from .conversation import ConversationSession  # noqa: F401
from .doc_extraction import parse_document  # noqa: F401
from .profile_builder import UserProfile  # noqa: F401
from .health_score import compute_health_score  # noqa: F401
from .goal_planner import plan_goals  # noqa: F401
from .tax_optimizer import compare_tax_regimes  # noqa: F401
from .portfolio_recommender import recommend_portfolio  # noqa: F401
from .report_generator import generate_report  # noqa: F401

__all__ = [
    "ConversationSession",
    "parse_document",
    "UserProfile",
    "compute_health_score",
    "plan_goals",
    "compare_tax_regimes",
    "recommend_portfolio",
    "generate_report",
]