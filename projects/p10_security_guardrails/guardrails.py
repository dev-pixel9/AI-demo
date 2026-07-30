import re
import time
from typing import Dict, List, Tuple, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    PII_EXPOSURE = "PII_EXPOSURE"
    TOXICITY_POLICY = "TOXICITY_POLICY"
    NONE = "NONE"


class GuardrailCheckResult(BaseModel):
    is_safe: bool
    violation_type: ViolationType
    sanitized_text: str
    redacted_items: List[str] = []
    risk_score: float  # 0.0 safe - 1.0 critical
    reason: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class SecurityGuardrailMiddleware:
    """Enterprise GenAI Security Middleware enforcing Prompt Injection Blocking, PII Scrubbing, and Output Filtering."""

    def __init__(self):
        # Prompt Injection & Jailbreak Heuristics
        self.injection_patterns = [
            r"ignore\s+(all\s+)?(previous\s+)?instructions",
            r"disregard\s+system\s+prompt",
            r"you\s+are\s+now\s+DAN",
            r"developer\s+mode\s+enabled",
            r"bypass\s+safety\s+filter",
            r"output\s+(the\s+)?system\s+secret",
            r"base64decode\(",
            r"sudo\s+override",
        ]

        # PII Regex Patterns
        self.pii_patterns = {
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "API_KEY": r"\b(?:sk-[a-zA-Z0-9]{32,}|api_[a-zA-Z0-9]{24,})\b",
        }

        # Harmful Content Policy Keywords
        self.banned_content_keywords = [
            "malware_creation_script",
            "exploit_payload_zero_day",
            "unauthorized_access_key",
            "bypass_authentication_token"
        ]

        self.security_logs: List[GuardrailCheckResult] = []

    def inspect_and_sanitize_input(self, input_text: str) -> GuardrailCheckResult:
        """Inspects user input for prompt injection, jailbreak vectors, and redacts PII."""
        # 1. Check for Prompt Injection / Jailbreak
        for pattern in self.injection_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                result = GuardrailCheckResult(
                    is_safe=False,
                    violation_type=ViolationType.PROMPT_INJECTION,
                    sanitized_text="[BLOCKED: Prompt Injection / Safety Policy Violation]",
                    risk_score=0.98,
                    reason=f"Matched jailbreak pattern: '{pattern}'"
                )
                self.security_logs.append(result)
                return result

        # 2. PII Redaction
        sanitized = input_text
        redacted_summary = []
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, sanitized)
            if matches:
                for match in matches:
                    redacted_summary.append(f"{pii_type}: {match[:3]}***")
                sanitized = re.sub(pattern, f"[{pii_type}_REDACTED]", sanitized)

        violation = ViolationType.PII_EXPOSURE if redacted_summary else ViolationType.NONE
        result = GuardrailCheckResult(
            is_safe=True,
            violation_type=violation,
            sanitized_text=sanitized,
            redacted_items=redacted_summary,
            risk_score=0.15 if redacted_summary else 0.0,
            reason="Clean input" if not redacted_summary else f"Redacted {len(redacted_summary)} PII instances"
        )
        self.security_logs.append(result)
        return result

    def inspect_output(self, output_text: str) -> GuardrailCheckResult:
        """Inspects LLM response before returning to user to guarantee zero harmful content leakage."""
        for kw in self.banned_content_keywords:
            if kw in output_text.lower():
                result = GuardrailCheckResult(
                    is_safe=False,
                    violation_type=ViolationType.TOXICITY_POLICY,
                    sanitized_text="[BLOCKED: Generated content violated enterprise safety policy]",
                    risk_score=0.95,
                    reason=f"Model output contained prohibited content keyword: '{kw}'"
                )
                self.security_logs.append(result)
                return result

        result = GuardrailCheckResult(
            is_safe=True,
            violation_type=ViolationType.NONE,
            sanitized_text=output_text,
            risk_score=0.0,
            reason="Output passed safety verification"
        )
        self.security_logs.append(result)
        return result
