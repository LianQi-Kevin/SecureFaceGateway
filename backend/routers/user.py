import glob
import logging
import os
from typing import Annotated, List, Sequence

from fastapi import APIRouter, Depends, File, UploadFile, Form, Path
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from .token import get_current_user, ENGINE
from ..api_tools.database import User, UserInDB
from ..api_tools.exceptions import Inactive_exception, Permission_exception, Unsupported_exception, Duplicate_exception, \
    NotFound_exception
from ..basic_configs import IMG_CACHE_PATH
from ..tools import get_password_hash, png_to_jpg

user_router = APIRouter(prefix="/api/user", tags=["User"])


def get_user_by_userid(user_id: str) -> UserInDB:
    """通过user_id获取用户信息"""
    with Session(ENGINE) as session:
        # 使用user_id搜索
        user = session.exec(select(UserInDB).where(UserInDB.user_id == user_id)).first()
        if not user:
            raise NotFound_exception
        return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前用户，要求用户未被禁用"""
    if current_user.disabled:
        raise Inactive_exception
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前用户，要求用户权限为admin"""
    if current_user.disabled or current_user.role != "admin":
        raise Permission_exception
    return current_user


def verify_username(username: str) -> bool:
    """校验用户名是否已被使用"""
    with Session(ENGINE) as session:
        result = session.exec(select(UserInDB).where(UserInDB.username == username)).first()
        logging.info(f"Verify username: {username}, result: {result}")
        if result:
            return True
        return False


@user_router.get("", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前用户信息"""
    return current_user


@user_router.post("", response_model=User)
async def create_user(
        username: str = Form(...), password: str = Form(...), role: str = Form(...),
        faceIMG: UploadFile = File(...), current_user: User = Depends(get_current_admin_user)) -> User:
    """创建用户"""
    logging.info(f"Start Create user: {username}, constraint by {current_user.username}")

    # 校验用户名是否已存在
    if verify_username(username):
        raise Duplicate_exception

    # 创建用户模型
    user = UserInDB(username=username, role=role, hashed_password=get_password_hash(password))

    # 校验上传的文件
    if faceIMG.content_type not in ["image/jpeg", "image/png"]:
        return Unsupported_exception

    # 保存文件
    if faceIMG.content_type != "image/jpeg":
        img_blob = png_to_jpg(faceIMG.file.read())
    else:
        img_blob = faceIMG.file.read()
    os.makedirs(IMG_CACHE_PATH, exist_ok=True)
    with open(f"{IMG_CACHE_PATH}/{user.user_id}.jpg", "wb") as f:
        f.write(img_blob)
    faceIMG.file.close()

    # 清理deepface使用的ckpl文件
    for filepath in glob.glob(os.path.join(IMG_CACHE_PATH, "*.pkl")):
        logging.debug(f"images path updated, clean deepface pkl file: {filepath}")
        os.remove(filepath)

    # 写数据库
    with Session(ENGINE) as session:
        session.add(user)
        session.commit()
        session.refresh(user)

        logging.info(f"Finish Create user: {username}")
        return user


@user_router.get("/all", response_model=List[User])
async def read_users(current_user: User = Depends(get_current_admin_user)) -> Sequence[UserInDB]:
    """获取所有用户信息"""
    logging.info(f"Read all users, constraint by {current_user.username}")
    with Session(ENGINE) as session:
        return session.exec(select(UserInDB)).all()


@user_router.delete("/{userID}", response_model=User)
async def delete_user(
        userID: Annotated[str, Path(title="USER_ID")],
        current_user: User = Depends(get_current_admin_user)) -> User:
    """删除用户"""
    logging.info(f"Delete user by id: {userID}, constraint by {current_user.username}")
    user = get_user_by_userid(userID)
    with Session(ENGINE) as session:
        session.delete(user)
        session.commit()
        session.flush()

    # 清理本地图片
    if os.path.exists(f"{IMG_CACHE_PATH}/{userID}.jpg"):
        os.remove(f"{IMG_CACHE_PATH}/{userID}.jpg")
    return user


@user_router.put("/{userID}", response_model=User)
async def update_user(
        userID: Annotated[str, Path(title="USER_ID")],
        username: str = Form(None), role: str = Form(None),
        faceIMG: UploadFile = File(None),
        current_user: User = Depends(get_current_admin_user)) -> User:
    """更新用户信息"""
    logging.info(f"Update user by id: {userID}, constraint by {current_user.username}")
    user = get_user_by_userid(userID)

    # 更新用户名
    if username:
        if verify_username(username):
            raise Duplicate_exception
        user.username = username

    # 更新权限组
    if role:
        user.role = role

    # 更新图片
    if faceIMG:
        if faceIMG.content_type not in ["image/jpeg", "image/png"]:
            return Unsupported_exception

        # 保存文件
        if faceIMG.content_type != "image/jpeg":
            img_blob = png_to_jpg(faceIMG.file.read())
        else:
            img_blob = faceIMG.file.read()
        os.makedirs(IMG_CACHE_PATH, exist_ok=True)
        with open(f"{IMG_CACHE_PATH}/{user.user_id}.jpg", "wb") as f:
            f.write(img_blob)
        faceIMG.file.close()

        # 清理deepface使用的ckpl文件
        for filepath in glob.glob(os.path.join(IMG_CACHE_PATH, "*.pkl")):
            logging.debug(f"images path updated, clean deepface pkl file: {filepath}")
            os.remove(filepath)

    # 写数据库
    with Session(ENGINE) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@user_router.put("/{userID}/password", response_model=User)
async def update_user_password(
        userID: Annotated[str, Path(title="USER_ID")],
        old_password: str = Form(...), new_password: str = Form(...),
        current_user: User = Depends(get_current_admin_user)) -> User:
    """更新用户密码"""
    logging.info(f"Update user password by id: {userID}, constraint by {current_user.username}")
    user = get_user_by_userid(userID)
    # 校验旧密码
    if not user.hashed_password == get_password_hash(old_password):
        raise Permission_exception
    # 更新密码
    user.hashed_password = get_password_hash(new_password)
    # 写数据库
    with Session(ENGINE) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@user_router.get("/faceImg", response_class=FileResponse)
async def get_face_img(current_user: User = Depends(get_current_active_user)):
    """获取当前用户的图片"""
    if not os.path.exists(f"{IMG_CACHE_PATH}/{current_user.user_id}.jpg"):
        raise NotFound_exception
    return FileResponse(path=f"{IMG_CACHE_PATH}/{current_user.user_id}.jpg")


@user_router.get("/faceImg/{userID}", response_class=FileResponse)
async def get_face_img_by_id(
        userID: Annotated[str, Path(title="USER_ID")],
        current_user: User = Depends(get_current_admin_user)):
    """通过user_id获取图片"""
    logging.info(f"Get face image by id: {userID}, constraint by {current_user.username}")
    if not os.path.exists(f"{IMG_CACHE_PATH}/{userID}.jpg"):
        raise NotFound_exception
    return FileResponse(path=f"{IMG_CACHE_PATH}/{userID}.jpg")
