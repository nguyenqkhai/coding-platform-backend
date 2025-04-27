from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.users import User
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.auth import utils, oauth2

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(oauth2.get_current_admin_user)
):
    """
    Tạo người dùng mới (yêu cầu quyền admin)
    """
    # Kiểm tra username đã tồn tại
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Kiểm tra email đã tồn tại
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Tạo user mới
    hashed_password = utils.get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        bio=user.bio,
        is_active=user.is_active,
        is_admin=user.is_admin,
        rating=user.rating
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Đăng ký người dùng mới (không yêu cầu quyền admin)
    """
    # Kiểm tra username đã tồn tại
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Kiểm tra email đã tồn tại
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Tạo user mới (không có quyền admin)
    hashed_password = utils.get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        bio=user.bio,
        is_active=True,
        is_admin=False,
        rating=0
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_active_user)
):
    """
    Lấy danh sách người dùng
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(oauth2.get_current_active_user)
):
    """
    Lấy thông tin người dùng hiện tại
    """
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_active_user)
):
    """
    Lấy thông tin người dùng theo ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_active_user)
):
    """
    Cập nhật thông tin người dùng
    """
    # Chỉ admin hoặc chính người dùng đó mới có quyền cập nhật
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Lấy thông tin user cần cập nhật
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cập nhật thông tin user
    user_data = user_update.dict(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = utils.get_password_hash(user_data.pop("password"))
    
    # Chỉ có admin mới được cập nhật trạng thái admin
    if "is_admin" in user_data and not current_user.is_admin:
        user_data.pop("is_admin")
    
    for key, value in user_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2.get_current_admin_user)
):
    """
    Xóa người dùng (yêu cầu quyền admin)
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(db_user)
    db.commit()
    return None