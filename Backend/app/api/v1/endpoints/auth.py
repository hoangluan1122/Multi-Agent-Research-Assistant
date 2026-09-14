"""
Endpoints quản lý Xác thực & Tài khoản người dùng (Auth API).
Hỗ trợ đăng ký (register), đăng nhập (login) và lấy thông tin cá nhân (me).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng ký tài khoản người dùng mới:
    - Kiểm tra email đã tồn tại hay chưa.
    - Băm mật khẩu bằng PBKDF2-HMAC-SHA256.
    - Lưu User vào database và trả về JWT Access Token.
    """
    stmt = select(User).where(User.email == payload.email.lower().strip())
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Địa chỉ Email này đã được đăng ký tài khoản."
        )
    
    new_user = User(
        email=payload.email.lower().strip(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role="user",
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Tạo JWT Token
    token = create_access_token({"sub": new_user.id, "email": new_user.email})
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng nhập bằng Email và Password:
    - Kiểm tra mật khẩu.
    - Trả về JWT Access Token nếu thông tin chính xác.
    """
    stmt = select(User).where(User.email == payload.email.lower().strip())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này đã bị khóa."
        )
    
    token = create_access_token({"sub": user.id, "email": user.email})
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin tài khoản của người dùng đang đăng nhập.
    """
    return UserResponse.model_validate(current_user)

