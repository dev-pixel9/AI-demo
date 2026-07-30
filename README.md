# Enterprise GenAI Production Suite (12 Projects)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.0-e92063.svg?style=flat-square&logo=pydantic)](https://docs.pydantic.dev/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Traced-4285F4.svg?style=flat-square&logo=opentelemetry)](https://opentelemetry.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

A complete, production-grade suite of **12 Generative AI Projects** demonstrating enterprise engineering, cost optimization, schema enforcement, grounded RAG, human-in-the-loop governance, local inference, and zero-trust security guardrails.

---

## 🚀 The 12 Projects Overview

| # | Project Name | Key Capabilities & Engineering Highlights | Target Value Proposition |
| :--- | :--- | :--- | :--- |
| **P01** | **Production API Wrapper** | Token-bucket rate limiting, automatic failover routing, async webhook dispatcher | Shows you build production APIs, not just scripts |
| **P02** | **Token Cost Estimator** | Pre-generation spend forecasting, usage ledger, budget alert thresholds ($10 warning, $15 hard-stop) | Shows you understand AI economics & budget safety |
| **P03** | **Validated JSON Agent** | Pydantic v2 schema enforcement, self-correcting retry loop with error diff feedback | Shows you prevent parsing errors in production |
| **P04** | **Cited RAG Bot** | Hybrid search (BM25 + Dense Vector), Reciprocal Rank Fusion (RRF), page-specific inline citations | Shows you ground outputs and eliminate hallucinations |
| **P05** | **HITL Workflow** | Stateful research agent pausing on high-cost (>$0.20) or risky actions, append-only audit trail | Shows you orchestrate complex multi-step tasks safely |
| **P06** | **Streaming Copilot UI** | Real-time Server-Sent Events (SSE) token streaming, latency degradation tracking, optimistic UI | Shows you ship high-performance user products |
| **P07** | **Automated Eval Harness** | 50 Golden Test Cases (Extraction, RAG, Safety, Summarization), regression detector | Shows you measure quality systematically |
| **P08** | **Local Inference Server** | vLLM engine simulator, AWQ INT4 quantization, PagedAttention KV cache metrics | Shows you optimize local inference for zero API costs |
| **P09** | **Traced Pipeline** | Dockerized agent with OpenTelemetry TraceID/SpanID, Prometheus `/metrics` exporter, alerting | Shows you debug production issues in minutes |
| **P10** | **Security Guardrails** | Prompt injection/jailbreak blocker, automatic PII scrubber (SSN, Cards, Emails), policy filter | Shows you build zero-trust safe enterprise systems |
| **P11** | **Architecture Repo** | SLA latency budgets, system design diagrams (Mermaid), benchmark specs | Shows you communicate technical decisions clearly |
| **P12** | **Portfolio Site UI** | Unified glassmorphic interactive web dashboard hosting live playgrounds for all 11 projects | Shows you are ready to work immediately |

---

## ⚡ Quickstart & Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Unified Portfolio Server
```bash
python main.py
```
Or with Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Access the Interactive Dashboard
Open your browser to:
👉 **`http://localhost:8000`**

---

## 🧪 Running Automated Tests

Run the complete test suite across all 12 projects:
```bash
pytest tests/ -v
```

---

## 🐳 Docker Deployment

Build and run using Docker Compose:
```bash
docker-compose up --build
```
Prometheus telemetry metrics available at `http://localhost:8000/api/p09/metrics`.

---

## 📄 Repository Details
Saved and formatted for target repository: **`https://github.com/dev-pixel9/AI-demo`**
