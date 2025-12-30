import yaml
import asyncio
from registry import REGISTRY
from aggregator import Aggregator
from runtime_config import load_runtime_config
import evaluators  # triggers registration


async def run_pipeline(
    generated: str,
    reference: str,
    config_path="config.yaml",
    runtime_config_path="runtime_config.yaml",
):
    # Load configs
    with open(config_path) as f:
        eval_config = yaml.safe_load(f)

    runtime_cfg = load_runtime_config(runtime_config_path)
    results = {}

    async def evaluate_method(category: str, method: str, weight: float):
        factory = REGISTRY.get(category, method)
        if not factory:
            print(f"[WARN] Evaluator not registered: {category}.{method}")
            return method, None, weight

        kwargs = runtime_cfg.get(method, {})
        evaluator = factory(**kwargs)

        score = await evaluator.evaluate(generated, reference)
        return method, score, weight

    # Evaluate all layers concurrently
    layer_tasks = []
    for category, methods in eval_config.get("evaluators", {}).items():
        if not isinstance(methods, dict):
            print(f"[WARN] methods for {category} must be a mapping")
            continue

        layer_tasks.append((category, [
            evaluate_method(category, method, weight if weight is not None else 1.0)
            for method, weight in methods.items()
        ]))

    # Run each layer concurrently
    layer_results = await asyncio.gather(*[
        asyncio.gather(*tasks, return_exceptions=True) for _, tasks in layer_tasks
    ])

    # Collect results per category
    for (category, _), task_results in zip(layer_tasks, layer_results):
        scores = {}
        weights = {}
        for method, score, weight in task_results:
            if score is None:
                continue
            scores[method] = score
            weights[method] = weight

        if scores:
            final_score = Aggregator.aggregate(scores, weights)
            results[category] = {
                "final_score": final_score,
                "evaluators": scores,
                "weights": weights,
            }

    return results


if __name__ == "__main__":
    import asyncio

    output = asyncio.run(
        run_pipeline(
            generated="This is generated text.",
            reference="This is reference text."
        )
    )
    print(output)
