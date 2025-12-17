import base64
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Simple authentication middleware that extracts Gong credentials from HTTP Basic Auth.
    Users provide their Gong Access Key as Client ID and Gong Access Secret as Client Secret.
    """
    async def dispatch(self, request: Request, call_next):
        scope_path = request.scope["path"]

        # Only apply authentication to the /mcp or /sse paths
        if not (scope_path.endswith("/sse")
                or scope_path.endswith("/mcp")
                or scope_path.endswith("/mcp/")
            ):
            return await call_next(request)

        # Extract credentials from Authorization header (HTTP Basic Auth)
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Basic "):
            return Response(
                status_code=401,
                content="Unauthorized: Missing or invalid Authorization header. Please provide Gong credentials via HTTP Basic Auth.",
                headers={"WWW-Authenticate": "Basic realm=\"Gong MCP Server\""}
            )

        try:
            # Decode Basic Auth credentials
            encoded_credentials = auth_header.replace("Basic ", "")
            decoded_bytes = base64.b64decode(encoded_credentials)
            decoded_str = decoded_bytes.decode("utf-8")

            # Split into access_key:access_secret
            if ":" not in decoded_str:
                return Response(status_code=401, content="Unauthorized: Invalid credentials format")

            access_key, access_secret = decoded_str.split(":", 1)

            # Store credentials in request state for use by the MCP tools
            request.state.gong_access_key = access_key
            request.state.gong_access_secret = access_secret

        except Exception as e:
            return Response(
                status_code=401,
                content=f"Unauthorized: Failed to decode credentials - {str(e)}"
            )

        response = await call_next(request)
        return response


class RedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        scope_path = request.scope["path"]        
        # Only rewrite paths that don't end in '/' and would match a mounted streamable-http subapp
        if not scope_path.endswith("/") and scope_path + "/" in ["/server/mcp/"]:
            request.scope["path"] = scope_path + "/"

        return await call_next(request)
