# /control/agent_control.py
import pymysql, bcrypt, random, string
from fastapi import FastAPI, HTTPException, Depends, Header, Path, Body
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, CHAR, Index
from sqlalchemy.orm import Session
from typing import Optional, List

# 从配置文件导入依赖项
from config.agent_config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    SUPPORTED_MODES, engine, SessionLocal, Base, setup
)

# 初始化FastAPI应用
app = setup()

# ==================== 数据库模型定义 ====================
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

class ChatConversation(Base):
    __tablename__ = "chat_conversation"
    conversation_id = Column(CHAR(16), primary_key=True)
    username = Column(String(50), nullable=False)
    title = Column(String(100), default="")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)
    __table_args__ = (Index("idx_username", "username"),)

class ChatMessage(Base):
    __tablename__ = "chat_message"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(CHAR(16), nullable=False)
    username = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)
    __table_args__ = (Index("idx_conversation_id", "conversation_id"), Index("idx_create_time", "create_time"))

# 创建数据库表
Base.metadata.create_all(bind=engine)

# ==================== Pydantic 模型定义 ====================
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class ConversationCreate(BaseModel):
    username: str = Field(..., max_length=50)
    title: Optional[str] = Field("", max_length=100)

class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)

class ConversationResponse(BaseModel):
    conversation_id: str; username: str; title: str
    create_time: datetime; update_time: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    conversation_id: str = Field(..., min_length=16, max_length=16)
    username: str = Field(..., max_length=50)
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(...)

class MessageResponse(BaseModel):
    id: int; conversation_id: str; username: str; role: str; content: str; create_time: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    conversation_id: str = Field(..., min_length=16, max_length=16)
    username: str = Field(..., max_length=50)
    content: str = Field(...)
    mode: SUPPORTED_MODES = "自动"

class ChatResponse(BaseModel):
    content: str = Field(...); mode: SUPPORTED_MODES = Field(...); conversation_id: str = Field(...)

# ==================== 工具函数 ====================
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try: yield db
    finally: db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try: return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception: return False

def create_access_token(data: dict):
    """生成JWT令牌"""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(db: Session, email: str, password: str):
    """用户认证"""
    user = db.query(User).filter(User.email == email, User.status == 1).first()
    if not user or not verify_password(password, user.password): return False
    
    user_info = {"id": user.id, "username": user.username, "email": user.email,
                "role": user.role, "permissions": user.permissions.split(',') if user.permissions else []}
    
    user.last_login_at = datetime.now()
    db.commit()
    return user_info

def get_token_from_header(authorization: Optional[str] = Header(None)):
    """从请求头获取令牌"""
    if not authorization: raise HTTPException(status_code=401, detail="未提供令牌，请在请求头中添加 Authorization: Bearer <token>")
    parts = authorization.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise HTTPException(status_code=401, detail="令牌格式错误，正确格式：Authorization: Bearer <token>")
    return parts[1]

def get_current_user(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)):
    """获取当前登录用户"""
    credentials_exception = HTTPException(status_code=401, detail="令牌无效或已过期", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None: raise credentials_exception
    except JWTError: raise credentials_exception
    
    user = db.query(User).filter(User.email == email, User.status == 1).first()
    if not user: raise credentials_exception
    
    return {"id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "permissions": user.permissions.split(',') if user.permissions else []}

def generate_conversation_id() -> str:
    """生成16位对话ID"""
    return datetime.now().strftime("%Y%m%d") + ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))

def get_ai_response_by_mode(user_content: str, mode: SUPPORTED_MODES) -> str:
    """根据模式生成AI回复"""
    return {
        "自动": f"这是一条自动模式下的AI回复。你输入的内容是：{user_content}",
        "数据": f"这是一条数据模式下的AI回复。针对你输入的「{user_content}」，我会为你提供数据相关的分析和解答。",
        "配置": f"这是一条配置模式下的AI回复。针对你输入的「{user_content}」，我会为你提供系统配置相关的建议和指导。",
        "翻译": f"这是一条翻译模式下的AI回复。你输入的「{user_content}」的英文翻译是：{user_content} (Translation Mode Response)",
        "代码": f"这是一条代码模式下的AI回复。针对你输入的「{user_content}」，我会为你提供代码相关的实现方案和解释。"
    }[mode]

# ==================== 路由注册 ====================
@app.post("/login", response_model=Token)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user_info = authenticate_user(db, form_data.email, form_data.password)
    if not user_info: raise HTTPException(status_code=401, detail="邮箱/密码错误或用户已禁用", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_access_token({"sub": user_info["email"]}), "token_type": "bearer", "user_info": user_info}

