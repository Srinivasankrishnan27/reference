from typing import Dict, Optional


class Aggregator:
    """
    Aggregates evaluator scores using weighted average.
    """

    @staticmethod
    def aggregate(
        scores: Dict[str, float],
        weights: Dict[str, float],
    ) -> Optional[float]:
        if not scores:
            return None

        total = 0.0
        total_weight = 0.0

        for name, score in scores.items():
            weight = weights.get(name, 1.0)
            total += score * weight
            total_weight += weight

        if total_weight == 0:
            return None

        return round(total / total_weight, 4)
