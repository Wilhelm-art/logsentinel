"""
LogSentinel — Statistical Sampler
Intelligently downsamples large log files while retaining anomalous entries.
"""

import logging
import random
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# HTTP status codes considered anomalous
ERROR_STATUS_CODES = {400, 401, 403, 404, 405, 408, 413, 414, 429, 500, 502, 503, 504}

# HTTP methods that are unusual and worth keeping
UNUSUAL_METHODS = {"PUT", "DELETE", "PATCH", "OPTIONS", "TRACE", "CONNECT", "PROPFIND", "MKCOL"}

# Suspicious URI length threshold
SUSPICIOUS_URI_LENGTH = 200


class Sampler:
    """
    Statistically samples log entries to stay within LLM context limits.
    Prioritizes anomalous and potentially malicious entries.
    """

    @staticmethod
    def should_sample(total_lines: int) -> bool:
        """Check if sampling is needed."""
        return total_lines > settings.MAX_LOG_LINES

    @staticmethod
    def sample(entries: list[dict], target_size: int = None) -> tuple[list[dict], int]:
        """
        Downsample entries while retaining the most interesting ones.
        
        Returns:
            (sampled_entries, original_count)
        """
        if target_size is None:
            target_size = settings.SAMPLING_THRESHOLD

        original_count = len(entries)

        if original_count <= target_size:
            return entries, original_count

        logger.info(
            f"Sampling activated: {original_count} entries → target {target_size}"
        )

        # ── Priority Buckets ──
        priority_1 = []  # Error status codes (4xx, 5xx)
        priority_2 = []  # Unusual HTTP methods
        priority_3 = []  # Suspiciously long URIs
        priority_4 = []  # Parse failures (potentially malformed/attack payloads)
        normal = []      # Everything else

        for entry in entries:
            categorized = False

            # Check for error status
            status = entry.get("response") or entry.get("status") or entry.get("status_code")
            if status is not None:
                try:
                    status_int = int(status)
                    if status_int in ERROR_STATUS_CODES:
                        priority_1.append(entry)
                        categorized = True
                except (ValueError, TypeError):
                    pass

            # Check for unusual methods
            if not categorized:
                method = (entry.get("verb") or entry.get("method") or "").upper()
                if method in UNUSUAL_METHODS:
                    priority_2.append(entry)
                    categorized = True

            # Check for suspicious URI length
            if not categorized:
                request = entry.get("request") or entry.get("uri") or entry.get("path") or ""
                if len(str(request)) > SUSPICIOUS_URI_LENGTH:
                    priority_3.append(entry)
                    categorized = True

            # Check for parse failures
            if not categorized and entry.get("_parse_failed"):
                priority_4.append(entry)
                categorized = True

            if not categorized:
                normal.append(entry)

        # ── Assemble Sample ──
        sampled = []
        remaining = target_size

        # Add all priority entries (up to capacity)
        for bucket_name, bucket in [
            ("error_status", priority_1),
            ("unusual_methods", priority_2),
            ("long_uris", priority_3),
            ("parse_failures", priority_4),
        ]:
            to_add = bucket[:remaining]
            sampled.extend(to_add)
            remaining -= len(to_add)
            logger.info(f"  {bucket_name}: {len(to_add)} entries retained")

            if remaining <= 0:
                break

        # Fill remaining capacity with random normal entries
        if remaining > 0 and normal:
            random_sample = random.sample(normal, min(remaining, len(normal)))
            sampled.extend(random_sample)
            logger.info(f"  random_normal: {len(random_sample)} entries retained")

        # Sort by original line number to preserve temporal order
        sampled.sort(key=lambda e: e.get("_line_number", 0))

        logger.info(
            f"Sampling complete: {original_count} → {len(sampled)} entries "
            f"(P1:{len(priority_1)} P2:{len(priority_2)} P3:{len(priority_3)} P4:{len(priority_4)} Normal:{len(normal)})"
        )

        return sampled, original_count
