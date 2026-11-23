"""文件上传：头像、简历、课程图片、课时视频。

- 按文件头魔数判断真实类型，不信任扩展名和 Content-Type；
- 随机文件名，按 类型/年月 分目录；
- 头像、简历：登录用户；课程图片、视频：教师或管理员。
"""
from __future__ import annotations

import secrets
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from ..config import settings
from ..deps import get_current_user
from ..models import User
from ..utils import ok

router = APIRouter(prefix="/api/uploads", tags=["上传"])

_CHUNK = 1024 * 1024

# 魔数 -> 扩展名
_SIGNATURES: list[tuple[bytes, int, str]] = [
    (b"\x89PNG\r\n\x1a\n", 0, "png"),
    (b"\xff\xd8\xff", 0, "jpg"),
    (b"GIF87a", 0, "gif"),
    (b"GIF89a", 0, "gif"),
    (b"RIFF", 0, "riff"),  # webp 需再检查 8:12 == WEBP
    (b"%PDF-", 0, "pdf"),
    (b"PK\x03\x04", 0, "docx"),
    (b"ftyp", 4, "mp4"),
    (b"\x1a\x45\xdf\xa3", 0, "webm"),
]

_KINDS = {
    "avatar": {"exts": {"png", "jpg", "gif", "webp"}, "mb": lambda: settings.max_image_mb, "teacher": False},
    "resume": {"exts": {"pdf", "docx"}, "mb": lambda: settings.max_document_mb, "teacher": False},
    "image": {"exts": {"png", "jpg", "gif", "webp"}, "mb": lambda: settings.max_image_mb, "teacher": True},
    "video": {"exts": {"mp4", "webm"}, "mb": lambda: settings.max_video_mb, "teacher": True},
}


def sniff(head: bytes) -> str | None:
    for sig, offset, ext in _SIGNATURES:
        if head[offset:offset + len(sig)] == sig:
            if ext == "riff":
                return "webp" if head[8:12] == b"WEBP" else None
            return ext
    return None


@router.post("")
async def upload(
    kind: str = Query(..., description="avatar / resume / image / video"),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    rule = _KINDS.get(kind)
    if rule is None:
        raise HTTPException(400, "不支持的上传类型")
    if rule["teacher"] and user.role not in ("teacher", "admin"):
        raise HTTPException(403, "只有教师或管理员可以上传课程素材")
    head = await file.read(16)
    ext = sniff(head)
    if ext not in rule["exts"]:
        allowed = "、".join(sorted(rule["exts"])).upper()
        raise HTTPException(400, f"文件格式不支持，请上传 {allowed}")
    limit = rule["mb"]() * 1024 * 1024
    sub = Path(kind) / datetime.now().strftime("%Y%m")
    target_dir = Path(settings.upload_dir) / sub
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{secrets.token_hex(12)}.{ext}"
    target = target_dir / name
    size = len(head)
    try:
        with target.open("wb") as fh:
            fh.write(head)
            while chunk := await file.read(_CHUNK):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"文件不能超过 {rule['mb']()}MB")
                fh.write(chunk)
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    url = "/uploads/" + (sub / name).as_posix()
    return ok({"url": url, "size": size, "type": ext, "name": (file.filename or name)[:120]})
