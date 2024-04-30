import json
import logging
from datetime import timedelta, timezone, datetime
from typing import Union

from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlmodel import SQLModel, create_engine, Session, select

from ..api_tools.database import Token, TokenData, UserInDB
from ..api_tools.exceptions import Inactive_exception, Credentials_exception
from ..basic_configs import DB_PATH, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from ..tools.password import generate_password, verify_password, get_password_hash

# init OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# init FastAPI router
token_router = APIRouter(prefix="/api/token", tags=["OAuth2"])

# 创建数据库
ENGINE = create_engine(f'sqlite:///{DB_PATH}', echo=True)
SQLModel.metadata.create_all(ENGINE)


# 初始化数据库
def init_db():
    # 检查数据库内是否存在权限为admin的账户，如果不存在则创建
    with Session(ENGINE) as session:
        starts_with_t = select(UserInDB).where(UserInDB.role == "admin")
        result = session.exec(starts_with_t).first()
        if not result:
            admin_username = generate_password(5)
            admin_password = generate_password(16)
            print(f"""
---------------------------------------------
    正在初始化数据库，未找到管理员账户
    数据库路径: {DB_PATH}
    管理员账户: {admin_username}
    管理员密码: {admin_password}
    请牢记管理员账户及密码，数据库内未记录明文密码
    该信息已保存至./default_admin.json
---------------------------------------------
            """)

            # 使用json.dump写入到./default_admin.json
            with open("./default_admin.json", "w") as f:
                json.dump({"username": admin_username, "password": admin_password}, f, indent=4, ensure_ascii=False)

            admin = UserInDB(username=admin_username, role="admin", hashed_password=get_password_hash(admin_password))
            session.add(admin)
            session.commit()
            logging.info("Finish init db")
        else:
            logging.info("Database already initialized")


init_db()


def get_user(username: str) -> UserInDB | None:
    """从使用用户名从数据库中获取用户信息"""
    with Session(ENGINE) as session:
        starts_with_t = select(UserInDB).where(UserInDB.username == username)
        # 处理如果用户不存在
        return session.exec(starts_with_t).first()


def authenticate_user(username: str, password: str) -> Union[bool, UserInDB]:
    """验证用户名和密码"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = timedelta(minutes=30)) -> str:
    """创建access token, 默认过期时间为30分钟"""
    to_encode = data.copy()
    # 更新token的exp
    to_encode.update({"exp": datetime.now(timezone.utc) + expires_delta})
    # 生成token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """从jwt提取用户名，并获取当前用户信息"""
    try:
        # 解码token
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        if username is None:
            raise Credentials_exception
        token_data = TokenData(username=username)
    # token解码失败
    except JWTError:
        raise Credentials_exception
    # 获取用户信息
    user = get_user(username=token_data.username)
    if user is None:
        raise Credentials_exception
    return user


@token_router.post("", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """登录，获取access token"""
    # 验证用户
    user: Union[bool, UserInDB] = authenticate_user(form_data.username, form_data.password)
    # 用户不存在
    if not user:
        raise Credentials_exception
    # 用户被禁用
    if user.disabled:
        raise Inactive_exception
    # 创建token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return Token(access_token=access_token)
