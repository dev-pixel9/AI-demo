import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "OK"  # OK, ERROR
    attributes: Dict[str, Any] = {}


class AlertRule(BaseModel):
    rule_name: str
    severity: str  # CRITICAL, WARNING, INFO
    triggered: bool
    message: str
    timestamp: float = Field(default_factory=time.time)


class TracedPipelineEngine:
    """Distributed Tracing & OpenTelemetry pipeline agent with Prometheus telemetry export."""

    def __init__(self):
        self.active_spans: Dict[str, TraceSpan] = {}
        self.completed_spans: List[TraceSpan] = []
        self.request_counter = 0
        self.error_counter = 0
        self.total_cost_usd = 0.0

    def start_trace(self, span_name: str, parent_span_id: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None) -> TraceSpan:
        """Starts a distributed tracing span."""
        trace_id = f"tr-{uuid.uuid4().hex[:12]}" if not parent_span_id else self.active_spans[parent_span_id].trace_id
        span_id = f"sp-{uuid.uuid4().hex[:8]}"

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=span_name,
            start_time=time.time(),
            attributes=attributes or {}
        )
        self.active_spans[span_id] = span
        return span

    def end_trace(self, span_id: str, status: str = "OK", cost_usd: float = 0.0, extra_attrs: Optional[Dict[str, Any]] = None) -> TraceSpan:
        """Ends an active tracing span and records telemetry metrics."""
        if span_id not in self.active_spans:
            raise KeyError(f"Span {span_id} not active.")

        span = self.active_spans.pop(span_id)
        span.end_time = time.time()
        span.duration_ms = round((span.end_time - span.start_time) * 1000, 2)
        span.status = status
        
        if extra_attrs:
            span.attributes.update(extra_attrs)
            
        span.attributes["cost_usd"] = cost_usd

        self.completed_spans.append(span)
        self.request_counter += 1
        self.total_cost_usd += cost_usd

        if status != "OK":
            self.error_counter += 1

        return span

    def get_prometheus_metrics(self) -> str:
        """Generates OpenTelemetry / Prometheus format metrics exposition."""
        err_rate = (self.error_counter / self.request_counter) if self.request_counter > 0 else 0.0
        
        metrics = [
            "# HELP genai_requests_total Total GenAI API requests processed",
            "# TYPE genai_requests_total counter",
            f"genai_requests_total {self.request_counter}",
            "",
            "# HELP genai_errors_total Total request errors encountered",
            "# TYPE genai_errors_total counter",
            f"genai_errors_total {self.error_counter}",
            "",
            "# HELP genai_error_rate_ratio Error rate ratio (0.0 - 1.0)",
            "# TYPE genai_error_rate_ratio gauge",
            f"genai_error_rate_ratio {round(err_rate, 4)}",
            "",
            "# HELP genai_cumulative_cost_usd Total cumulative spend in USD",
            "# TYPE genai_cumulative_cost_usd counter",
            f"genai_cumulative_cost_usd {round(self.total_cost_usd, 6)}",
            "",
            "# HELP genai_active_spans Number of concurrently executing spans",
            "# TYPE genai_active_spans gauge",
            f"genai_active_spans {len(self.active_spans)}"
        ]
        return "\n".join(metrics)

    def evaluate_alert_rules(self) -> List[AlertRule]:
        """Evaluates production alerting thresholds."""
        alerts = []

        # Rule 1: High Error Rate (>5%)
        err_rate = (self.error_counter / self.request_counter) if self.request_counter > 0 else 0.0
        alerts.append(AlertRule(
            rule_name="HighErrorRateThreshold",
            severity="CRITICAL",
            triggered=(err_rate > 0.05),
            message=f"Current error rate is {round(err_rate * 100, 2)}% (Threshold: > 5.0%)"
        ))

        # Rule 2: High Latency (> 350ms p99)
        durations = [s.duration_ms for s in self.completed_spans if s.duration_ms]
        p99 = max(durations) if durations else 0.0
        alerts.append(AlertRule(
            rule_name="LatencySpikeAlert",
            severity="WARNING",
            triggered=(p99 > 350.0),
            message=f"P99 latency recorded at {p99}ms (Threshold: > 350.0ms)"
        ))

        # Rule 3: Spend Threshold Alert
        alerts.append(AlertRule(
            rule_name="DailyBudgetAlert",
            severity="INFO",
            triggered=(self.total_cost_usd > 5.00),
            message=f"Cumulative daily pipeline spend reached ${round(self.total_cost_usd, 4)}"
        ))

        return alerts
