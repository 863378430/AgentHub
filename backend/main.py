from fastapi import FastAPI, HTTPException, Depends, Header, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, ConfigDict  # 新增导入 ConfigDict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, CHAR, Index
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import pymysql
import bcrypt
import random
import string
from typing import Optional, List, Dict, Literal  # 保留Literal用于模式枚举

# -------------------------- 核心配置 --------------------------
MYSQL_URL = "mysql+pymysql://root:123456@192.168.100.128:3306/agent?charset=utf8mb4"
SECRET_KEY = "your-secret-key-keep-it-safe-123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60

# 定义支持的模式（仅接口层面使用，不入库）
SUPPORTED_MODES = Literal["自动", "数据", "配置", "翻译", "代码"]

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

# -------------------------- 数据库模型（无mode字段） --------------------------
# 原有用户表
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

# 新增对话主表模型
class ChatConversation(Base):
    __tablename__ = "chat_conversation"
    conversation_id = Column(CHAR(16), primary_key=True, comment="16位聊天对话ID")
    username = Column(String(50), nullable=False, comment="用户名")
    title = Column(String(100), default="", comment="对话标题")
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除（软删除）")
    
    # 索引
    __table_args__ = (
        Index("idx_username", "username"),
    )

# 消息详情表模型（无mode字段）
class ChatMessage(Base):
    __tablename__ = "chat_message"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="消息自增主键")
    conversation_id = Column(CHAR(16), nullable=False, comment="关联16位对话ID")
    username = Column(String(50), nullable=False, comment="用户名")
    role = Column(String(20), nullable=False, comment="角色（user/assistant）")
    content = Column(Text, nullable=False, comment="消息内容")
    create_time = Column(DateTime, default=datetime.now, comment="发送时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除（软删除）")
    
    # 索引（无mode索引）
    __table_args__ = (
        Index("idx_conversation_id", "conversation_id"),
        Index("idx_create_time", "create_time"),
    )

# 初始化数据库表（首次运行时执行）
Base.metadata.create_all(bind=engine)

# -------------------------- Pydantic模型 --------------------------
# 原有登录模型
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

# 新增对话相关模型
class ConversationCreate(BaseModel):
    """创建对话的入参"""
    username: str = Field(..., max_length=50, description="用户名")
    title: Optional[str] = Field("", max_length=100, description="对话标题")

class ConversationUpdate(BaseModel):
    """更新对话的入参"""
    title: Optional[str] = Field(None, max_length=100, description="新的对话标题")

class ConversationResponse(BaseModel):
    """对话响应模型"""
    conversation_id: str
    username: str
    title: str
    create_time: datetime
    update_time: datetime

    # 修复：替换为 Pydantic V2 推荐的 ConfigDict 方式
    model_config = ConfigDict(from_attributes=True)  # 替代原 orm_mode=True

# 消息相关模型（无mode字段）
class MessageCreate(BaseModel):
    """创建消息的入参"""
    conversation_id: str = Field(..., min_length=16, max_length=16, description="16位对话ID")
    username: str = Field(..., max_length=50, description="用户名")
    role: str = Field(..., pattern="^(user|assistant)$", description="角色（user/assistant）")
    content: str = Field(..., description="消息内容")

class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    conversation_id: str
    username: str
    role: str
    content: str
    create_time: datetime

    # 修复：替换为 Pydantic V2 推荐的 ConfigDict 方式
    model_config = ConfigDict(from_attributes=True)  # 替代原 orm_mode=True

# 聊天接口入参模型（含mode，仅接口使用）
class ChatRequest(BaseModel):
    """聊天请求入参（用户发送消息+模式）"""
    conversation_id: str = Field(..., min_length=16, max_length=16, description="16位对话ID")
    username: str = Field(..., max_length=50, description="用户名")
    content: str = Field(..., description="用户消息内容")
    mode: SUPPORTED_MODES = Field("自动", description="对话模式（自动/数据/配置/翻译/代码）")

# 聊天接口响应模型（含mode，仅接口返回）
class ChatResponse(BaseModel):
    """聊天响应（返回AI回复+模式）"""
    content: str = Field(..., description="AI回复内容")
    mode: SUPPORTED_MODES = Field(..., description="当前使用的模式")
    conversation_id: str = Field(..., description="对话ID")

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

# 从请求头解析Token
def get_token_from_header(authorization: Optional[str] = Header(None)):
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

# 生成16位唯一对话ID（时间戳+随机字符）
def generate_conversation_id() -> str:
    # 前8位：年月日（如20260316）
    date_part = datetime.now().strftime("%Y%m%d")
    # 后8位：随机数字+字母（确保唯一）
    random_part = ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))
    return date_part + random_part

# 核心：根据模式生成AI回复（仅接口层面使用，不入库）
def get_ai_response_by_mode(user_content: str, mode: SUPPORTED_MODES) -> str:
    """
    根据不同模式返回对应AI回复（模式仅在接口层使用，不存储到数据库）
    :param user_content: 用户输入内容
    :param mode: 对话模式
    :return: AI回复文本
    """
    mode_responses = {
        "自动": f"这是一条自动模式下的AI回复。你输入的内容是：{user_content}",
        "数据": f"这是一条数据模式下的AI回复。针对你输入的「{user_content}」，我会为你提供数据相关的分析和解答。",
        "配置": f"这是一条配置模式下的AI回复。针对你输入的「{user_content}」，我会为你提供系统配置相关的建议和指导。",
        "翻译": f"这是一条翻译模式下的AI回复。你输入的「{user_content}」的英文翻译是：{user_content} (Translation Mode Response)",
        "代码": f"这是一条代码模式下的AI回复。针对你输入的「{user_content}」，我会为你提供代码相关的实现方案和解释。"
    }
    return mode_responses[mode]

