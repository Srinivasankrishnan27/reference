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

    for category, methods in eval_config.get("evaluators", {}).items():
        if not isinstance(methods, dict):
            print(f"[WARN] methods for {category} must be a mapping")
            continue

        scores = {}
        weights = {}

        for method, weight in methods.items():
            weight = weight if weight is not None else 1.0
            factory = REGISTRY.get(category, method)

            if not factory:
                print(f"[WARN] Evaluator not registered: {category}.{method}")
                continue

            # Inject runtime config generically
            kwargs = runtime_cfg.get(method, {})
            evaluator = factory(**kwargs)

            score = await evaluator.evaluate(generated, reference)
            scores[method] = score
            weights[method] = weight

        final_score = Aggregator.aggregate(scores, weights)

        if final_score is not None:
            results[category] = {
                "final_score": final_score,
                "evaluators": scores,
                "weights": weights,
            }

    return results


if __name__ == "__main__":
    output = asyncio.run(
        run_pipeline(
            generated="This is generated text.",
            reference="This is reference text."
        )
    )
    print(output)
