from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import get_password_hash
from app.models.deficiency import User
from app.schemas.auth import Token, RefreshTokenInput, TokenPayload
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    db_user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=security.get_password_hash(user_in.password),
        age=user_in.age,
        gender=user_in.gender,
        height=user_in.height,
        weight=user_in.weight,
        bmi=user_in.bmi,
        activity_level=user_in.activity_level,
        occupation=user_in.occupation,
        sleep_hours=user_in.sleep_hours,
        water_intake_l=user_in.water_intake_l,
        is_smoker=user_in.is_smoker,
        drinks_alcohol=user_in.drinks_alcohol,
        medical_conditions=user_in.medical_conditions,
        food_allergies=user_in.food_allergies,
        diet_preference=user_in.diet_preference,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 token login — returns JWT access + refresh tokens."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = security.create_refresh_token(subject=user.id)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshTokenInput, db: Session = Depends(get_db)):
    """Validate refresh token and issue new token pair."""
    try:
        payload = jwt.decode(data.refresh_token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = security.create_refresh_token(subject=user.id)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Get current logged-in user profile."""
    return current_user


@router.put("/profile", response_model=UserOut)
def update_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated user's health profile.
    Only provided (non-None) fields are updated.
    """
    update_data = user_in.model_dump(exclude_unset=True)

    # Handle password separately
    password = update_data.pop("password", None)
    if password:
        current_user.password_hash = get_password_hash(password)

    # Auto-compute BMI if height/weight are updated
    for field, value in update_data.items():
        setattr(current_user, field, value)

    # Recompute BMI if we have both height and weight
    if current_user.height and current_user.weight and current_user.height > 0:
        current_user.bmi = round(current_user.weight / ((current_user.height / 100.0) ** 2), 2)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Stateless logout — client should delete stored tokens."""
    return {"detail": "Successfully logged out"}
