"""
Authentication routes
Handles user registration, login, and current user retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User as UserModel
from app.schemas import User, UserCreate, UserLogin, Token, AuthResponse, UserMeUpdate
from app.utils.auth import verify_password, get_password_hash, create_access_token
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user object with access token

    Raises:
        HTTPException: If email already registered
    """
    # Check if user already exists
    existing_user = db.query(UserModel).filter(
        UserModel.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = UserModel(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        birthday=user_data.birthday,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token for the new user
    access_token = create_access_token(data={"sub": new_user.id})

    return {
        "user": new_user,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(UserModel).filter(
        UserModel.email == credentials.email
    ).first()

    # Verify password
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        Current user object
    """
    return current_user


@router.patch("/me", response_model=User)
async def update_current_user_info(
    body: UserMeUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current authenticated user profile fields (currently: birthday).
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.birthday = body.birthday
    db.commit()
    db.refresh(user)
    return user


@router.put("/me", response_model=User)
async def put_current_user_info(
    body: UserMeUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Same as PATCH /me (some environments prefer PUT over PATCH).
    """
    user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.birthday = body.birthday
    db.commit()
    db.refresh(user)
    return user
