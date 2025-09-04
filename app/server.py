from fastapi import FastAPI

# Import Routers
from app.middleware import AuthenticationMiddleware, RedirectMiddleware
from app.routes.auth import auth_router

# Import Gong MCP 
from app.gong_mcp import gong_mcp as mcp

# SSE transport (deprecated)
# sse_app = mcp.http_app(transport="sse")

# Streamable HTTP transport (recommended)
http_app = mcp.http_app(transport="streamable-http")

app = FastAPI(
    title="Gong MCP Service",
    description="A service that provides Gong's sales call data and transcripts",
    version="1.0.0",
    lifespan=http_app.router.lifespan_context,
)
# app.mount("/mcp-server", sse_app, name="mcp-sse")
app.mount("/server", http_app, name="mcp-http")

app.include_router(auth_router, prefix="", tags=["Auth"])

app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RedirectMiddleware)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint showing service information."""
    return {
        "service": "Gong MCP Service",
        "version": "1.0.0",
        "status": "running",
    }

# Health check endpoint
@app.get("/health/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
