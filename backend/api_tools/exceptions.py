from fastapi import HTTPException, status

# 用户被禁用
Inactive_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Inactive user"
)

# 用户名重复
Duplicate_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Username already exists"
)

# 用户权限不足
Permission_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Permission denied"
)

# JWT token错误
Credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"}
)

# 用户脸部图片格式错误
Unsupported_exception = HTTPException(
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    detail="Unsupported file type, only support jpeg or png"
)

# 未找到用户脸部图片
NotFound_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="image not found"
)
