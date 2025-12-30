import asyncio
from abc import ABC
from evaluator_base import Evaluator

class BaseJudge(Evaluator, ABC):
    """
    Base class for LLM Judge evaluators.
    Provides shared helper methods like async API calls.
    """

    async def call_llm(self, generated: str, reference: str, prompt: str) -> float:
        """
        Placeholder for actual LLM call.
        Returns a dummy score for now.
        Replace this with your API call using self.base_url, self.api_key, etc.
        """
        await asyncio.sleep(0.1)  # simulate async network latency
        # Dummy deterministic score for demo
        return round(hash(prompt + generated + reference) % 100 / 100, 2)

    @staticmethod
    def build_prompt(dimension: str, generated: str, reference: str) -> str:
        """
        Build LLM prompt for a single dimension.
        """
        return f"Evaluate the generated text for {dimension} vs reference."