@app.get("/api/user/info")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {"code": 200, "data": current_user}

def get_valid_conversation(db: Session, conversation_id: str):
    """获取有效的对话（未删除）"""
    conv = db.query(ChatConversation).filter(ChatConversation.conversation_id == conversation_id, ChatConversation.is_deleted == False).first()
    if not conv: raise HTTPException(status_code=404, detail="对话不存在或已删除")
    return conv

@app.post("/api/conversation", response_model=ConversationResponse, summary="创建新对话")
async def create_conversation(conv: ConversationCreate = Body(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    conv_id = generate_conversation_id()
    db_conv = ChatConversation(conversation_id=conv_id, username=conv.username, title=conv.title)
    db.add(db_conv); db.commit(); db.refresh(db_conv)
    return db_conv

@app.get("/api/conversation/{conversation_id}", response_model=ConversationResponse, summary="获取单个对话")
async def get_conversation(conversation_id: str = Path(..., min_length=16, max_length=16), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return get_valid_conversation(db, conversation_id)

@app.get("/api/conversations/{username}", response_model=List[ConversationResponse], summary="获取用户所有对话")
async def get_user_conversations(username: str = Path(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(ChatConversation).filter(ChatConversation.username == username, ChatConversation.is_deleted == False).order_by(ChatConversation.update_time.desc()).all()

@app.put("/api/conversation/{conversation_id}", response_model=ConversationResponse, summary="更新对话标题")
async def update_conversation(conversation_id: str = Path(..., min_length=16, max_length=16), conv_update: ConversationUpdate = Body(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    conv = get_valid_conversation(db, conversation_id)
    if conv_update.title is not None: conv.title = conv_update.title
    db.commit(); db.refresh(conv)
    return conv

@app.delete("/api/conversation/{conversation_id}", summary="删除对话（软删除）")
async def delete_conversation(conversation_id: str = Path(..., min_length=16, max_length=16), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    conv = get_valid_conversation(db, conversation_id)
    conv.is_deleted = True; db.commit()
    return {"code": 200, "message": "对话删除成功"}

@app.post("/api/message", response_model=MessageResponse, summary="发送新消息（仅存储）")
async def create_message(msg: MessageCreate = Body(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    get_valid_conversation(db, msg.conversation_id)
    db_msg = ChatMessage(conversation_id=msg.conversation_id, username=msg.username, role=msg.role, content=msg.content)
    db.add(db_msg); db.commit(); db.refresh(db_msg)
    return db_msg

@app.get("/api/messages/{conversation_id}", response_model=List[MessageResponse], summary="获取对话的所有消息")
async def get_conversation_messages(conversation_id: str = Path(..., min_length=16, max_length=16), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    get_valid_conversation(db, conversation_id)
    return db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation_id, ChatMessage.is_deleted == False).order_by(ChatMessage.create_time.asc()).all()

@app.delete("/api/message/{message_id}", summary="删除消息（软删除）")
async def delete_message(message_id: int = Path(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    msg = db.query(ChatMessage).filter(ChatMessage.id == message_id, ChatMessage.is_deleted == False).first()
    if not msg: raise HTTPException(status_code=404, detail="消息不存在或已删除")
    msg.is_deleted = True; db.commit()
    return {"code": 200, "message": "消息删除成功"}

@app.post("/api/chat", response_model=ChatResponse, summary="发送消息并获取模式化AI回复（核心接口）")
async def chat(request: ChatRequest = Body(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    conv = db.query(ChatConversation).filter(ChatConversation.conversation_id == request.conversation_id,
                                             ChatConversation.username == request.username,
                                             ChatConversation.is_deleted == False).first()
    if not conv: raise HTTPException(status_code=404, detail="对话不存在或无权限访问")
    
    # 存储用户消息和AI回复
    db.add(ChatMessage(conversation_id=request.conversation_id, username=request.username, role="user", content=request.content))
    ai_content = get_ai_response_by_mode(request.content, request.mode)
    db.add(ChatMessage(conversation_id=request.conversation_id, username=request.username, role="assistant", content=ai_content))
    
    # 更新对话时间
    conv.update_time = datetime.now()
    db.commit()
    
    return ChatResponse(content=ai_content, mode=request.mode, conversation_id=request.conversation_id)

# 暴露app实例供main.py使用
__all__ = ["app"]