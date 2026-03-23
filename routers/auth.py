from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_current_user
from database import get_db
from models.domain import User
from schemas.domain import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_me(user_update: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "university" in user_update:
        current_user.university = user_update["university"]
    if "department" in user_update:
        current_user.department = user_update["department"]
    db.commit()
    db.refresh(current_user)
    return current_user
