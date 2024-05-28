import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, Form
from sqlmodel import SQLModel, create_engine, Session, select

from ..api_tools import User, TaskID_NotFound_exception
from ..routers.user import get_current_user, get_current_admin_user
from ..api_tools.database import leaveApplication
from ..basic_configs import DB_PATH

app_router = APIRouter(prefix="/api/app", tags=["Application"])

# 创建数据库,
ENGINE = create_engine(f'sqlite:///{DB_PATH}', echo=True)
SQLModel.metadata.create_all(ENGINE)


@app_router.post("/leave", summary="Leave application")
async def leave_application(task_id: str = Form(...), user_id: str = Form(...), reason: str = Form(...),
                            start_time: int = Form(...), end_time: int = Form(...),
                            current_user: User = Depends(get_current_user)):
    logging.debug(f"Leave application: {task_id}, {user_id}, {reason}, {start_time}, {end_time}")
    logging.debug(f"current_user: {current_user.user_id}")
    # create a new leave application
    with Session(ENGINE) as session:
        session.add(
            leaveApplication(
                task_id=task_id,
                user_id=user_id,
                reason=reason,
                start_time=datetime.utcfromtimestamp(start_time / 1000),
                end_time=datetime.utcfromtimestamp(end_time / 1000),
                status="pending",
            )
        )
        session.commit()
        session.flush()


@app_router.get("/leave", summary="Get leave application", response_model=List[leaveApplication])
async def get_leave_application(current_user: User = Depends(get_current_user)):
    """Get leave application"""
    logging.debug(f"Get leave application, current_user: {current_user.user_id}")
    with Session(ENGINE) as session:
        return session.exec(select(leaveApplication).where(leaveApplication.user_id == current_user.user_id)).all()


@app_router.get("/leave/all", summary="Get leave application", response_model=List[leaveApplication])
async def get_leave_application(current_user: User = Depends(get_current_admin_user)):
    """Create leave application"""
    logging.debug(f"Get leave application, current_user: {current_user.user_id}")
    with Session(ENGINE) as session:
        return session.exec(select(leaveApplication)).all()


@app_router.put("/leave", summary="Approve or reject leave application", response_model=leaveApplication)
async def approve_leave_application(task_id: str = Form(...), status: str = Form(...),
                                    current_user: User = Depends(get_current_admin_user)):
    """Approve or reject leave application"""
    logging.debug(f"Approve leave application: {task_id}, {status}")
    with Session(ENGINE) as session:
        leave_app = session.exec(select(leaveApplication).where(leaveApplication.task_id == task_id)).first()
        if not leave_app:
            raise TaskID_NotFound_exception
        leave_app.status = status
        leave_app.reply_manager = current_user.user_id
        session.commit()
        session.flush()
        return leave_app
