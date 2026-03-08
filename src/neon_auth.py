"""
Neon Authentication Service for SafeRouteAI
Handles user authentication and session management using Neon Auth
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from neon_database import neon_db, User

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Neon Auth Configuration
NEON_AUTH_URL = os.getenv("NEON_AUTH_URL", "https://auth.neon.tech")

security = HTTPBearer()

class NeonAuthService:
    """
    Authentication service using Neon Auth and JWT tokens
    """
    
    def __init__(self):
        self.jwt_secret = JWT_SECRET
        self.jwt_algorithm = JWT_ALGORITHM
        self.expiration_hours = JWT_EXPIRATION_HOURS
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token for user"""
        expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def authenticate_with_neon(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with Neon Auth
        In production, this would integrate with Neon's authentication system
        For now, we'll simulate the authentication process
        """
        try:
            # In production, this would be a real API call to Neon Auth
            # For demo purposes, we'll create/get the user from our database
            
            # Check if user exists in our database
            user = await neon_db.get_user_by_email(email)
            
            if not user:
                # Create new user (in production, this would come from Neon Auth)
                user = await neon_db.create_user(email=email, name=email.split('@')[0])
                logger.info(f"Created new user: {email}")
            
            # Update last login
            await neon_db.update_user_login(user.id)
            
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "preferences": user.preferences,
                "last_login": user.last_login
            }
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None
    
    async def register_user(self, email: str, name: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Register new user with Neon Auth
        """
        try:
            # Check if user already exists
            existing_user = await neon_db.get_user_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already exists"
                )
            
            # In production, this would register with Neon Auth first
            # For demo, we'll create the user directly
            user = await neon_db.create_user(email=email, name=name)
            
            logger.info(f"Registered new user: {email}")
            
            return {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "preferences": user.preferences,
                "created_at": user.created_at
            }
            
        except Exception as e:
            logger.error(f"Registration failed for {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """
        Get current authenticated user from JWT token
        """
        try:
            # Verify the token
            payload = self.verify_token(credentials.credentials)
            
            # Get user from database
            user = await neon_db.get_user_by_email(payload["email"])
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication"
            )
    
    async def refresh_token(self, token: str) -> str:
        """Refresh JWT token"""
        try:
            # Verify current token (even if expired, we'll allow refresh)
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": False}  # Don't verify expiration for refresh
            )
            
            # Get fresh user data
            user = await neon_db.get_user_by_email(payload["email"])
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new token
            user_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
            
            return self.create_access_token(user_data)
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    async def logout_user(self, user_id: str) -> bool:
        """
        Logout user (in production, this would invalidate tokens)
        """
        try:
            # In production, you'd add the token to a blacklist
            # For now, we'll just log the logout
            logger.info(f"User {user_id} logged out")
            return True
            
        except Exception as e:
            logger.error(f"Logout failed for user {user_id}: {e}")
            return False
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            await neon_db.update_user_preferences(user_id, preferences)
            return True
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return False

# Global auth service instance
auth_service = NeonAuthService()

# Dependency for protected routes
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    return await auth_service.get_current_user(credentials)

# Optional authentication (for routes that work with or without auth)
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[User]:
    """Optional authentication dependency"""
    if credentials:
        try:
            return await auth_service.get_current_user(credentials)
        except HTTPException:
            return None
    return None