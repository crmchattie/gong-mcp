import redis
import os
from mixpanel import Mixpanel
 
# Redis Client Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_KEY = os.getenv("REDIS_KEY")
REDIS_URL = f"rediss://:{REDIS_KEY}@{REDIS_HOST}:{REDIS_PORT}/0?ssl_cert_reqs=required"

redis_client = redis.from_url(REDIS_URL)

# Mixpanel Client Configuration
MIXPANEL_KEY = os.getenv("MIXPANEL_KEY")
mixpanel_client = Mixpanel(MIXPANEL_KEY)
