# /config/agent_config.py
from fastapi import FastAPI
from datetime import timedelta
from typing import Literal
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.middleware.cors import CORSMiddleware

# ==================== 基础配置 ====================
# 数据库配置
MYSQL_URL = "mysql+pymysql://root:123456@192.168.100.128:3306/agent?charset=utf8mb4"

# JWT 配置
SECRET_KEY = "your-secret-key-keep-it-safe-123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7天

# CORS 配置
CORS_ORIGINS = ["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# 业务配置
SUPPORTED_MODES = Literal["自动", "数据", "配置", "翻译", "代码"]
CONVERSATION_ID_LENGTH = 16  # 对话ID长度
USERNAME_MAX_LENGTH = 50     # 用户名最大长度
TITLE_MAX_LENGTH = 100       # 标题最大长度

# ==================== 初始化配置 ====================
# 数据库连接配置
engine = create_engine(MYSQL_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def setup():
    app = FastAPI()
    """配置CORS中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS
    )
    return app

    