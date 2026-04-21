"""
LogSentinel — Log Parser Service
Parses Nginx, Apache, and JSONL logs into structured dictionaries using py3grok.
"""

import json
import logging
from typing import Optional

from py3grok import GrokEnvironment

logger = logging.getLogger(__name__)
grok_env = GrokEnvironment()

# Pre-compiled patterns
NGINX_COMBINED = grok_env.create(
    '%{IPORHOST:clientip} %{USER:ident} %{USER:auth} \\[%{HTTPDATE:timestamp}\\] '
    '"%{WORD:verb} %{URIPATHPARAM:request} HTTP/%{NUMBER:httpversion}" '
    '%{NUMBER:response:int} %{NUMBER:bytes:int} "%{DATA:referrer}" "%{DATA:agent}"'
)

APACHE_COMBINED = grok_env.create(
    '%{COMMONAPACHELOG} "%{DATA:referrer}" "%{DATA:agent}"'
)

APACHE_COMMON = grok_env.create('%{COMMONAPACHELOG}')

# Simpler nginx pattern as fallback
NGINX_SIMPLE = grok_env.create(
    '%{IPORHOST:clientip} - - \\[%{HTTPDATE:timestamp}\\] '
    '"%{DATA:request}" %{NUMBER:response:int} %{NUMBER:bytes:int}'
)


class LogParser:
    """Parses log files into structured dictionaries."""

    PATTERNS = [
        ("nginx", NGINX_COMBINED),
        ("apache", APACHE_COMBINED),
        ("apache", APACHE_COMMON),
        ("nginx", NGINX_SIMPLE),
    ]

    @staticmethod
    def detect_format(lines: list[str]) -> str:
        """Auto-detect log format from the first non-empty lines."""
        sample = [l.strip() for l in lines[:20] if l.strip()]

        if not sample:
            return "unknown"

        # Check if JSONL
        json_count = 0
        for line in sample[:5]:
            try:
                json.loads(line)
                json_count += 1
            except (json.JSONDecodeError, ValueError):
                pass

        if json_count >= 3:
            return "jsonl"

        # Try grok patterns
        for name, pattern in LogParser.PATTERNS:
            matches = 0
            for line in sample[:10]:
                result = pattern.match(line)
                if result:
                    matches += 1
            if matches >= 3:
                return name

        return "unknown"

    @staticmethod
    def parse(raw_content: str) -> tuple[list[dict], str, int]:
        """
        Parse raw log content into structured dictionaries.
        
        Returns:
            (parsed_entries, format_detected, total_line_count)
        """
        lines = raw_content.splitlines()
        total_lines = len(lines)

        if not lines:
            return [], "unknown", 0

        # Detect format
        log_format = LogParser.detect_format(lines)
        logger.info(f"Detected log format: {log_format} ({total_lines} lines)")

        parsed = []

        if log_format == "jsonl":
            parsed = LogParser._parse_jsonl(lines)
        elif log_format in ("nginx", "apache"):
            parsed = LogParser._parse_grok(lines, log_format)
        else:
            # Fallback: treat each line as raw text
            parsed = LogParser._parse_raw(lines)

        logger.info(f"Successfully parsed {len(parsed)}/{total_lines} lines")
        return parsed, log_format, total_lines

    @staticmethod
    def _parse_jsonl(lines: list[str]) -> list[dict]:
        """Parse JSONL format."""
        entries = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry["_line_number"] = i + 1
                entry["_raw"] = line
                entries.append(entry)
            except json.JSONDecodeError:
                logger.debug(f"Skipping malformed JSONL at line {i + 1}")
        return entries

    @staticmethod
    def _parse_grok(lines: list[str], log_format: str) -> list[dict]:
        """Parse using Grok patterns."""
        entries = []

        # Try all patterns of the detected format, then fallback to others
        ordered_patterns = [
            (n, p) for n, p in LogParser.PATTERNS if n == log_format
        ] + [
            (n, p) for n, p in LogParser.PATTERNS if n != log_format
        ]

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            parsed = None
            for name, pattern in ordered_patterns:
                result = pattern.match(line)
                if result:
                    parsed = result
                    break

            if parsed:
                parsed["_line_number"] = i + 1
                parsed["_raw"] = line
                entries.append(parsed)
            else:
                # Keep unparseable lines as raw entries
                entries.append({
                    "_line_number": i + 1,
                    "_raw": line,
                    "_parse_failed": True,
                })

        return entries

    @staticmethod
    def _parse_raw(lines: list[str]) -> list[dict]:
        """Fallback: wrap each line in a dict."""
        return [
            {"_line_number": i + 1, "_raw": line.strip(), "_parse_failed": True}
            for i, line in enumerate(lines)
            if line.strip()
        ]
