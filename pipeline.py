import yaml
import asyncio
from registry import REGISTRY
from aggregator import Aggregator
from runtime_config import load_runtime_config
import evaluators  # triggers registration of all evaluators


async def run_pipeline(
    generated: str,
    reference: str,
    config_path="config.yaml",
    runtime_config_path="runtime_config.yaml",
):
    """
    Run evaluation pipeline over all configured layers and methods.

    Returns:
        dict: {
            category: {
                "final_score": float,
                "evaluators": {
                    method_name: {"score": float, "comment": str}, ...
                },
                "weights": {method_name: float, ...}
            },
            ...
        }
    """
    # Load configs
    with open(config_path) as f:
        eval_config = yaml.safe_load(f)

    runtime_cfg = load_runtime_config(runtime_config_path)
    results = {}

    async def evaluate_method(category: str, method: str, weight: float):
        """
        Evaluate a single method asynchronously and return its result.
        """
        factory = REGISTRY.get(category, method)
        if not factory:
            print(f"[WARN] Evaluator not registered: {category}.{method}")
            return method, None, weight

        kwargs = runtime_cfg.get(method, {})
        evaluator = factory(**kwargs)

        result = await evaluator.evaluate(generated, reference)
        return method, result, weight

    # Prepare per-layer tasks
    layer_tasks = []
    for category, methods in eval_config.get("evaluators", {}).items():
        if not isinstance(methods, dict):
            print(f"[WARN] methods for {category} must be a mapping")
            continue

        tasks = []
        for method, weight in methods.items():
            weight = weight if weight is not None else 1.0
            tasks.append(evaluate_method(category, method, weight))

        layer_tasks.append((category, tasks))

    # Run all layers concurrently
    all_layer_results = await asyncio.gather(
        *[asyncio.gather(*tasks, return_exceptions=True) for _, tasks in layer_tasks]
    )

    # Collect results
    for (category, _), layer_result in zip(layer_tasks, all_layer_results):
        scores = {}
        weights = {}

        for method, result, weight in layer_result:
            if result is None:
                continue
            scores[method] = result  # {"score": float, "comment": str}
            weights[method] = weight

        if scores:
            final_score = Aggregator.aggregate(
                {k: v["score"] for k, v in scores.items()},
                weights
            )
            results[category] = {
                "final_score": final_score,
                "evaluators": scores,
                "weights": weights
            }

    return results


if __name__ == "__main__":
    output = asyncio.run(
        run_pipeline(
            generated="This is generated text.",
            reference="This is reference text."
        )
    )
    import json
    print(json.dumps(output, indent=4))
