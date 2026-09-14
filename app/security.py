import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

PUBLIC_PATHS={"/health","/ready"}
class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        expected=os.getenv("CASE_API_KEY")
        if not expected or request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        if request.headers.get("X-API-Key") != expected:
            return JSONResponse(status_code=401, content={"detail":"Unauthorized"})
        return await call_next(request)