# -------------------------- 原有登录接口 --------------------------
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

@app.get("/api/user/info")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {"code": 200, "data": current_user}

# -------------------------- 对话（ChatConversation）增删改查接口 --------------------------
# 1. 创建对话
@app.post("/api/conversation", response_model=ConversationResponse, summary="创建新对话")
async def create_conversation(
    conv: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 需登录
):
    # 生成16位对话ID
    conv_id = generate_conversation_id()
    # 创建对话记录
    db_conv = ChatConversation(
        conversation_id=conv_id,
        username=conv.username,
        title=conv.title
    )
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv

# 2. 获取单个对话详情
@app.get("/api/conversation/{conversation_id}", response_model=ConversationResponse, summary="获取单个对话")
async def get_conversation(
    conversation_id: str = Path(..., min_length=16, max_length=16),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.conversation_id == conversation_id,
        ChatConversation.is_deleted == False
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在或已删除")
    return conv

# 3. 获取用户所有对话
@app.get("/api/conversations/{username}", response_model=List[ConversationResponse], summary="获取用户所有对话")
async def get_user_conversations(
    username: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    convs = db.query(ChatConversation).filter(
        ChatConversation.username == username,
        ChatConversation.is_deleted == False
    ).order_by(ChatConversation.update_time.desc()).all()
    return convs

# 4. 更新对话标题
@app.put("/api/conversation/{conversation_id}", response_model=ConversationResponse, summary="更新对话标题")
async def update_conversation(
    conversation_id: str = Path(..., min_length=16, max_length=16),
    conv_update: ConversationUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.conversation_id == conversation_id,
        ChatConversation.is_deleted == False
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在或已删除")
    # 更新标题（仅当传入标题时）
    if conv_update.title is not None:
        conv.title = conv_update.title
    db.commit()
    db.refresh(conv)
    return conv

# 5. 删除对话（软删除）
@app.delete("/api/conversation/{conversation_id}", summary="删除对话（软删除）")
async def delete_conversation(
    conversation_id: str = Path(..., min_length=16, max_length=16),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.conversation_id == conversation_id,
        ChatConversation.is_deleted == False
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在或已删除")
    # 软删除：标记is_deleted为True
    conv.is_deleted = True
    db.commit()
    return {"code": 200, "message": "对话删除成功"}

# -------------------------- 消息（ChatMessage）增删改查接口 --------------------------
# 1. 创建消息
@app.post("/api/message", response_model=MessageResponse, summary="发送新消息（仅存储）")
async def create_message(
    msg: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 校验对话是否存在
    conv = db.query(ChatConversation).filter(
        ChatConversation.conversation_id == msg.conversation_id,
        ChatConversation.is_deleted == False
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="关联的对话不存在或已删除")
    # 创建消息记录（无mode字段）
    db_msg = ChatMessage(
        conversation_id=msg.conversation_id,
        username=msg.username,
        role=msg.role,
        content=msg.content
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

# 2. 获取单个对话的所有消息
@app.get("/api/messages/{conversation_id}", response_model=List[MessageResponse], summary="获取对话的所有消息")
async def get_conversation_messages(
    conversation_id: str = Path(..., min_length=16, max_length=16),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # 校验对话是否存在
    conv = db.query(ChatConversation).filter(
        ChatConversation.conversation_id == conversation_id,
        ChatConversation.is_deleted == False
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在或已删除")
    # 查询消息（按发送时间升序）
    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.is_deleted == False
    ).order_by(ChatMessage.create_time.asc()).all()
    return messages

# 3. 删除消息（软删除）
@app.delete("/api/message/{message_id}", summary="删除消息（软删除）")
async def delete_message(
    message_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    msg = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.is_deleted == False
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在或已删除")
    # 软删除
    msg.is_deleted = True
    db.commit()
    return {"code": 200, "message": "消息删除成功"}

# -------------------------- 核心：模式化聊天接口（mode仅接口使用，不入库） --------------------------
@app.post("/api/chat", response_model=ChatResponse, summary="发送消息并获取模式化AI回复（核心接口）")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    前端核心调用接口：接收用户消息和模式，返回对应模式的AI回复
    （模式仅在接口层使用，不存储到数据库）
    """
    # 1. 校验对话是否存在
    conv = db.query(ChatConversation).filter(
        ChatConversation.conversation_id == request.conversation_id,
        ChatConversation.username == request.username,
        ChatConversation.is_deleted == False
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在或无权限访问")
    
    # 2. 存储用户消息（无mode字段）
    user_msg = ChatMessage(
        conversation_id=request.conversation_id,
        username=request.username,
        role="user",
        content=request.content  # 仅存储内容，不存mode
    )
    db.add(user_msg)
    
    # 3. 根据模式生成AI回复（接口层处理mode）
    ai_content = get_ai_response_by_mode(request.content, request.mode)
    
    # 4. 存储AI消息（无mode字段）
    ai_msg = ChatMessage(
        conversation_id=request.conversation_id,
        username=request.username,
        role="assistant",
        content=ai_content  # 仅存储回复内容，不存mode
    )
    db.add(ai_msg)
    
    # 5. 更新对话的更新时间
    conv.update_time = datetime.now()
    
    # 6. 提交数据库事务
    db.commit()
    
    # 7. 返回AI回复+模式（接口层返回mode，不入库）
    return ChatResponse(
        content=ai_content,
        mode=request.mode,  # 返回mode，但不存储
        conversation_id=request.conversation_id
    )

# -------------------------- 启动服务 --------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)