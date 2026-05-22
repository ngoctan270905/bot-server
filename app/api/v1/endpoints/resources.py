from fastapi import APIRouter, Depends, UploadFile, File
from typing import List, Any
from app.services.resource_service import ResourceService
from app.api.v1.dependencies import get_resource_service, get_current_user
from app.schemas.user import UserDetailResponse

router = APIRouter()

@router.post("/bot-source", status_code=200)
async def upload_bot_source(
    files: List[UploadFile] = File(...),
    current_user: UserDetailResponse = Depends(get_current_user),
    resource_service: ResourceService = Depends(get_resource_service)
) -> Any:
    """
    Upload file nguồn cho bot (PDF, Docx, Txt).
    Server sẽ lưu file và trả về số lượng ký tự để Frontend gọi tiếp API upsert.
    """
    return await resource_service.upload_bot_source(files)
