import time
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APIWrapper")


class RateLimiter:
    """Token Bucket Rate Limiter per client API key."""
    def __init__(self, capacity: int = 10, refill_rate_per_sec: float = 2.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}

    def is_allowed(self, client_id: str) -> tuple[bool, float]:
        now = time.time()
        if client_id not in self.tokens:
            self.tokens[client_id] = float(self.capacity)
            self.last_update[client_id] = now

        # Refill tokens based on elapsed time
        elapsed = now - self.last_update[client_id]
        self.tokens[client_id] = min(
            float(self.capacity),
            self.tokens[client_id] + elapsed * self.refill_rate
        )
        self.last_update[client_id] = now

        if self.tokens[client_id] >= 1.0:
            self.tokens[client_id] -= 1.0
            return True, self.tokens[client_id]
        else:
            return False, self.tokens[client_id]


class WebhookNotifier:
    """Dispatches webhook payloads asynchronously with retry logic."""
    def __init__(self):
        self.dispatched_webhooks: List[Dict[str, Any]] = []

    async def send_webhook(self, url: str, payload: Dict[str, Any], max_retries: int = 3) -> bool:
        logger.info(f"Dispatching Webhook to {url} with payload summary: {payload.get('status')}")
        for attempt in range(1, max_retries + 1):
            try:
                # Simulated HTTP Post dispatch
                await asyncio.sleep(0.05)
                record = {
                    "target_url": url,
                    "payload": payload,
                    "timestamp": time.time(),
                    "attempt": attempt,
                    "status": "SUCCESS"
                }
                self.dispatched_webhooks.append(record)
                return True
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt} failed: {e}")
                await asyncio.sleep(0.1 * attempt)
        return False


class APIRequestPayload(BaseModel):
    client_id: str = Field(..., description="Client API Key or Identifier")
    prompt: str = Field(..., description="LLM prompt string")
    model_preference: str = Field("gpt-4o", description="Target model family")
    webhook_url: Optional[str] = Field(None, description="Optional asynchronous completion callback URL")
    max_tokens: int = Field(500, description="Max tokens for response")


class APIResponsePayload(BaseModel):
    request_id: str
    client_id: str
    status: str
    response_text: str
    provider_used: str
    tokens_remaining: float
    latency_ms: float
    error: Optional[str] = None


class APIWrapperEngine:
    """Production Proxy Wrapper for LLM APIs with Failover & Webhooks."""
    def __init__(self):
        self.rate_limiter = RateLimiter(capacity=5, refill_rate_per_sec=2.0)
        self.webhook_notifier = WebhookNotifier()
        self.primary_provider = "OpenAI-v1"
        self.fallback_provider = "Gemini-v1.5"
        self.request_counter = 0

    async def execute_request(self, payload: APIRequestPayload) -> APIResponsePayload:
        start_time = time.time()
        self.request_counter += 1
        req_id = f"req-{self.request_counter:05d}"

        # 1. Rate Limiting Check
        allowed, remaining = self.rate_limiter.is_allowed(payload.client_id)
        if not allowed:
            return APIResponsePayload(
                request_id=req_id,
                client_id=payload.client_id,
                status="RATE_LIMITED",
                response_text="",
                provider_used="NONE",
                tokens_remaining=remaining,
                latency_ms=(time.time() - start_time) * 1000,
                error="Rate limit exceeded. Try again in a few seconds."
            )

        # 2. Execution with Fallback Logic
        provider = self.primary_provider
        output_text = ""
        error_msg = None

        try:
            # Simulate primary provider execution
            if "fail_primary" in payload.prompt.lower():
                raise RuntimeError("Primary provider down or timed out")
            
            output_text = f"[{provider} Output] Processed: '{payload.prompt[:40]}...'"
        except Exception as primary_err:
            logger.warning(f"Primary provider failed: {primary_err}. Triggering failover to {self.fallback_provider}")
            provider = self.fallback_provider
            output_text = f"[{provider} Failover Output] Processed: '{payload.prompt[:40]}...'"

        latency = (time.time() - start_time) * 1000
        res = APIResponsePayload(
            request_id=req_id,
            client_id=payload.client_id,
            status="SUCCESS",
            response_text=output_text,
            provider_used=provider,
            tokens_remaining=remaining,
            latency_ms=round(latency, 2)
        )

        # 3. Webhook Trigger if requested
        if payload.webhook_url:
            asyncio.create_task(self.webhook_notifier.send_webhook(
                url=payload.webhook_url,
                payload=res.model_dump()
            ))

        return res
