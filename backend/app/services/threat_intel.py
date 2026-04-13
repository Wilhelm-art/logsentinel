"""
LogSentinel — Threat Intelligence Service
Queries AbuseIPDB for IP reputation and enriches log entries.
"""

import json
import logging
from typing import Optional

import httpx
import redis

from app.config import settings

logger = logging.getLogger(__name__)

ABUSEIPDB_CHECK_URL = "https://api.abuseipdb.com/api/v2/check"
CACHE_TTL = 86400  # 24 hours


class ThreatIntelService:
    """Queries AbuseIPDB and enriches log entries with threat scores."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
            )
            self.redis_client.ping()
            logger.info("Redis connected for threat intel caching")
        except Exception as e:
            logger.warning(f"Redis connection failed for threat intel: {e}")
            self.redis_client = None

    def _get_cached(self, ip: str) -> Optional[dict]:
        """Check Redis cache for an IP lookup result."""
        if not self.redis_client:
            return None
        try:
            cached = self.redis_client.get(f"abuseipdb:{ip}")
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        return None

    def _set_cached(self, ip: str, data: dict):
        """Cache an IP lookup result in Redis."""
        if not self.redis_client:
            return
        try:
            self.redis_client.setex(
                f"abuseipdb:{ip}",
                CACHE_TTL,
                json.dumps(data),
            )
        except Exception:
            pass

    def check_ip(self, ip: str) -> Optional[dict]:
        """
        Query AbuseIPDB for a single IP.
        Returns the data dict or None if unavailable.
        """
        if not settings.ABUSEIPDB_ENABLED or not settings.ABUSEIPDB_API_KEY:
            return None

        # Check cache first
        cached = self._get_cached(ip)
        if cached is not None:
            return cached

        try:
            response = httpx.get(
                ABUSEIPDB_CHECK_URL,
                params={"ipAddress": ip, "maxAgeInDays": "90"},
                headers={
                    "Accept": "application/json",
                    "Key": settings.ABUSEIPDB_API_KEY,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json().get("data", {})

            result = {
                "ip": ip,
                "abuse_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "country_code": data.get("countryCode", ""),
                "isp": data.get("isp", ""),
                "is_whitelisted": data.get("isWhitelisted", False),
            }

            self._set_cached(ip, result)
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("AbuseIPDB rate limit reached")
            else:
                logger.error(f"AbuseIPDB API error: {e}")
        except Exception as e:
            logger.error(f"AbuseIPDB query failed for {ip}: {e}")

        return None

    def enrich_entries(
        self,
        entries: list[dict],
        ip_map: dict[str, str],
    ) -> list[dict]:
        """
        Enrich sanitized log entries with threat intelligence.
        Uses the ip_map (hash → original IP) to query AbuseIPDB,
        then tags the hashed entries with threat scores.
        """
        if not settings.ABUSEIPDB_ENABLED or not settings.ABUSEIPDB_API_KEY:
            logger.info("AbuseIPDB disabled or no API key, skipping enrichment")
            return entries

        # Query unique IPs
        threat_data: dict[str, dict] = {}
        for ip_hash, original_ip in ip_map.items():
            result = self.check_ip(original_ip)
            if result and result.get("abuse_score", 0) > 0:
                threat_data[ip_hash] = result

        if not threat_data:
            logger.info("No threat intelligence hits found")
            return entries

        logger.info(f"Found {len(threat_data)} IPs with threat intelligence data")

        # Enrich entries
        for entry in entries:
            raw = entry.get("_raw", "")
            for ip_hash, intel in threat_data.items():
                hash_tag = f"[IP_HASH: {ip_hash}]"
                if hash_tag in raw:
                    score = intel["abuse_score"]
                    entry["_raw"] = raw.replace(
                        hash_tag,
                        f"{hash_tag} [THREAT_INTEL: MALICIOUS_SCORE_{score}]"
                    )
                    entry["_threat_intel"] = intel
                    raw = entry["_raw"]  # Update for subsequent replacements

        return entries
