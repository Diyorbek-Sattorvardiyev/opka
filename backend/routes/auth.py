from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import create_access_token, get_current_user, hash_password, password_fits_bcrypt, verify_password
from models.user import User
from schemas.auth_schema import TokenOut, UserCreate, UserLogin, UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


def ok(message: str, data):
    return {"success": True, "message": message, "data": data}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if not password_fits_bcrypt(payload.password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parol 72 baytdan oshmasin")

    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(full_name=payload.full_name.strip(), email=payload.email.lower(), hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    data = TokenOut(access_token=token, user=UserOut.model_validate(user)).model_dump(mode="json")
    return ok("Ro'yxatdan o'tish muvaffaqiyatli yakunlandi", data)


@router.post("/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email yoki parol noto'g'ri")

    token = create_access_token(str(user.id))
    data = TokenOut(access_token=token, user=UserOut.model_validate(user)).model_dump(mode="json")
    return ok("Tizimga kirish muvaffaqiyatli", data)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return ok("Foydalanuvchi ma'lumotlari", UserOut.model_validate(current_user).model_dump(mode="json"))
