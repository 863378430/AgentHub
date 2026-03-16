from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import pymysql
import bcrypt
from typing import Optional

# -------------------------- 核心配置 --------------------------
MYSQL_URL = "mysql+pymysql://root:123456@192.168.100.128:3306/agent?charset=utf8mb4"
SECRET_KEY = "your-secret-key-keep-it-safe-123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60

# -------------------------- 初始化 --------------------------
app = FastAPI()

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MySQL连接
engine = create_engine(MYSQL_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------- 数据库模型 --------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    permissions = Column(String(500), default="")
    status = Column(Integer, default=1)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# -------------------------- Pydantic模型 --------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

# -------------------------- 工具函数 --------------------------
# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # 统一转为 bytes 进行校验
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"密码校验失败: {e}")
        return False

# 生成JWT令牌
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 验证用户
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email, User.status == 1).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    
    perm_list = user.permissions.split(',') if user.permissions else []
    user_info = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "permissions": perm_list
    }
    
    user.last_login_at = datetime.now()
    db.commit()
    return user_info

# 核心修复：自定义依赖函数解析Token（从请求头获取）
def get_token_from_header(authorization: Optional[str] = Header(None)):
    """从Authorization请求头解析token"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="未提供令牌，请在请求头中添加 Authorization: Bearer <token>"
        )
    parts = authorization.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise HTTPException(
            status_code=401,
            detail="令牌格式错误，正确格式：Authorization: Bearer <token>"
        )
    return parts[1]

# 验证令牌并返回用户信息
def get_current_user(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="令牌无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email, User.status == 1).first()
    if not user:
        raise credentials_exception
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "permissions": user.permissions.split(',') if user.permissions else []
    }

# -------------------------- 接口 --------------------------
# 登录接口
@app.post("/login", response_model=Token)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user_info = authenticate_user(db, form_data.email, form_data.password)
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="邮箱/密码错误或用户已禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user_info["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": user_info
    }

# 获取当前用户信息（修复依赖注入）
@app.get("/api/user/info")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {"code": 200, "data": current_user}

# 权限测试接口（修复依赖注入）
@app.get("/api/test/perm/{perm_code}")
async def test_permission(perm_code: str, current_user: dict = Depends(get_current_user)):
    if perm_code not in current_user["permissions"]:
        raise HTTPException(status_code=403, detail=f"无{perm_code}权限")
    return {"code": 200, "data": f"验证通过：你拥有{perm_code}权限"}

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)