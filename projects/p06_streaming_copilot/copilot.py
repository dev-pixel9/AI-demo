import time
import asyncio
import json
from typing import AsyncGenerator, Dict, Any
from pydantic import BaseModel, Field


class StreamTokenChunk(BaseModel):
    chunk_id: int
    token: str
    is_final: bool = False
    time_to_first_token_ms: float = 0.0
    current_tokens_per_sec: float = 0.0
    degraded_mode: bool = False


class StreamingCopilotEngine:
    """Token Streaming Copilot backend engine supporting SSE and latency degradation management."""

    def __init__(self):
        self.sample_responses = [
            "Here is the optimized solution for your production pipeline:\n\n1. Use token-bucket rate limiting.\n2. Enforce Pydantic validation schemas.\n3. Monitor real-time token spend per endpoint.",
            "Analyzing system telemetry... All green! Latency p95 is 42ms, zero injection attempts detected, and KV cache hit rate is 94.2%.",
            "To deploy zero-cost local inference, configure vLLM with PagedAttention and INT4 quantization profiles."
        ]

    async def stream_tokens(self, prompt: str, simulated_latency_spike: bool = False) -> AsyncGenerator[str, None]:
        """Yields Server-Sent Events (SSE) data chunks with metrics."""
        start_time = time.time()
        ttft = 0.0

        response_text = self.sample_responses[hash(prompt) % len(self.sample_responses)]
        words = response_text.split(" ")
        
        # Determine delay per token based on latency mode
        delay_per_word = 0.12 if simulated_latency_spike else 0.03
        is_degraded = simulated_latency_spike

        for idx, word in enumerate(words):
            token = word + (" " if idx < len(words) - 1 else "")
            
            if idx == 0:
                ttft = (time.time() - start_time) * 1000

            await asyncio.sleep(delay_per_word)

            elapsed = time.time() - start_time
            tps = (idx + 1) / elapsed if elapsed > 0 else 0.0

            chunk = StreamTokenChunk(
                chunk_id=idx + 1,
                token=token,
                is_final=(idx == len(words) - 1),
                time_to_first_token_ms=round(ttft, 2),
                current_tokens_per_sec=round(tps, 1),
                degraded_mode=is_degraded
            )

            # SSE format
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"

        yield "data: [DONE]\n\n"
