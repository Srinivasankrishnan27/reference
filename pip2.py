import yaml
import asyncio
from registry import REGISTRY
from aggregator import Aggregator
from runtime_config import load_runtime_config

# IMPORTANT: this import triggers registration via decorators
import evaluators


async def run_pipeline(
    generated: str,
    reference: str,
    config_path: str = "config.yaml",
    runtime_config_path: str = "runtime_config.yaml",
):
    """
    Run evaluation pipeline over all configured layers and methods.

    Returns:
        dict: {
            category: {
                "final_score": float,
                "evaluators": {
                    method_name: {
                        "score": float,
                        "comment": str
                    }
                },
                "weights": {
                    method_name: float
                }
            }
        }
    """

    # -------------------------
    # Load configuration
    # -------------------------
    with open(config_path, "r") as f:
        eval_config = yaml.safe_load(f) or {}

    runtime_cfg = load_runtime_config(runtime_config_path)
    results = {}

    # -------------------------
    # Async method evaluation
    # -------------------------
    async def evaluate_method(category: str, method: str, weight: float):
        """
        Evaluate a single method asynchronously.
        Returns (method, result, weight)
        """

        kwargs = runtime_cfg.get(method, {})

        evaluator = REGISTRY.get(category, method, **kwargs)

        if evaluator is None:
            print(f"[WARN] Skipping evaluator: {category}.{method}")
            return method, None, weight

        try:
            result = await evaluator.evaluate(generated, reference)
            return method, result, weight
        except Exception as e:
            print(f"[ERROR] Evaluation failed for {category}.{method}: {e}")
            return method, None, weight

    # -------------------------
    # Prepare tasks per layer
    # -------------------------
    layer_tasks = []

    for category, cfg in eval_config.get("evaluators", {}).items():
        methods = cfg.get("methods")

        if not isinstance(methods, dict):
            print(f"[WARN] methods for {category} must be a mapping — skipping layer")
            continue

        tasks = []
        for method, weight in methods.items():
            weight = weight if weight is not None else 1.0
            tasks.append(evaluate_method(category, method, weight))

        if tasks:
            layer_tasks.append((category, tasks))

    # -------------------------
    # Run all layers concurrently
    # -------------------------
    all_results = await asyncio.gather(
        *[asyncio.gather(*tasks, return_exceptions=False) for _, tasks in layer_tasks]
    )

    # -------------------------
    # Aggregate results
    # -------------------------
    for (category, _), layer_result in zip(layer_tasks, all_results):
        scores = {}
        weights = {}

        for method, result, weight in layer_result:
            if result is None:
                continue
            scores[method] = result  # {"score": float, "comment": str}
            weights[method] = weight

        if not scores:
            print(f"[INFO] No valid results for category: {category}")
            continue

        final_score = Aggregator.aggregate(
            {k: v["score"] for k, v in scores.items()},
            weights
        )

        results[category] = {
            "final_score": final_score,
            "evaluators": scores,
            "weights": weights,
        }

    return results


# -------------------------
# CLI / Debug entrypoint
# -------------------------
if __name__ == "__main__":
    output = asyncio.run(
        run_pipeline(
            generated="This is generated text.",
            reference="This is reference text."
        )
    )

    import json
    print(json.dumps(output, indent=4))
