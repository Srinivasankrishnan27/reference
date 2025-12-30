from registry_decorator import register_evaluator
from .base_judge import BaseJudge

# Define all judge dimensions
DIMENSIONS = ["coverage", "faithfulness", "clarity", "coherence"]

# Register each dimension as a separate evaluator
for dim in DIMENSIONS:
    def factory(dimension=dim, **kwargs):
        class JudgeEvaluator(BaseJudge):
            def __init__(self, **kwargs_inner):
                super().__init__(**kwargs_inner)
                self.dimension = dimension
                # optionally store LLM config
                self.base_url = kwargs_inner.get("base_url")
                self.api_key = kwargs_inner.get("api_key")
                self.model_name = kwargs_inner.get("model_name")
                self.kwargs = kwargs_inner

            async def evaluate(self, generated: str, reference: str) -> float:
                prompt = self.build_prompt(self.dimension, generated, reference)
                return await self.call_llm(generated, reference, prompt)

        return JudgeEvaluator(**kwargs)

    register_evaluator(category="llm_judge", name=dim)(factory)
