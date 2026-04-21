"""
LogSentinel — LLM Orchestration Service
Dispatches sanitized log data to Gemini or Groq for security analysis.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings
from app.schemas import SecurityReport

logger = logging.getLogger(__name__)
SYSTEM_PROMPT = """You are an elite, Principal Cybersecurity Analyst. Your objective is to analyze the provided web server and application logs to identify security incidents, misconfigurations, and attack vectors.

The logs have been sanitized. Personally Identifiable Information (PII) has been removed. IP addresses have been hashed (e.g., [IP_HASH: XYZ]). Some entries include [THREAT_INTEL] tags—these indicate the IP was flagged by AbuseIPDB.

Analyze the logs enclosed in the <LOGS> XML tags.

OUTPUT RESTRICTIONS:
You MUST respond ONLY with valid, minified JSON. Do not include markdown formatting like ```json. Do not include any conversational text.

Your JSON output must perfectly adhere to the following schema:
{
  "summary": "A 2-paragraph high-level markdown summary of the security posture and immediate threats.",
  "incidents": [
    {
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "attack_type": "SQLi | XSS | Path Traversal | DDoS | Bruteforce | RCE | SSRF | etc.",
      "target_endpoint": "/api/v1/users",
      "actor_hash": "[IP_HASH: XYZ]",
      "description": "Detailed explanation of the attack mechanics based on the log entry."
    }
  ],
  "waf_rule_suggestions": [
    "A list of actionable regex patterns or NGINX rules to block the identified malicious traffic."
  ]
}

If no security incidents are found, return incidents as an empty array and include a positive summary.
Do not invent or fabricate incidents. Only report what is evidenced in the logs."""


def _build_prompt(sanitized_logs: str) -> str:
    """Build the full prompt with log data embedded in XML delimiters."""
    return f"""<LOGS>
{sanitized_logs}
</LOGS>"""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def analyze(self, sanitized_logs: str) -> tuple[SecurityReport, dict]:
        """
        Send sanitized logs to the LLM for analysis.
        Returns (parsed_report, metadata).
        """
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini 2.0 Flash provider."""

    def __init__(self):
        from google import genai
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"

    def analyze(self, sanitized_logs: str) -> tuple[SecurityReport, dict]:
        start_time = time.time()

        response = self.client.models.generate_content(
            model=self.model,
            contents=_build_prompt(sanitized_logs),
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": SecurityReport,
                "temperature": 0.1,
                "max_output_tokens": 8192,
            },
        )

        elapsed = int(time.time() - start_time)

        # Parse structured response
        if response.parsed:
            report = response.parsed
        else:
            # Fallback: parse text as JSON
            report = SecurityReport.model_validate_json(response.text)

        metadata = {
            "provider": "gemini",
            "model": self.model,
            "processing_time": elapsed,
            "token_usage": {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", None),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", None),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", None),
            } if hasattr(response, "usage_metadata") and response.usage_metadata else {},
        }

        return report, metadata


class GroqProvider(LLMProvider):
    """Groq (Llama 3) provider."""

    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def analyze(self, sanitized_logs: str) -> tuple[SecurityReport, dict]:
        start_time = time.time()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_prompt(sanitized_logs)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=8192,
        )

        elapsed = int(time.time() - start_time)

        # Parse JSON response
        raw_text = response.choices[0].message.content
        report = SecurityReport.model_validate_json(raw_text)

        metadata = {
            "provider": "groq",
            "model": self.model,
            "processing_time": elapsed,
            "token_usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
                "total_tokens": response.usage.total_tokens if response.usage else None,
            },
        }

        return report, metadata


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
        return GeminiProvider()
    elif provider == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")
        return GroqProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'gemini' or 'groq'.")


def analyze_logs_with_llm(sanitized_entries: list[dict]) -> tuple[SecurityReport, dict]:
    """
    Compile sanitized entries into a prompt and send to the LLM.
    Handles retries with exponential backoff.
    """
    # Compile entries into text for the prompt
    log_lines = []
    for entry in sanitized_entries:
        raw = entry.get("_raw", "")
        threat_intel = entry.get("_threat_intel")

        line = raw
        if threat_intel:
            score = threat_intel.get("abuse_score", 0)
            if score > 0:
                line = f"{raw} [THREAT_INTEL: MALICIOUS_SCORE_{score}]"
        log_lines.append(line)

    sanitized_text = "\n".join(log_lines)
    logger.info(f"Compiled {len(log_lines)} lines for LLM analysis ({len(sanitized_text)} chars)")

    provider = get_llm_provider()
    max_retries = 3

    for attempt in range(max_retries):
        try:
            report, metadata = provider.analyze(sanitized_text)
            logger.info(
                f"LLM analysis complete via {metadata['provider']} "
                f"in {metadata['processing_time']}s "
                f"({len(report.incidents)} incidents found)"
            )
            return report, metadata

        except Exception as e:
            wait_time = 2 ** attempt
            logger.warning(
                f"LLM attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {wait_time}s..."
            )
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                logger.error(f"All LLM attempts failed: {e}")
                raise
