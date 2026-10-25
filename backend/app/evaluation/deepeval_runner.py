"""Runs GEval, Hallucination, and Bias metrics on each screening decision."""
import asyncio
import logging

from deepeval.metrics import BiasMetric, GEval, HallucinationMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from app.core.config import settings
from app.services.llm import get_llm

logger = logging.getLogger(__name__)


class VertexAIDeepEvalModel(DeepEvalBaseLLM):
    """DeepEval evaluator model wrapper for GCP Vertex AI Gemini."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.llm_model
        self.llm = get_llm(temperature=0.0)

    def load_model(self):
        return self.llm

    def generate(self, prompt: str) -> str:
        res = self.llm.invoke(prompt)
        return str(res.content)

    async def a_generate(self, prompt: str) -> str:
        res = await self.llm.ainvoke(prompt)
        return str(res.content)

    def get_model_name(self) -> str:
        return self.model_name


def _get_eval_model():
    if settings.llm_provider == "vertexai":
        return VertexAIDeepEvalModel()
    return None  # DeepEval defaults to OpenAI model if None


def _run_metrics(jd_text: str, resume_text: str, reasoning: str) -> dict:
    try:
        eval_model = _get_eval_model()
        test_case = LLMTestCase(
            input=f"Assess this resume against the job description.\n\nJD:\n{jd_text}\n\nResume:\n{resume_text}",
            actual_output=reasoning,
            context=[resume_text, jd_text],
        )
        
        geval_kwargs = {
            "name": "Screening Accuracy",
            "criteria": "The output must justify the match score using only skills and experience present in the resume and the job requirements.",
            "evaluation_params": [LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            "threshold": 0.5,
        }
        if eval_model:
            geval_kwargs["model"] = eval_model
            
        geval = GEval(**geval_kwargs)
        
        hallucination_kwargs = {"threshold": 0.5}
        bias_kwargs = {"threshold": 0.5}
        if eval_model:
            hallucination_kwargs["model"] = eval_model
            bias_kwargs["model"] = eval_model
            
        hallucination = HallucinationMetric(**hallucination_kwargs)
        bias = BiasMetric(**bias_kwargs)

        geval.measure(test_case)
        hallucination.measure(test_case)
        bias.measure(test_case)

        return {
            "geval_score": geval.score,
            "hallucination_score": hallucination.score,
            "bias_score": bias.score,
            "details": {
                "geval_reason": getattr(geval, "reason", ""),
                "hallucination_reason": getattr(hallucination, "reason", ""),
                "bias_reason": getattr(bias, "reason", ""),
            },
        }
    except Exception as exc:
        logger.error(f"DeepEval evaluation failed or skipped: {exc}", exc_info=True)
        return {
            "geval_score": None,
            "hallucination_score": None,
            "bias_score": None,
            "details": {"error": str(exc)},
        }


async def run_screening_evaluation(jd_text: str, resume_text: str, reasoning: str) -> dict:
    return await asyncio.to_thread(_run_metrics, jd_text, resume_text, reasoning)
