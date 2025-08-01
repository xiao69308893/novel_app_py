# app/core/security.py
# -*- coding: utf-8 -*-
"""
安全相关功能
处理密码加密、JWT token生成和验证等
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
import secrets
import hashlib
import hmac
from urllib.parse import quote_plus

from app.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
        subject: Union[str, Any],
        expires_delta: timedelta = None
) -> str:
    """
    创建访问token

    Args:
        subject: token主题（通常是用户ID）
        expires_delta: 过期时间间隔

    Returns:
        str: JWT访问token
    """

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(
        subject: Union[str, Any],
        expires_delta: timedelta = None
) -> str:
    """
    创建刷新token

    Args:
        subject: token主题（通常是用户ID）
        expires_delta: 过期时间间隔

    Returns:
        str: JWT刷新token
    """

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 验证结果
    """

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希密码
    """

    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """
    生成密码重置token

    Args:
        email: 用户邮箱

    Returns:
        str: 重置token
    """

    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expire = now + delta

    to_encode = {
        "exp": expire,
        "nbf": now,
        "sub": email,
        "type": "password_reset"
    }

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    验证密码重置token

    Args:
        token: 重置token

    Returns:
        Optional[str]: 用户邮箱，验证失败返回None
    """

    try:
        decoded_token = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if decoded_token.get("type") != "password_reset":
            return None

        email = decoded_token.get("sub")
        return email

    except jwt.JWTError:
        return None


def generate_api_key(user_id: str, prefix: str = "sk") -> str:
    """
    生成API密钥

    Args:
        user_id: 用户ID
        prefix: 密钥前缀

    Returns:
        str: API密钥
    """

    # 生成随机部分
    random_part = secrets.token_urlsafe(32)

    # 生成验证部分（基于用户ID的哈希）
    verification_part = hashlib.sha256(
        f"{user_id}{settings.SECRET_KEY}".encode()
    ).hexdigest()[:8]

    return f"{prefix}_{verification_part}_{random_part}"


def verify_api_key(api_key: str, user_id: str) -> bool:
    """
    验证API密钥

    Args:
        api_key: API密钥
        user_id: 用户ID

    Returns:
        bool: 验证结果
    """

    try:
        parts = api_key.split("_")
        if len(parts) != 3:
            return False

        _, verification_part, _ = parts

        expected_verification = hashlib.sha256(
            f"{user_id}{settings.SECRET_KEY}".encode()
        ).hexdigest()[:8]

        return hmac.compare_digest(verification_part, expected_verification)

    except Exception:
        return False


def generate_verification_code(length: int = 6) -> str:
    """
    生成验证码

    Args:
        length: 验证码长度

    Returns:
        str: 数字验证码
    """

    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def generate_secure_random_string(length: int = 32) -> str:
    """
    生成安全的随机字符串

    Args:
        length: 字符串长度

    Returns:
        str: 随机字符串
    """

    return secrets.token_urlsafe(length)


def hash_string(content: str, salt: str = None) -> str:
    """
    哈希字符串

    Args:
        content: 要哈希的内容
        salt: 盐值

    Returns:
        str: 哈希结果
    """

    if salt is None:
        salt = settings.SECRET_KEY

    return hashlib.sha256(f"{content}{salt}".encode()).hexdigest()


def create_signed_url(
        path: str,
        expires_in: int = 3600,
        additional_data: dict = None
) -> str:
    """
    创建签名URL

    Args:
        path: URL路径
        expires_in: 过期时间（秒）
        additional_data: 额外数据

    Returns:
        str: 签名URL
    """

    expire_time = int(datetime.utcnow().timestamp()) + expires_in

    # 构建要签名的数据
    sign_data = f"{path}:{expire_time}"
    if additional_data:
        sign_data += f":{additional_data}"

    # 生成签名
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        sign_data.encode(),
        hashlib.sha256
    ).hexdigest()

    # 构建URL参数
    params = f"expires={expire_time}&signature={signature}"
    if additional_data:
        for key, value in additional_data.items():
            params += f"&{key}={quote_plus(str(value))}"

    separator = "&" if "?" in path else "?"
    return f"{path}{separator}{params}"


def verify_signed_url(
        url: str,
        signature: str,
        expires: int,
        additional_data: dict = None
) -> bool:
    """
    验证签名URL

    Args:
        url: 原始URL路径
        signature: 签名
        expires: 过期时间戳
        additional_data: 额外数据

    Returns:
        bool: 验证结果
    """

    # 检查是否过期
    if datetime.utcnow().timestamp() > expires:
        return False

    # 重新生成签名用于比较
    sign_data = f"{url}:{expires}"
    if additional_data:
        sign_data += f":{additional_data}"

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        sign_data.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def sanitize_input(input_str: str) -> str:
    """
    输入数据净化（防XSS）

    Args:
        input_str: 输入字符串

    Returns:
        str: 净化后的字符串
    """

    # 基础的HTML标签转义
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
        '&': '&amp;'
    }

    for char, replacement in replacements.items():
        input_str = input_str.replace(char, replacement)

    return input_str


def mask_sensitive_data(data: str, mask_char: str = "*", show_last: int = 4) -> str:
    """
    脱敏敏感数据

    Args:
        data: 原始数据
        mask_char: 掩码字符
        show_last: 显示最后几位

    Returns:
        str: 脱敏后的数据
    """

    if len(data) <= show_last:
        return mask_char * len(data)

    return mask_char * (len(data) - show_last) + data[-show_last:]