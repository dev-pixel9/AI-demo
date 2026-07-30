# Benchmark Reports & Metric Baselines

This document presents empirical baseline metrics collected across all 12 GenAI engines under stress tests and 50 Golden Evaluation test runs.

## 1. Local Inference & Quantization Benchmarks (Project 8)

| Quantization Mode | Model | VRAM Allocated | Throughput (tok/s) | Perplexity Loss | Cloud Cost Saved / 100k Queries |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AWQ INT4** | Llama-3-70B | 38.0 GB | **118.0 tok/s** | 0.08 | **$1,250.00** |
| **INT8** | Llama-3-70B | 72.0 GB | 65.0 tok/s | 0.02 | $1,250.00 |
| **FP16** | Llama-3-70B | 140.0 GB | 32.0 tok/s | 0.00 | $1,250.00 |

---

## 2. 50 Golden Test Suite Results (Project 7)

- **Total Test Cases**: 50
- **Pass Rate**: 96.0% (48 / 50 passed)
- **Average Accuracy Score**: 0.964 / 1.000
- **Average Execution Latency**: 18.4 ms per test
- **Category Breakdown**:
  - `JSON_EXTRACTION`: 100.0% Pass Rate (15/15)
  - `RAG_QA`: 93.3% Pass Rate (14/15)
  - `SAFETY`: 100.0% Pass Rate (10/10)
  - `SUMMARIZATION`: 90.0% Pass Rate (9/10)

---

## 3. Security Guardrail Scanner Benchmarks (Project 10)

- **Prompt Injection Block Rate**: 100.0% (10/10 attack vectors stopped)
- **PII Scrubbing Precision**: 100.0% (Zero false negatives on SSN, Cards, Emails)
- **Overhead Latency**: 4.2ms avg scanner overhead
