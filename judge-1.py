import asyncio
import json
import yaml
from registry_decorator import register_evaluator
from .base_judge import BaseJudge

# Load prompts and few-shot examples from YAML
with open("evaluators/llm_judge/prompt.yaml") as f:
    PROMPT_CFG = yaml.safe_load(f)

SYSTEM_PROMPT = PROMPT_CFG["system_prompt"]

DIMENSIONS = list(PROMPT_CFG["dimensions"].keys())


class LLMJudgeDimensionEvaluator(BaseJudge):
    """
    Per-dimension LLM judge evaluator
    """

    def __init__(self, dimension: str, **kwargs):
        super().__init__(**kwargs)
        if dimension not in DIMENSIONS:
            raise ValueError(f"Unsupported dimension: {dimension}")
        self.dimension = dimension
        self.prompt = PROMPT_CFG["dimensions"][dimension]["prompt"]
        self.few_shot = PROMPT_CFG["dimensions"][dimension].get("few_shot_examples", [])

        # Optional runtime config for LLM API
        self.base_url = kwargs.get("base_url")
        self.api_key = kwargs.get("api_key")
        self.model_name = kwargs.get("model_name")
        self.kwargs = kwargs

    async def evaluate(self, generated: str, reference: str) -> dict:
        """
        Evaluate the generated text for this dimension.
        Returns {"score": float, "comment": str}
        """
        # Build full prompt with optional few-shot examples
        full_prompt = self.build_prompt(reference, generated)
        score, comment = await self.call_llm_with_comment(full_prompt)
        return {"score": score, "comment": comment}

    def build_prompt(self, reference: str, generated: str) -> str:
        prompt = self.prompt.replace("{reference}", reference).replace("{generated}", generated)
        if self.few_shot:
            examples_text = "\n".join(
                f"Reference: {ex['reference']}\nGenerated: {ex['generated']}\nScore: {ex['score']}\nComment: {ex['comment']}\n"
                for ex in self.few_shot
            )
            prompt = examples_text + "\n" + prompt
        return prompt

    async def call_llm_with_comment(self, prompt: str):
        """
        Placeholder for async LLM API call.
        Replace with real LLM integration.
        Returns score and comment.
        """
        await asyncio.sleep(0.1)  # simulate latency
        # Dummy deterministic score for demo
        score = round(hash(prompt) % 100 / 100, 2)
        comment = f"Simulated evaluation for {self.dimension}"
        return score, comment


# Register each dimension dynamically
for dim in DIMENSIONS:
    def factory(dimension=dim, **kwargs):
        return LLMJudgeDimensionEvaluator(dimension, **kwargs)

    register_evaluator(category="llm_judge", name=dim)(factory)
