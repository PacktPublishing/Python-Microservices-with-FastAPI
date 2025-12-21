"""Evaluation tests for the support agent."""
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, Evaluator, EvaluatorContext, IsInstance

from domain.support.schemas import SupportQuery, SupportResponse
from domain.support.services import SupportService


@dataclass
class HasSources(Evaluator[SupportQuery, SupportResponse]):
    """Check that the response includes source documents."""

    min_sources: int = 1

    def evaluate(
        self, ctx: EvaluatorContext[SupportQuery, SupportResponse]
    ) -> bool:
        return len(ctx.output.sources) >= self.min_sources


@dataclass
class MinConfidenceCheck(Evaluator[SupportQuery, SupportResponse]):
    """Check that confidence meets minimum threshold."""

    min_level: str = "medium"

    def evaluate(
        self, ctx: EvaluatorContext[SupportQuery, SupportResponse]
    ) -> bool:
        levels = ["low", "medium", "high"]
        min_index = levels.index(self.min_level)
        actual_index = levels.index(ctx.output.confidence.value)
        return actual_index >= min_index


@dataclass
class NoUncertainLanguage(Evaluator[SupportQuery, SupportResponse]):
    """Check that response doesn't hedge with uncertain language."""

    forbidden_terms: tuple = ("maybe", "not sure", "I think", "possibly")

    def evaluate(
        self, ctx: EvaluatorContext[SupportQuery, SupportResponse]
    ) -> bool:
        answer_lower = ctx.output.answer.lower()
        return not any(term in answer_lower for term in self.forbidden_terms)


refund_cases = Dataset(
    cases=[
        Case(
            name="refund_sitter_cancels",
            inputs=SupportQuery(
                question="Can I get a refund if the sitter cancels?"
            ),
            expected_output=None,
            metadata={"category": "refunds"},
        ),
        Case(
            name="refund_timing",
            inputs=SupportQuery(
                question="How long does a refund take to process?"
            ),
            expected_output=None,
            metadata={"category": "refunds"},
        ),
    ],
    evaluators=[
        IsInstance(type_name="SupportResponse"),
        Contains(value="refund", case_sensitive=False),
    ],
)

refund_cases.add_evaluator(HasSources(min_sources=1))
refund_cases.add_evaluator(MinConfidenceCheck(min_level="medium"))
refund_cases.add_evaluator(NoUncertainLanguage())


async def run_support_agent(query: SupportQuery) -> SupportResponse:
    """Run the support agent for evaluation."""
    service = SupportService()
    return await service.answer_question(query)


if __name__ == "__main__":
    report = refund_cases.evaluate_sync(run_support_agent)
    report.print(include_input=True, include_output=True)
