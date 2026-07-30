import time
import math
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# Pricing per 1M tokens in USD (Input / Output)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "llama-3-70b": {"input": 0.60, "output": 0.80},
}


class UsageRecord(BaseModel):
    client_id: str
    endpoint: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: float = Field(default_factory=time.time)


class BudgetStatus(BaseModel):
    client_id: str
    current_spend_usd: float
    budget_limit_usd: float
    percentage_used: float
    alert_level: str  # OK, WARNING, EXCEEDED
    can_proceed: bool


class TokenCostEstimator:
    """Pre-generation cost estimator, ledger tracker, and budget threshold engine."""

    def __init__(self, default_budget_limit: float = 10.00, warning_threshold: float = 0.80):
        self.default_budget_limit = default_budget_limit
        self.warning_threshold = warning_threshold
        self.client_budgets: Dict[str, float] = {}
        self.usage_ledger: List[UsageRecord] = []
        self.endpoint_usage: Dict[str, Dict[str, float]] = {}

    def count_tokens(self, text: str) -> int:
        """Estimate token count based on word & punctuation heuristic (approx 4 chars/token)."""
        if not text:
            return 0
        words = text.split()
        char_count = len(text)
        # Accurate average token heuristic for English and Code
        estimated_tokens = max(len(words), math.ceil(char_count / 3.8))
        return estimated_tokens

    def estimate_cost(self, prompt: str, expected_max_completion_tokens: int, model: str) -> Dict[str, Any]:
        """Calculates estimated spend BEFORE model execution."""
        pricing = MODEL_PRICING.get(model.lower(), MODEL_PRICING["gpt-4o"])
        input_tokens = self.count_tokens(prompt)
        
        est_input_cost = (input_tokens / 1_000_000) * pricing["input"]
        est_output_cost = (expected_max_completion_tokens / 1_000_000) * pricing["output"]
        total_est_cost = est_input_cost + est_output_cost

        return {
            "model": model,
            "input_tokens": input_tokens,
            "estimated_output_tokens": expected_max_completion_tokens,
            "estimated_input_cost_usd": round(est_input_cost, 6),
            "estimated_output_cost_usd": round(est_output_cost, 6),
            "total_estimated_cost_usd": round(total_est_cost, 6),
        }

    def check_budget(self, client_id: str, projected_cost_usd: float = 0.0) -> BudgetStatus:
        """Checks if client can proceed under budget threshold rules."""
        limit = self.client_budgets.get(client_id, self.default_budget_limit)
        current_spend = sum(rec.cost_usd for rec in self.usage_ledger if rec.client_id == client_id)
        projected = current_spend + projected_cost_usd
        
        pct_used = (projected / limit) if limit > 0 else 1.0

        if pct_used >= 1.0:
            alert = "EXCEEDED"
            can_proceed = False
        elif pct_used >= self.warning_threshold:
            alert = "WARNING"
            can_proceed = True
        else:
            alert = "OK"
            can_proceed = True

        return BudgetStatus(
            client_id=client_id,
            current_spend_usd=round(current_spend, 4),
            budget_limit_usd=limit,
            percentage_used=round(pct_used * 100, 2),
            alert_level=alert,
            can_proceed=can_proceed
        )

    def record_actual_usage(self, client_id: str, endpoint: str, model: str, prompt: str, completion: str) -> UsageRecord:
        """Logs actual token consumption and updates endpoint metrics."""
        pricing = MODEL_PRICING.get(model.lower(), MODEL_PRICING["gpt-4o"])
        input_tokens = self.count_tokens(prompt)
        output_tokens = self.count_tokens(completion)

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        record = UsageRecord(
            client_id=client_id,
            endpoint=endpoint,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(total_cost, 6)
        )
        self.usage_ledger.append(record)

        # Track by endpoint
        if endpoint not in self.endpoint_usage:
            self.endpoint_usage[endpoint] = {"requests": 0, "total_cost": 0.0, "total_tokens": 0}
        self.endpoint_usage[endpoint]["requests"] += 1
        self.endpoint_usage[endpoint]["total_cost"] += record.cost_usd
        self.endpoint_usage[endpoint]["total_tokens"] += (input_tokens + output_tokens)

        return record
