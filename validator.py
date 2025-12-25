from typing import Dict, Any


class YAMLValidationError(Exception):
    """Raised when evaluation YAML is structurally invalid."""
    pass


def validate_eval_config(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Validate and normalize evaluation YAML config.

    Expected structure:

    evaluators:
      <layer_name>:
        methods:
          <method_name>: <weight | null>

    Rules:
    - 'evaluators' is mandatory
    - evaluator names are arbitrary
    - 'methods' is optional
    - if methods exist, it must be a mapping
    - missing / null weight defaults to 1.0
    - weights must be numeric and > 0
    - empty evaluators are skipped
    - at least one valid evaluator must exist
    """

    if "evaluators" not in cfg:
        raise YAMLValidationError("Missing top-level 'evaluators' key")

    evaluators = cfg["evaluators"]

    if not isinstance(evaluators, dict):
        raise YAMLValidationError("'evaluators' must be a mapping")

    validated: Dict[str, Dict[str, Dict[str, float]]] = {}

    for layer_name, layer_cfg in evaluators.items():

        # evaluator defined but empty
        if layer_cfg is None:
            print(f"[WARN] Evaluator '{layer_name}' has no config — skipping")
            continue

        if not isinstance(layer_cfg, dict):
            raise YAMLValidationError(
                f"Evaluator '{layer_name}' must be a mapping"
            )

        methods = layer_cfg.get("methods")

        # methods key missing → skip evaluator
        if methods is None:
            print(f"[WARN] Evaluator '{layer_name}' has no methods — skipping")
            continue

        if not isinstance(methods, dict):
            raise YAMLValidationError(
                f"'methods' for evaluator '{layer_name}' must be a mapping"
            )

        normalized_methods: Dict[str, float] = {}

        for method_name, weight in methods.items():

            # default weight
            if weight is None:
                weight = 1.0

            if not isinstance(weight, (int, float)):
                raise YAMLValidationError(
                    f"Weight for method '{method_name}' in evaluator "
                    f"'{layer_name}' must be numeric or null"
                )

            if weight <= 0:
                raise YAMLValidationError(
                    f"Weight for method '{method_name}' in evaluator "
                    f"'{layer_name}' must be > 0"
                )

            normalized_methods[method_name] = float(weight)

        # empty methods block → skip evaluator
        if not normalized_methods:
            print(f"[WARN] Evaluator '{layer_name}' has empty methods — skipping")
            continue

        validated[layer_name] = {"methods": normalized_methods}

    if not validated:
        raise YAMLValidationError("No valid evaluators found in config")

    return validated
