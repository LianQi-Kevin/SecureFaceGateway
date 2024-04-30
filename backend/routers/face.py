import base64
import logging
import os.path

from deepface import DeepFace
from fastapi import APIRouter, UploadFile, File

from ..api_tools import FaceFindResponse, FaceFindPose
from ..basic_configs import FACE_FIND_MODEL_NAME, IMG_CACHE_PATH
from ..routers.user import get_user_by_userid

face_router = APIRouter(prefix="/api/face", tags=["Face"])

MODEL = DeepFace.build_model(FACE_FIND_MODEL_NAME)


@face_router.post("/detect")
async def detect_face(file: UploadFile = File(...), ) -> FaceFindResponse:
    # 校验图片格式
    if file.content_type != "image/jpeg":
        return FaceFindResponse(success=False, message="Unsupported file type, only supported image/jpeg",
                                username=file.filename, role="user", conf=0.0)
    # 转换为base64字串
    img_base64 = f"data:image/jpeg;base64,{base64.b64encode(file.file.read()).decode()}"
    # 调用DeepFace进行人脸验证
    results = DeepFace.find(
        img_path=img_base64,
        db_path=IMG_CACHE_PATH,
        model_name=FACE_FIND_MODEL_NAME,
        enforce_detection=False
    )

    # 提取identity和distance
    df = results[0]
    # 判断df非空
    if df.empty:
        return FaceFindResponse(success=False, message="Face not found")

    max_distance_row = df.loc[df['distance'].idxmax()]
    identity: str = max_distance_row['identity']
    distance: float = max_distance_row['distance']
    source_x: int = max_distance_row['source_x']
    source_y: int = max_distance_row['source_y']
    source_w: int = max_distance_row['source_w']
    source_h: int = max_distance_row['source_h']
    logging.info(f"face detected, identity: {identity}, distance: {distance}, "
                 f"source_x: {source_x}, source_y: {source_y}, source_w: {source_w}, source_h: {source_h}")

    if (1 - distance) < 0.3:
        return FaceFindResponse(success=False, message="Face not found")
    # 从identity中解析user_id
    user_id = os.path.splitext(os.path.basename(identity))[0]
    # 使用user_id查询用户信息
    logging.info(f"SQL searched, user_id: {user_id}, distance: {distance}")
    user = get_user_by_userid(user_id)
    return FaceFindResponse(success=True, message="success", username=user.username, role=user.role, conf=1 - distance,
                            pose=FaceFindPose(x=source_x, y=source_y, w=source_w, h=source_h))
