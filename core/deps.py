from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from firebase_admin import auth
import logging

from database import get_db
from models.domain import User

security = HTTPBearer()
logger = logging.getLogger(__name__)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        name = decoded_token.get("name", "")
        avatar_url = decoded_token.get("picture", "")

        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            user = User(
                firebase_uid=uid,
                email=email,
                name=name,
                avatar_url=avatar_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        # In dev mode, we might want to bypass or allow mock tokens if firebase isn't fully configured
        # But per requirements we implement verify_id_token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
