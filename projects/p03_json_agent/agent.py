import json
import logging
import re
from typing import Type, TypeVar, Tuple, List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JSONAgent")

T = TypeVar("T", bound=BaseModel)


# Sample Schemas for Demonstration
class UserProfileSchema(BaseModel):
    name: str = Field(..., description="Full user name")
    email: str = Field(..., description="Valid email address containing @")
    age: int = Field(..., ge=18, le=120, description="Age must be between 18 and 120")
    roles: List[str] = Field(..., min_length=1, description="List of user roles")
    is_active: bool = Field(True, description="Account active status")


class ProductAnalysisSchema(BaseModel):
    product_name: str = Field(..., description="Name of the evaluated product")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score between -1.0 and +1.0")
    key_features: List[str] = Field(..., min_length=2, description="At least two key product features")
    recommendation: str = Field(..., description="Buy, Pass, or Consider")


class ValidationAttemptLog(BaseModel):
    attempt: int
    raw_output: str
    is_valid: bool
    errors: List[str] = []
    correction_prompt_sent: Optional[str] = None


class ValidatedJSONAgent:
    """Agent that enforces Pydantic schemas with iterative self-correction retries."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.validation_logs: List[ValidationAttemptLog] = []

    def _extract_json_substring(self, text: str) -> str:
        """Extracts JSON block from markdown codeblocks or raw strings."""
        text = text.strip()
        # Remove ```json ... ``` wrappers if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def _mock_llm_generate(self, prompt: str, attempt: int, simulate_initial_error: bool) -> str:
        """Simulates LLM responses, optionally outputting broken JSON on first attempts to demonstrate retry repair."""
        if simulate_initial_error and attempt == 1:
            # Missing email, invalid age < 18, bad formatting
            return '```json\n{"name": "Alice Smith", "age": 15, "roles": []}\n```'
        elif simulate_initial_error and attempt == 2:
            # Correcting age but missing email
            return '{"name": "Alice Smith", "email": "invalid_email_no_at", "age": 28, "roles": ["Admin"]}'
        else:
            # Fully valid JSON matching schema
            if "UserProfileSchema" in prompt or "email" in prompt.lower():
                return json.dumps({
                    "name": "Alice Smith",
                    "email": "alice.smith@enterprise.ai",
                    "age": 29,
                    "roles": ["Admin", "Engineer"],
                    "is_active": True
                })
            else:
                return json.dumps({
                    "product_name": "Antigravity AI Workstation",
                    "sentiment_score": 0.95,
                    "key_features": ["Autonomous Task Execution", "Distributed Tracing", "Zero Latency Cache"],
                    "recommendation": "Buy"
                })

    def run_validated_generation(
        self,
        prompt: str,
        schema: Type[T],
        simulate_initial_error: bool = False
    ) -> Tuple[Optional[T], List[ValidationAttemptLog]]:
        """Executes LLM generation with schema enforcement and self-correcting retry loop."""
        self.validation_logs.clear()
        current_prompt = prompt
        schema_json_str = json.dumps(schema.model_json_schema(), indent=2)

        for attempt in range(1, self.max_retries + 1):
            # Instruct LLM to conform to schema
            full_prompt = (
                f"{current_prompt}\n\n"
                f"You MUST respond ONLY with valid JSON conforming exactly to this Pydantic schema:\n"
                f"```json\n{schema_json_str}\n```"
            )

            raw_response = self._mock_llm_generate(full_prompt, attempt, simulate_initial_error)
            extracted_json = self._extract_json_substring(raw_response)

            try:
                # 1. JSON Parse
                parsed_dict = json.loads(extracted_json)

                # 2. Pydantic Schema Validation
                validated_obj = schema.model_validate(parsed_dict)

                # Success!
                log_item = ValidationAttemptLog(
                    attempt=attempt,
                    raw_output=raw_response,
                    is_valid=True
                )
                self.validation_logs.append(log_item)
                logger.info(f"Schema validation succeeded on attempt {attempt}")
                return validated_obj, self.validation_logs

            except (json.JSONDecodeError, ValidationError) as err:
                error_details = []
                if isinstance(err, json.JSONDecodeError):
                    error_details.append(f"Invalid JSON syntax: {str(err)}")
                elif isinstance(err, ValidationError):
                    for e in err.errors():
                        loc = " -> ".join(str(x) for x in e["loc"])
                        error_details.append(f"Field '{loc}': {e['msg']}")

                logger.warning(f"Validation failed on attempt {attempt}: {error_details}")

                # Prepare targeted feedback prompt for self-correction
                feedback_prompt = (
                    f"Your previous output contained validation errors:\n"
                    + "\n".join(f"- {msg}" for msg in error_details)
                    + f"\n\nPlease fix these errors and return valid JSON conforming to the schema."
                )

                log_item = ValidationAttemptLog(
                    attempt=attempt,
                    raw_output=raw_response,
                    is_valid=False,
                    errors=error_details,
                    correction_prompt_sent=feedback_prompt
                )
                self.validation_logs.append(log_item)
                current_prompt = prompt + f"\n\n[RETRY FEEDBACK]\n{feedback_prompt}"

        return None, self.validation_logs
