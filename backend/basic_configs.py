# Deepface configs
FACE_FIND_MODEL_NAME = "VGG-Face"
IMG_CACHE_PATH = "./cache_images"

# JWT OAuth2 Configs
DB_PATH = "./account.db"  # 数据库路径
SECRET_KEY = "e6c7d0d0f6a3b0b0b6c3c2f3a3b0b0b0"  # JWT签名密钥
ALGORITHM = "HS256"  # JWT签名算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # access-token过期分钟数
