import time
from core.config import REDIS_HOST, REDIS_PORT, REDIS_DB
import redis

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None

def check_rate_limit(identifier: str, limit: int = 60, window: int = 60) -> bool:
    if not redis_client:
        return True
    current_time = int(time.time())
    window_start = current_time - window
    redis_client.zremrangebyscore(f"rate_limit:{identifier}", 0, window_start)
    current_count = redis_client.zcard(f"rate_limit:{identifier}")
    if current_count >= limit:
        return False
    redis_client.zadd(f"rate_limit:{identifier}", {str(current_time): current_time})
    redis_client.expire(f"rate_limit:{identifier}", window)
    return True 