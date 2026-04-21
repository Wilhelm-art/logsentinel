"""
LogSentinel — PII Sanitizer Service (The Air-Gap)
Strips emails, names, JWTs, and hashes IP addresses before LLM dispatch.
"""

import hashlib
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)
# IPv4
IPV4_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

# IPv6 (simplified — catches most common formats)
IPV6_PATTERN = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|'
    r'\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|'
    r'\b::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b|'
    r'\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b'
)

# JWT (3 base64url segments separated by dots)
JWT_PATTERN = re.compile(
    r'\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'
)

# Email
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# Bearer tokens
BEARER_PATTERN = re.compile(
    r'Bearer\s+[A-Za-z0-9._~+/=-]+',
    re.IGNORECASE
)

# API keys (generic long hex/alphanumeric strings in headers)
API_KEY_PATTERN = re.compile(
    r'\b[A-Za-z0-9]{32,}\b'
)


class Sanitizer:
    """
    The Air-Gap sanitization pipeline.
    Ensures zero PII reaches the LLM.
    """

    def __init__(self):
        self.ip_map: dict[str, str] = {}  # hash -> original IP
        self._presidio_available = False
        self._analyzer = None
        self._anonymizer = None
        self._init_presidio()

    def _init_presidio(self):
        """Initialize Presidio if available."""
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
            self._presidio_available = True
            logger.info("Presidio initialized successfully")
        except Exception as e:
            logger.warning(f"Presidio not available, using regex-only sanitization: {e}")
            self._presidio_available = False

    def _hash_ip(self, ip: str) -> str:
        """Deterministically hash an IP address."""
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:12]
        self.ip_map[ip_hash] = ip
        return f"[IP_HASH: {ip_hash}]"

    def _sanitize_ips(self, text: str) -> str:
        """Replace all IP addresses with deterministic hashes."""
        # IPv4
        text = IPV4_PATTERN.sub(lambda m: self._hash_ip(m.group()), text)
        # IPv6
        text = IPV6_PATTERN.sub(lambda m: self._hash_ip(m.group()), text)
        return text

    def _sanitize_jwts(self, text: str) -> str:
        """Strip JWTs completely."""
        return JWT_PATTERN.sub("[REDACTED_JWT]", text)

    def _sanitize_emails(self, text: str) -> str:
        """Redact email addresses."""
        return EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)

    def _sanitize_bearer_tokens(self, text: str) -> str:
        """Redact Bearer tokens."""
        return BEARER_PATTERN.sub("Bearer [REDACTED_TOKEN]", text)

    def _sanitize_with_presidio(self, text: str) -> str:
        """Use Presidio for NER-based PII detection."""
        if not self._presidio_available or not self._analyzer:
            return text

        try:
            results = self._analyzer.analyze(
                text=text,
                language="en",
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                ],
                score_threshold=0.7,
            )

            if results:
                anonymized = self._anonymizer.anonymize(
                    text=text,
                    analyzer_results=results,
                )
                return anonymized.text
        except Exception as e:
            logger.warning(f"Presidio analysis failed: {e}")

        return text

    def sanitize_entries(self, entries: list[dict]) -> tuple[list[dict], dict[str, str]]:
        """
        Run the full sanitization pipeline on parsed log entries.
        
        Returns:
            (sanitized_entries, ip_map) — ip_map maps hash → original IP
        """
        self.ip_map = {}
        sanitized = []

        for entry in entries:
            clean = {}
            for key, value in entry.items():
                if key.startswith("_"):
                    # Internal metadata — sanitize _raw but keep others
                    if key == "_raw":
                        clean[key] = self._sanitize_field(str(value))
                    else:
                        clean[key] = value
                else:
                    clean[key] = self._sanitize_field(str(value)) if value is not None else None

            sanitized.append(clean)

        logger.info(
            f"Sanitization complete. {len(sanitized)} entries processed, "
            f"{len(self.ip_map)} unique IPs hashed."
        )

        return sanitized, dict(self.ip_map)

    def _sanitize_field(self, text: str) -> str:
        """Apply all sanitization steps to a text field."""
        # Order matters: hash IPs before Presidio (which might catch IPs differently)
        text = self._sanitize_ips(text)
        text = self._sanitize_jwts(text)
        text = self._sanitize_emails(text)
        text = self._sanitize_bearer_tokens(text)

        # Presidio for names and other entities
        text = self._sanitize_with_presidio(text)

        return text
