import os

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_VALIDITY = os.getenv("JWT_VALIDITY", 86400 * 7)

# Gong API Configuration
BASE_URL = "https://mcp.gong.io"
GONG_API_URL = "https://api.gong.io/v2"

# Gong API Endpoints
GONG_CALLS_API = f"{GONG_API_URL}/calls"
GONG_TRANSCRIPTS_API = f"{GONG_API_URL}/calls/transcript"

# Security Configuration
TIER_TIME_LIMITS = {
    "FREE": {"limit": 30, "days": 7},
    "TRIAL": {"limit": 30, "days": 7},
    "STUDENT": {"limit": 30, "days": 7},
    "ENTERPRISE": {"limit": 30, "days": 7},
}

TIER_TOTAL_LIMITS = {
    "FREE": 100,
    "TRIAL": 100,
    "STUDENT": 100,
    "ENTERPRISE": 100,
}
