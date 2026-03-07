from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from entity.user import User
from params.user import UserCreateParams
from response.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).all()


@router.post("/", response_model=UserResponse)
def create_user(params: UserCreateParams, db: Session = Depends(get_db)) -> User:
    user = User(name=params.name, email=params.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
