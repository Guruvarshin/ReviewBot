import operator
from typing import Annotated, TypedDict

from app.models import AgentResult, PRMetadata, ReviewResult, StaticAnalysisResult


class ReviewState(TypedDict):
    pr_url: str
    started_at: float
    pr: PRMetadata
    static_analysis: StaticAnalysisResult
    agent_results: Annotated[list[AgentResult], operator.add]
    final_review: ReviewResult
