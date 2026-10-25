"""Runs GEval, Hallucination, and Bias metrics on each screening decision."""
import asyncio

from deepeval.metrics import BiasMetric, GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


def _run_metrics(jd_text: str, resume_text: str, reasoning: str) -> dict:
    test_case = LLMTestCase(
        input=f"Assess this resume against the job description.\n\nJD:\n{jd_text}\n\nResume:\n{resume_text}",
        actual_output=reasoning,
        context=[resume_text, jd_text],
    )
    geval = GEval(
        name="Screening Accuracy",
        criteria="The output must justify the match score using only skills and experience present in the resume and the job requirements.",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.5,
    )
    hallucination = HallucinationMetric(threshold=0.5)
    bias = BiasMetric(threshold=0.5)

    geval.measure(test_case)
    hallucination.measure(test_case)
    bias.measure(test_case)
    return {
        "geval_score": geval.score,
        "hallucination_score": hallucination.score,
        "bias_score": bias.score,
        "details": {
            "geval_reason": geval.reason,
            "hallucination_reason": hallucination.reason,
            "bias_reason": bias.reason,
        },
    }


async def run_screening_evaluation(jd_text: str, resume_text: str, reasoning: str) -> dict:
    return await asyncio.to_thread(_run_metrics, jd_text, resume_text, reasoning)
