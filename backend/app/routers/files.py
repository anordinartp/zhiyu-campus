"""文件上传：聊天室发图片用。

只做最小实现：
  - 只允许图片（jpg/png/gif/webp）
  - 单文件不超过 5 MB
  - 存本地 uploads 目录，返回可访问的 URL
真实项目应换成对象存储（MinIO/OSS），接口形状不用变。
"""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile

from .. import errors
from ..deps import current_user

router = APIRouter(prefix="/api/v1/files", tags=["文件"])

# backend/uploads
UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}
MAX_BYTES = 5 * 1024 * 1024     # 5 MB


@router.post("")
async def upload(file: UploadFile = File(...), user: dict = Depends(current_user)):
    ctype = (file.content_type or "").lower()
    if ctype not in ALLOWED:
        raise errors.ApiError(
            errors.CODE_PARAM, "只支持 jpg / png / gif / webp 格式的图片")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise errors.ApiError(errors.CODE_PARAM, "图片不能超过 5 MB")
    if not data:
        raise errors.ApiError(errors.CODE_PARAM, "文件为空")

    name = f"{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:12]}{ALLOWED[ctype]}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as fh:
        fh.write(data)

    return errors.ok({
        "url": f"/uploads/{name}",
        "name": file.filename,
        "size": len(data),
    })
