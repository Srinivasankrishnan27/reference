import yaml
import asyncio
from registry import REGISTRY
from aggregator import Aggregator
import evaluators  # triggers registration


async def run_pipeline(generated: str, reference: str, config_path="config.yaml"):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    results = {}

    for category, methods in config.get("evaluators", {}).items():
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

            evaluator = factory()
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
