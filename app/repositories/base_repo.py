from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from datetime import datetime, timezone
from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection

class BaseRepository:
    """
    Base Repository cung cấp các thao tác CRUD cơ bản với MongoDB Async.
    Nguyên tắc:
    - Chỉ thao tác với Database.
    - Trả về dữ liệu thô (dict hoặc list[dict]).
    - Tự động convert ObjectId sang str.
    """

    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    def _format_id(self, data: Any) -> Any:
        """Helper để convert ObjectId sang str trong dict hoặc list."""
        if isinstance(data, list):
            for item in data:
                if "_id" in item:
                    item["_id"] = str(item["_id"])
            return data
        if isinstance(data, dict) and "_id" in data:
            data["_id"] = str(data["_id"])
        return data

    async def create(self, data: dict) -> dict:
        """Tạo mới bản ghi."""
        if "created_at" not in data:
            data["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in data:
            data["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        return data

    async def get_by_id(self, id: str) -> Optional[dict]:
        """Lấy bản ghi theo ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(id)})
            return self._format_id(doc) if doc else None
        except Exception:
            return None

    async def find_one(self, filter: dict) -> Optional[dict]:
        """Tìm một bản ghi theo điều kiện."""
        doc = await self.collection.find_one(filter)
        return self._format_id(doc) if doc else None

    async def find_many(
        self,
        filter: dict = {},
        sort: List[Tuple[str, int]] = [("_id", 1)],
        skip: int = 0,
        limit: int = 20,
        projection: Optional[dict] = None
    ) -> List[dict]:
        """Tìm nhiều bản ghi có phân trang và sắp xếp."""
        cursor = self.collection.find(filter, projection).sort(sort).skip(skip).limit(limit)
        items = [item async for item in cursor]
        return self._format_id(items)

    async def update(self, id: str, data: dict) -> Optional[dict]:
        """Cập nhật bản ghi."""
        data["updated_at"] = datetime.now(timezone.utc)
        # Loại bỏ _id nếu có để tránh lỗi MongoDB
        data.pop("_id", None)

        try:
            updated_doc = await self.collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": data},
                return_document=ReturnDocument.AFTER
            )
            return self._format_id(updated_doc) if updated_doc else None
        except Exception:
            return None

    async def delete(self, id: str) -> bool:
        """Xóa bản ghi."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def count_documents(self, filter: dict = {}) -> int:
        """Đếm số lượng bản ghi theo điều kiện."""
        return await self.collection.count_documents(filter)
