# auth.py —— 登录认证相关：密码哈希 + 签发/校验 JWT
# 为什么单独一个文件：认证逻辑和业务接口分开，main.py 只负责"谁调用、调什么"
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()  # 从 .env 读 JWT_SECRET

SECRET_KEY = os.getenv("JWT_SECRET")   # JWT 签名密钥（敏感信息不放代码里）
ALGORITHM = "HS256"                    # 签名算法
TOKEN_EXPIRE_MINUTES = 60              # token 有效期 1 小时

if not SECRET_KEY:
    raise RuntimeError("缺少 JWT_SECRET，请在 .env 里配置")


# ---- 密码哈希：PBKDF2 + 随机盐，数据库里存 "盐$哈希"，不存明文 ----
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)  # 每个用户一把随机盐：即使两人密码一样，存进去的哈希也不同
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, expected = stored.split("$")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return secrets.compare_digest(dk.hex(), expected)  # 常量时间比较，防时序攻击


# ---- JWT 签发与校验 ----
def create_access_token(username: str, role: str) -> str:
    payload = {
        "sub": username,                        # sub = 主题，习惯上放用户名
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# 从请求头里取 Authorization: Bearer <token>
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """FastAPI 依赖：校验 token，通过才放行，失败抛 401"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录：请先 POST /auth/login 拿 token")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="token 无效")
    return payload  # 里面是 {"sub": 用户名, "role": 角色, "exp": 过期时间}
