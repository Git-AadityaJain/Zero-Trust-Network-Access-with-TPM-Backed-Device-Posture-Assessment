from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.security.passwords import hash_password

def create_user(db: Session, user: UserCreate):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise ValueError("Username already registered")
    hashed = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_users(db: Session):
    return db.query(User).all()
