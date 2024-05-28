from typing import Optional, Union
from uuid import uuid4
from datetime import datetime

from pydantic import BaseModel, Field
from sqlmodel import Field as sql_Field
from sqlmodel import SQLModel


# sqlmodel 数据库表
class User(SQLModel):
    """用户基础结构"""
    id: Optional[int] = sql_Field(primary_key=True, default=None, index=True)
    username: str = sql_Field(index=True, unique=True)
    role: str = sql_Field(default="user", description="权限组 (user/admin)")
    user_id: str = sql_Field(default_factory=lambda: uuid4().hex, description="用户ID", index=True)
    disabled: Optional[bool] = sql_Field(default=False, description="是否禁用用户")


class UserInDB(User, table=True):
    """数据库表"""
    hashed_password: str = sql_Field(default=None)


class leaveApplication(SQLModel, table=True):
    """请假申请"""
    task_id: str = sql_Field(primary_key=True, index=True, description="任务ID")
    user_id: str = sql_Field(index=True, description="用户ID")
    reason: str = sql_Field(description="请假原因")
    create_time: datetime = sql_Field(description="申请创建时间", default_factory=lambda: datetime.now())
    start_time: datetime = sql_Field(description="请假开始时间")
    end_time: datetime = sql_Field(description="请假结束时间")
    status: str = sql_Field(default="pending", description="申请状态, ['pending', 'approved', 'rejected']")
    reply_manager: Optional[str] = sql_Field(description="审批人", default="None")


class userInfoChange(BaseModel):
    """用户信息修改"""
    username: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None
    disabled: Optional[bool] = None


# FastAPI response
class Token(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")


# JWT解码后
class TokenData(BaseModel):
    username: Union[str, None] = None


# face_router Return
class FaceFindPose(BaseModel):
    """人脸位置"""
    x: int
    y: int
    w: int
    h: int


class FaceFindResponse(BaseModel):
    """人脸识别返回"""
    success: bool
    message: str
    username: Optional[str] = None
    role: Optional[str] = None
    conf: Optional[float] = None
    pose: Optional[FaceFindPose] = None
