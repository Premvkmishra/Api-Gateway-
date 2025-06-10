import time
from fastapi import Request, HTTPException
from db.crud import log_request
from core.rate_limit import check_rate_limit
from core.security import decode_token

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    user_id = None
    try:
        if "authorization" in request.headers:
            token = request.headers["authorization"].replace("Bearer ", "")
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
    except:
        pass
    client_ip = request.client.host
    rate_limit_key = f"ip:{client_ip}" if not user_id else f"user:{user_id}"
    if not check_rate_limit(rate_limit_key, limit=100):
        log_request(user_id, str(request.url.path), 429, 0)
        raise HTTPException(status_code=429, detail="Too many requests")
    response = await call_next(request)
    process_time = time.time() - start_time
    log_request(user_id, str(request.url.path), response.status_code, process_time)
    return response 