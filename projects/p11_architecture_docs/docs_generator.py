class ArchitectureDocsGenerator:
    """Generates technical documentation, Mermaid architecture diagrams, and latency budget tables."""

    @staticmethod
    def get_system_architecture_markdown() -> str:
        return """# System Architecture & Engineering Trade-offs

## Enterprise GenAI Production Suite Architecture

```mermaid
graph TD
    User([Client Application / Browser]) --> Gateway[FastAPI API Proxy Gateway - P01]
    Gateway --> Guardrails[Security Guardrail Middleware - P10]
    Guardrails --> CostTracker[Token Cost Estimator Ledger - P02]
    CostTracker --> Tracing[OpenTelemetry Pipeline Tracer - P09]
    
    Tracing --> Router{Execution Route}
    Router -->|Structured JSON| P03[Validated JSON Agent - P03]
    Router -->|Document Q&A| P04[Cited RAG Engine - P04]
    Router -->|High-Cost Action| P05[HITL Workflow Approval Queue - P05]
    Router -->|Realtime Chat| P06[Streaming SSE Copilot - P06]
    Router -->|Evaluation Suite| P07[Automated 50-Case Eval Harness - P07]
    Router -->|Zero API Cost| P08[vLLM Local Inference Engine - P08]
```

## System SLA Latency Budget Matrix

| Pipeline Component | Target SLA (P95) | Subsystem Responsibilities | Failover Strategy |
| :--- | :--- | :--- | :--- |
| **API Wrapper Gateway (P01)** | `< 15ms` | Token-bucket rate limit, auth verification | Failover to secondary LLM region |
| **Security Guardrails (P10)** | `< 8ms` | Regex & PII redaction scanner | Block on high risk, pass sanitized text |
| **Cost Estimator (P02)** | `< 2ms` | Tokenizer count & threshold evaluation | Soft warning log on calculation error |
| **Cited RAG Engine (P04)** | `< 120ms` | BM25 + Vector Dense RRF Reranking | Fallback to BM25 keyword search |
| **Streaming Copilot (P06)** | `< 45ms (TTFT)`| Real-time token generator over SSE | Optimistic UI typing indicator |
| **vLLM Local Engine (P08)** | `< 25ms` | AWQ INT4 PagedAttention KV Cache | Dynamic batch scaling |

## Security & Governance Model

1. **Zero-Trust Input Sanitization**: All incoming prompts pass through regex heuristics and pattern matchers before hitting model execution.
2. **Deterministic PII Scrubbing**: SSN, credit cards, emails, and API keys are stripped and replaced with deterministic redaction tokens.
3. **Immutability & Audit Trail**: Every approval action in Human-in-the-Loop workflows is cryptographically timestamped and logged.
"""
