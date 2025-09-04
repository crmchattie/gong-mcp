import jwt
import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.constants import JWT_ALGORITHM, JWT_SECRET, JWT_VALIDITY
from starlette.requests import Request

from app.models.auth import OAuthUserMCP
from app.models.user import User
from app.models.apikey import APIKey
from app.services.user import UserService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_oauth_client(self, client_id: str) -> OAuthUserMCP | None:
        stmt = select(OAuthUserMCP).where(OAuthUserMCP.client_id == client_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_oauth_client(
            self,
            client_id: str, 
            client_secret: str, 
            client_name: str, 
            redirect_uris: list[str]
        ) -> OAuthUserMCP | None:
        
        client = OAuthUserMCP(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_name,
            redirect_uris=redirect_uris,
            created_at=datetime.now()
        )
        self.db.add(client)
        try:
            await self.db.commit()
            return client
        except IntegrityError:
            await self.db.rollback()
            return None
    
    @staticmethod
    def create_access_token(email: str, tier: str, origin: str) -> str:
        payload = {
            "sub": email,
            "tier": tier,
            "origin": origin,
            "exp": time.time() + JWT_VALIDITY,
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def get_bearer_token(request: Request) -> str | None:
        headers = request.headers
        # Check if 'Authorization' header is present
        authorization_header = headers.get('Authorization')
        
        if authorization_header:
            # Split the header into 'Bearer <token>'
            parts = authorization_header.split()
            
            if len(parts) == 2 and parts[0] == 'Bearer':
                return parts[1]
            else:
                return None
        else:
            return None
    
    @staticmethod
    def get_user_from_request(request: Request) -> dict | None:
        token = AuthService.get_bearer_token(request)
        if not token:
            return None

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    async def generate_token_for_api_key(self, api_key: str) -> str | None:
        """
        Generate a JWT token for the given API key.
        """
        stmt = (
            select(APIKey)
            .options(selectinload(APIKey.user))
            .where(APIKey.token == api_key)
        )
        result = await self.db.execute(stmt)
        api_key: APIKey | None = result.scalar_one_or_none()
        if not api_key:
            return None
        
        user: User = api_key.user
        tier = await UserService(self.db).get_user_tier(user.email)
        token = self.create_access_token(user.email, tier, "apikey")
        return token
