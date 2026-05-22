import os
import uuid
import aiofiles
from fastapi import UploadFile
from typing import List, Dict, Any
from app.core.config import settings
from app.helper.document_processor import document_processor
from app.core.exceptions import BadRequestException

class ResourceService:
    async def upload_bot_source(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """
        Xử lý upload nhiều file nguồn cho bot, đếm ký tự và trả về thông tin giống Node.js.
        """
        results = []
        
        # Đảm bảo thư mục upload tồn tại
        upload_dir = os.path.join(os.getcwd(), settings.UPLOADS_DIR)
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            # 1. Kiểm tra định dạng file
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".pdf", ".docx", ".txt"]:
                raise BadRequestException(detail=f"File type {ext} is not supported.")

            # 2. Tạo tên file duy nhất
            file_key = f"{uuid.uuid4()}-{file.filename}"
            absolute_path = os.path.join(upload_dir, file_key)
            relative_path = f"{settings.UPLOADS_DIR}/{file_key}"

            # 3. Lưu file vật lý
            async with aiofiles.open(absolute_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)

            # 4. Đếm số ký tự
            num_chars = await document_processor.count_characters(absolute_path)

            # 5. Xây dựng URL truy cập
            file_url = f"{settings.DOMAIN_URL}/static/uploads/{file_key}"

            results.append({
                "url": file_url,
                "name": file.filename,
                "filePath": relative_path,
                "numberOfCharacters": num_chars
            })

        return results
