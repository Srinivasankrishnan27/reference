import json
from typing import Dict, Any

from evaluators.base import BaseEvaluator
from evaluators.llm_judge.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from evaluators.llm_judge.data_model import (
    LLMJudgeRawOutput,
    LLMJudgeEvaluatorOutput
)


class LLMJudgeEvaluator(BaseEvaluator):
    """
    LLM-as-a-Judge evaluator producing method-level scores,
    optional comments, and confidence.
    """

    name = "llm_judge"

    def __init__(self, llm_client):
        """
        llm_client must expose:
            async chat(system: str, user: str) -> str
        """
        self.llm = llm_client

    async def evaluate(self, generated: str, reference: str) -> Dict[str, Any]:
        """
        Executes a single LLM call and returns structured evaluation output.

        Returns:
        {
            "scores": { coverage, faithfulness, clarity, coherence },
            "details": optional comments per dimension,
            "confidence": overall confidence
        }
        """

        # ----------------------------
        # Build prompt
        # ----------------------------
        prompt = USER_PROMPT_TEMPLATE.format(
            generated=generated,
            reference=reference
        )

        # ----------------------------
        # Call LLM
        # ----------------------------
        response = await self.llm.chat(
            system=SYSTEM_PROMPT,
            user=prompt
        )

        # ----------------------------
        # Parse & validate raw LLM JSON
        # ----------------------------
        try:
            raw_dict = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM Judge returned invalid JSON: {response}") from e

        try:
            raw = LLMJudgeRawOutput(**raw_dict)
        except Exception as e:
            # Include descriptive field info from Pydantic
            raise ValueError(
                f"LLM Judge output failed schema validation: {e}\n"
                f"Raw output: {raw_dict}"
            ) from e

        # ----------------------------
        # Build evaluator output
        # ----------------------------
        evaluator_output = LLMJudgeEvaluatorOutput(
            scores={
                "coverage": raw.coverage,
                "faithfulness": raw.faithfulness,
                "clarity": raw.clarity,
                "coherence": raw.coherence,
            },
            details=raw.comments,
            confidence=raw.confidence
        )

        return evaluator_output.model_dump()
