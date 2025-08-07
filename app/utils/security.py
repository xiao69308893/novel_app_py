# app/utils/security.py
# -*- coding: utf-8 -*-
"""
安全工具模块
提供密码加密、JWT token、权限验证等安全功能
"""

import hashlib
import secrets
import hmac
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

import bcrypt
import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet


class HashAlgorithm(Enum):
    """哈希算法"""
    BCRYPT = "bcrypt"
    PBKDF2 = "pbkdf2_sha256"
    ARGON2 = "argon2"


class TokenType(Enum):
    """Token类型"""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"


class PasswordManager:
    """密码管理器"""
    
    def __init__(self, algorithm: HashAlgorithm = HashAlgorithm.BCRYPT):
        self.algorithm = algorithm
        
        # 配置密码上下文
        schemes = []
        if algorithm == HashAlgorithm.BCRYPT:
            schemes = ["bcrypt"]
        elif algorithm == HashAlgorithm.PBKDF2:
            schemes = ["pbkdf2_sha256"]
        elif algorithm == HashAlgorithm.ARGON2:
            schemes = ["argon2"]
        
        self.pwd_context = CryptContext(
            schemes=schemes,
            deprecated="auto",
            bcrypt__rounds=12,
            pbkdf2_sha256__rounds=100000,
            argon2__memory_cost=65536,
            argon2__time_cost=3,
            argon2__parallelism=1
        )
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def needs_update(self, hashed_password: str) -> bool:
        """检查密码是否需要更新"""
        return self.pwd_context.needs_update(hashed_password)
    
    def generate_password(self, length: int = 12) -> str:
        """生成随机密码"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """检查密码强度"""
        import re
        
        score = 0
        feedback = []
        
        # 长度检查
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("密码长度至少8位")
        
        if len(password) >= 12:
            score += 1
        
        # 字符类型检查
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("需要包含小写字母")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("需要包含大写字母")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("需要包含数字")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("需要包含特殊字符")
        
        # 常见密码检查
        common_passwords = [
            "123456", "password", "123456789", "12345678",
            "12345", "1234567", "qwerty", "abc123"
        ]
        if password.lower() in common_passwords:
            score = max(0, score - 2)
            feedback.append("不能使用常见密码")
        
        # 强度等级
        if score >= 5:
            strength = "强"
        elif score >= 3:
            strength = "中"
        else:
            strength = "弱"
        
        return {
            "score": score,
            "max_score": 6,
            "strength": strength,
            "feedback": feedback
        }


class JWTManager:
    """JWT Token管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        
        # 默认过期时间
        self.token_expires = {
            TokenType.ACCESS: timedelta(hours=1),
            TokenType.REFRESH: timedelta(days=30),
            TokenType.RESET_PASSWORD: timedelta(hours=1),
            TokenType.EMAIL_VERIFICATION: timedelta(hours=24),
            TokenType.PHONE_VERIFICATION: timedelta(minutes=10)
        }
    
    def create_token(self, data: Dict[str, Any], token_type: TokenType,
                    expires_delta: Optional[timedelta] = None) -> str:
        """创建JWT token"""
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + self.token_expires[token_type]
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": token_type.value
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str, token_type: Optional[TokenType] = None) -> Dict[str, Any]:
        """解码JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 验证token类型
            if token_type and payload.get("type") != token_type.value:
                raise jwt.InvalidTokenError("Invalid token type")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token")
    
    def refresh_token(self, refresh_token: str) -> str:
        """刷新访问token"""
        payload = self.decode_token(refresh_token, TokenType.REFRESH)
        
        # 创建新的访问token
        new_payload = {
            "sub": payload["sub"],
            "user_id": payload.get("user_id"),
            "username": payload.get("username")
        }
        
        return self.create_token(new_payload, TokenType.ACCESS)
    
    def revoke_token(self, token: str) -> bool:
        """撤销token（需要配合黑名单实现）"""
        # 这里可以将token加入黑名单
        # 实际实现需要配合Redis或数据库
        return True


class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            key = Fernet.generate_key()
        self.cipher = Fernet(key)
        self.key = key
    
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """加密数据"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """解密数据"""
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode('utf-8')
    
    def encrypt_dict(self, data: Dict[str, Any]) -> bytes:
        """加密字典数据"""
        import json
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: bytes) -> Dict[str, Any]:
        """解密字典数据"""
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class SecurityValidator:
    """安全验证器"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        import re
        # 中国手机号格式
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, Any]:
        """验证用户名"""
        import re
        
        errors = []
        
        # 长度检查
        if len(username) < 3:
            errors.append("用户名长度至少3位")
        elif len(username) > 20:
            errors.append("用户名长度不能超过20位")
        
        # 字符检查
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', username):
            errors.append("用户名只能包含字母、数字、下划线和中文")
        
        # 开头检查
        if username[0].isdigit():
            errors.append("用户名不能以数字开头")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理输入内容"""
        import html
        import re
        
        # HTML转义
        text = html.escape(text)
        
        # 移除潜在的脚本标签
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除潜在的样式标签
        text = re.sub(r'<style.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """检查SQL注入"""
        import re
        
        # SQL注入关键词
        sql_keywords = [
            'select', 'insert', 'update', 'delete', 'drop', 'create',
            'alter', 'exec', 'execute', 'union', 'script', 'javascript'
        ]
        
        text_lower = text.lower()
        for keyword in sql_keywords:
            if keyword in text_lower:
                return True
        
        # 检查特殊字符组合
        patterns = [
            r"'.*'",  # 单引号包围
            r'".*"',  # 双引号包围
            r'--',    # SQL注释
            r'/\*.*\*/',  # 多行注释
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        return False


class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """检查是否允许请求"""
        now = datetime.now()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # 清理过期的请求记录
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        # 检查是否超过限制
        if len(self.requests[key]) >= max_requests:
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True
    
    def get_remaining_requests(self, key: str, max_requests: int, window_seconds: int) -> int:
        """获取剩余请求次数"""
        now = datetime.now()
        
        if key not in self.requests:
            return max_requests
        
        # 清理过期的请求记录
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff]
        
        return max(0, max_requests - len(self.requests[key]))


# 全局实例
password_manager = PasswordManager()
jwt_manager = JWTManager("your-secret-key")  # 实际使用时应从配置文件读取
encryption_manager = EncryptionManager()
rate_limiter = RateLimiter()


# 便捷函数
def hash_password(password: str) -> str:
    """哈希密码"""
    return password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return password_manager.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问token"""
    return jwt_manager.create_token(data, TokenType.ACCESS, expires_delta)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新token"""
    return jwt_manager.create_token(data, TokenType.REFRESH, expires_delta)


def decode_token(token: str, token_type: Optional[TokenType] = None) -> Dict[str, Any]:
    """解码token"""
    return jwt_manager.decode_token(token, token_type)


def generate_verification_code(length: int = 6) -> str:
    """生成验证码"""
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))


def generate_secure_token(length: int = 32) -> str:
    """生成安全token"""
    return secrets.token_urlsafe(length)


def calculate_hmac(data: str, key: str) -> str:
    """计算HMAC"""
    return hmac.new(
        key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def verify_hmac(data: str, key: str, signature: str) -> bool:
    """验证HMAC"""
    expected = calculate_hmac(data, key)
    return hmac.compare_digest(expected, signature)