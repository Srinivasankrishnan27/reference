from typing import Dict, Optional
from pydantic import BaseModel, Field, confloat


# ----------------------------
# Raw LLM JSON response schema
# ----------------------------

class LLMJudgeRawOutput(BaseModel):
    """
    Represents raw output from the LLM-as-judge.
    All scores are floats between 0.0 and 1.0.
    Optional comments can provide human-readable notes.
    """

    coverage: confloat(ge=0.0, le=1.0) = Field(..., description="Completeness of the generated text vs reference")
    faithfulness: confloat(ge=0.0, le=1.0) = Field(..., description="Factual accuracy and consistency")
    clarity: confloat(ge=0.0, le=1.0) = Field(..., description="Readability and wording quality")
    coherence: confloat(ge=0.0, le=1.0) = Field(..., description="Logical flow and structure")
    
    comments: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional short human-readable comment for each dimension"
    )
    confidence: confloat(ge=0.0, le=1.0) = Field(
        default=1.0,
        description="Model's self-reported confidence in the scores"
    )


# ----------------------------
# Internal Evaluator Output
# ----------------------------

class LLMJudgeEvaluatorOutput(BaseModel):
    """
    Represents the structured output returned by the LLMJudgeEvaluator.
    This is what the aggregator consumes.
    """

    scores: Dict[str, confloat(ge=0.0, le=1.0)] = Field(
        ...,
        description="Dictionary of dimension scores (coverage, faithfulness, clarity, coherence)"
    )
    details: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional human-readable comments per dimension"
    )
    confidence: confloat(ge=0.0, le=1.0) = Field(
        default=1.0,
        description="Overall confidence for this evaluation"
    )
