# LogSentinel — AI-Powered Security Log Analyzer

> Enterprise-grade log analysis platform that leverages LLMs for automated threat detection, PII sanitization, and WAF rule generation.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20Celery-green)
![LLMs](https://img.shields.io/badge/LLM-Gemini%20%7C%20Groq-purple)

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Nginx Reverse Proxy                │
│                    (Port 80/443)                     │
├─────────────────────┬────────────────────────────────┤
│   Next.js 14        │        FastAPI Backend         │
│   (Frontend)        │        (Port 8000)             │
│   - NextAuth v5     │        - Log Parser            │
│   - Dashboard       │        - PII Sanitizer         │
│   - Report Viewer   │        - Threat Intel           │
│   - Live Tail       │        - LLM Orchestrator      │
├─────────────────────┴────────────────────────────────┤
│                    Celery Workers                     │
│            (Background Analysis Tasks)               │
├──────────────────────┬───────────────────────────────┤
│   PostgreSQL 16      │         Redis 7               │
│   (Reports & Tasks)  │   (Queue & Cache)             │
└──────────────────────┴───────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Google/GitHub OAuth app credentials
- Gemini API key and/or Groq API key
- (Optional) AbuseIPDB API key

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/logsentinel.git
cd logsentinel

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: AUTH_SECRET, OAuth credentials, LLM API key
```

### 2. Generate Auth Secret

```bash
npx auth secret
# Copy the generated secret to AUTH_SECRET in .env
```

### 3. Build & Run

```bash
docker compose build
docker compose up -d
```

### 4. Verify

```bash
# Check all services are healthy
docker compose ps

# Check backend health
curl http://localhost/api/health

# Open in browser
open http://localhost
```

## 📋 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AUTH_SECRET` | ✅ | NextAuth encryption secret |
| `AUTH_GOOGLE_ID` | ✅ | Google OAuth client ID |
| `AUTH_GOOGLE_SECRET` | ✅ | Google OAuth client secret |
| `AUTH_GITHUB_ID` | ✅ | GitHub OAuth app client ID |
| `AUTH_GITHUB_SECRET` | ✅ | GitHub OAuth app secret |
| `ALLOWED_EMAILS` | ✅ | Comma-separated allowed email addresses |
| `POSTGRES_PASSWORD` | ✅ | PostgreSQL password |
| `LLM_PROVIDER` | ✅ | `gemini` or `groq` |
| `GEMINI_API_KEY` | ⚡ | Required if LLM_PROVIDER=gemini |
| `GROQ_API_KEY` | ⚡ | Required if LLM_PROVIDER=groq |
| `ABUSEIPDB_API_KEY` | ❌ | Optional threat intelligence |
| `ABUSEIPDB_ENABLED` | ❌ | Default: true |

## 🔐 Security Pipeline

1. **Log Parsing** — Grok patterns auto-detect Nginx/Apache/JSONL formats
2. **PII Sanitization** — Microsoft Presidio + regex strips emails, names, JWTs
3. **IP Hashing** — All IPs → deterministic SHA-256 hashes (maintains tracking context)
4. **Threat Enrichment** — AbuseIPDB cross-reference with Redis caching
5. **LLM Analysis** — Structured JSON output with schema enforcement
6. **Report Storage** — Only AI metadata persisted; raw logs destroyed

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/logs/upload` | Upload log file for analysis |
| `GET` | `/api/v1/logs/status/{task_id}` | Poll analysis progress |
| `GET` | `/api/v1/logs/report/{task_id}` | Get completed report |
| `GET` | `/api/v1/logs/history` | List past analyses |
| `GET` | `/api/v1/logs/tail` | SSE live log stream |
| `GET` | `/health` | System health check |

## 🧪 Sample Data

Test logs are provided in `samples/sample_nginx.log` containing:
- SQL injection attempts (sqlmap patterns)
- XSS payloads in query strings and User-Agent headers
- Path traversal attacks (DirBuster)
- Brute-force login attempts (repeated 401s)
- LLM prompt injection in User-Agent
- PII (emails, JWTs) for sanitization testing

## 📄 License

MIT
