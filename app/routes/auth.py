from app.clients import redis_client
from app.constants import BASE_URL, JWT_VALIDITY
from app.models.auth import OAuthUserMCP
from app.dependencies import get_async_db
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, Body, Query, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import secrets, json, hashlib, base64
import logging

from app.services.auth import AuthService

from app.services.mixpanel import mixpanel_event_tracking
from app.services.user import UserService

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")

auth_router = APIRouter()


def store_auth_code(code: str, data: dict, expires_in: int = 600):
    redis_client.setex(f"auth_code:{code}", expires_in, json.dumps(data))


def get_auth_code(code: str):
    val = redis_client.get(f"auth_code:{code}")
    if val:
        redis_client.delete(f"auth_code:{code}")
        return json.loads(val)
    return None


@auth_router.api_route("/register", methods=["POST"])
async def register_client(
    client_name: str = Body(...),
    redirect_uris: list[str] = Body(...),
    token_endpoint_auth_method: str = Body("client_secret_post"),
    db: AsyncSession = Depends(get_async_db)
):
    client_id = secrets.token_urlsafe(16)
    client_secret = secrets.token_urlsafe(32)

    client_received = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": token_endpoint_auth_method,
    }
    logger.info(f"[REGISTER] Registering client: {client_received}")

    client = await AuthService(db).create_oauth_client(
        client_id=client_id,
        client_secret=client_secret,
        client_name=client_name,
        redirect_uris=redirect_uris
    )
    if not client:
        raise HTTPException(400, detail="Client already exists")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": token_endpoint_auth_method,
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
    }


@auth_router.api_route("/authorize", methods=["GET"], response_class=HTMLResponse)
async def authorize(
    request: Request,
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query(...),
    state: str = Query(...),
    code_challenge: str = Query(None),
    code_challenge_method: str = Query("S256"),
    db: AsyncSession = Depends(get_async_db)
):
    client: OAuthUserMCP = await AuthService(db).get_oauth_client(client_id)
    if not client:
        raise HTTPException(400, detail="Invalid client or redirect_uri")

    return templates.TemplateResponse("login.html", {
        "request": request,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method
    })


@auth_router.api_route("/login", methods=["POST"])
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    code_challenge: str = Form(...),
    state: str = Form(...),
    db: AsyncSession = Depends(get_async_db),
):
    auth_service = AuthService(db)
    oauth_client = await auth_service.get_oauth_client(client_id)
    if not oauth_client:
        raise HTTPException(401, detail="Invalid client credentials")

    user_service = UserService(db)
    is_valid = await user_service.validate_password(email, password)
    if not is_valid:
        print(f"[LOGIN] Invalid credentials for {email}")
        # Instead of raising HTTPException, render the login page with error
        return templates.TemplateResponse("login.html", {
            "request": request,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "error_message": "Incorrect email or password"
        })

    has_mcp_access = await user_service.has_mcp_access(email)
    if not has_mcp_access:
        logger.info(f"[LOGIN] User {email} does not have MCP access")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "error_message": "You don't have access to this service. Please contact your administrator or your Daloopa account team to request access"
        })

    tier = await user_service.get_user_tier(email)

    code = secrets.token_urlsafe(32)
    store_auth_code(code, {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "user_email": email,
        "user_tier": tier,
        "origin": oauth_client.client_name,
    }, expires_in=600)

    mixpanel_data = {
        "origin": oauth_client.client_name,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "user_tier": tier,
    }
    background_tasks.add_task(mixpanel_event_tracking, email, "oauth_login", mixpanel_data)

    return RedirectResponse(url=f"{redirect_uri}?code={code}&state={state}", status_code=302)


@auth_router.api_route("/token", methods=["POST"])
async def token(
    grant_type: str = Form(None),
    code: str = Form(None),
    redirect_uri: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
    code_verifier: str = Form(None),
    db: AsyncSession = Depends(get_async_db),
):  
    # Log the input
    input = {
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "code_verifier": code_verifier,
    }
    logger.info(f"[TOKEN] Received token request with input: {input}")
    print(f"[TOKEN] Received token request with input: {input}")

    data = get_auth_code(code)
    if not data:
        raise HTTPException(400, detail="Invalid or expired code")

    if data["client_id"] != client_id:
        logger.info(f"[TOKEN] Mismatched redirect_uri or client_id")
        raise HTTPException(400, detail="Mismatched redirect_uri or client_id")

    auth_service = AuthService(db)
    # Validate client_secret if provided
    if client_secret:
        client = await auth_service.get_oauth_client(client_id)
        if not client or client.client_secret != client_secret:
            raise HTTPException(401, detail="Invalid client credentials")

    # Validate PKCE if code_verifier provided
    if code_verifier:
        if "code_challenge" not in data:
            raise HTTPException(400, detail="PKCE verification failed")
            
        digest = hashlib.sha256(code_verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        if data["code_challenge"] != challenge:
            raise HTTPException(400, detail="PKCE verification failed")

    access_token = auth_service.create_access_token(
        email=data["user_email"], 
        tier=data["user_tier"],
        origin=data["origin"],
    )
    logger.info(f"[TOKEN] Access token created for user: {data['user_email']}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_VALIDITY
    }


@auth_router.api_route("/auth/token", methods=["POST"])
async def api_key_token(api_key: str = Body(..., embed=True), db: AsyncSession = Depends(get_async_db)):
    token = await AuthService(db).generate_token_for_api_key(api_key)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_VALIDITY
    })


@auth_router.api_route("/.well-known/oauth-authorization-server", methods=["GET"])
async def well_known():
    return JSONResponse({
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/authorize",
        "token_endpoint":  f"{BASE_URL}/token",
        "registration_endpoint":  f"{BASE_URL}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
    })
