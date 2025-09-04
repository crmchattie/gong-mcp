from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import DBAsyncSession
from app.services.auth import AuthService
from app.services.user import UserService


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        scope_path = request.scope["path"]
        body = await request.body()
        print(f"[AuthenticationMiddleware] Request path: {scope_path}, Body: {body}")
        
        if not (scope_path.endswith("/sse") 
                or scope_path.endswith("/mcp")
                or scope_path.endswith("/mcp/")
            ):
            # Only apply authentication to the /mcp or /sse paths
            return await call_next(request)
        
        user = AuthService.get_user_from_request(request)
        if user is None:
            return Response(status_code=401, content="Unauthorized")

        # Validate if the user has MCP access
        async with DBAsyncSession() as session:
            has_mcp_access = await UserService(session).has_mcp_access(user["sub"])
            if not has_mcp_access:
                return Response(status_code=403, content="Forbidden")

        response = await call_next(request)
        return response


class RedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        scope_path = request.scope["path"]        
        # Only rewrite paths that don't end in '/' and would match a mounted streamable-http subapp
        if not scope_path.endswith("/") and scope_path + "/" in ["/server/mcp/"]:
            request.scope["path"] = scope_path + "/"

        return await call_next(request)
