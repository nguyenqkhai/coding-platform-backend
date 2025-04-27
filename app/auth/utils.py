import bcrypt
from passlib.context import CryptContext

# Sử dụng passlib để băm và xác thực mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Kiểm tra mật khẩu"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Băm mật khẩu"""
    return pwd_context.hash(password)