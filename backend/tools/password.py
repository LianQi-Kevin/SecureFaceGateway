import base64
import hashlib
import random
import string

from bcrypt import hashpw, checkpw, gensalt


def generate_password(n: int = 16) -> str:
    """创建长度为n的密码, 返回明文"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码和哈希密码是否匹配

    :param plain_password: 明文密码, 从API请求中获取
    :param hashed_password: 哈希密码, 从数据库中获取
    """
    return checkpw(
        # 使用b64+sha256防止过长密码
        password=base64.b64encode(hashlib.sha256(plain_password.encode('utf-8')).digest()),
        hashed_password=hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """获取密码hash"""
    return hashpw(
        # 使用b64+sha256防止过长密码
        password=base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest()),
        salt=gensalt(12)
    ).decode("utf-8")
