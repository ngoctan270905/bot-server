import uuid
import os
from datetime import datetime, timezone
from typing import List
from app.db.mongodb import get_database
from app.services.ai_engine import ai_engine
from app.helper.document_processor import document_processor
from langchain_core.documents import Document
from loguru import logger

async def train_bot_task(ctx, bot_id: str, source_ids: List[str]):
    """
    Task xử lý ngầm để huấn luyện bot.
    1. Lấy dữ liệu từ các sources.
    2. Cắt nhỏ và Embedding.
    3. Lưu vào Qdrant.
    4. Cập nhật trạng thái và lưu lịch sử.
    """
    db = get_database()
    try:
        logger.bind(context="Training").info(f"Bắt đầu huấn luyện cho bot {bot_id} với {len(source_ids)} sources.")
        
        # 1. Lấy danh sách sources từ DB
        from bson import ObjectId
        sources_cursor = db["BotDataSource"].find({"_id": {"$in": [ObjectId(id) for id in source_ids]}})
        sources = [s async for s in sources_cursor]
        
        if not sources:
            logger.bind(context="Training").warning(f"Không tìm thấy sources nào để train cho bot {bot_id}.")
            return

        all_docs = []
        total_chars = 0
        
        # 2. Xử lý từng source
        for source in sources:
            s_type = source["type"]
            s_docs = []
            
            if s_type == "Text":
                s_docs.append(Document(page_content=source["text"]))
            elif s_type == "Website":
                s_docs.append(Document(page_content=source["text"], metadata={"source": source.get("fetchedUrl")}))
            elif s_type == "QA":
                q = source["qna"]["question"]
                a = source["qna"]["answer"]
                s_docs.append(Document(page_content=f"Question: {q}\nAnswer: {a}"))
            elif s_type == "File":
                file_path = source["filePath"]
                # Cần đảm bảo đường dẫn đúng (thường join với UPLOADS_DIR)
                # Giả sử filePath đã là đường dẫn tương đối từ project root hoặc uploads dir
                full_path = file_path # Cần check kỹ chỗ này
                s_docs = await document_processor.load_file(full_path)
            
            all_docs.extend(s_docs)
            total_chars += source.get("numberOfCharacters", 0)

        if not all_docs:
            logger.bind(context="Training").warning(f"Không trích xuất được nội dung nào từ các sources của bot {bot_id}.")
            return

        # 3. Cắt nhỏ văn bản
        chunks = document_processor.chunk_documents(all_docs)
        
        # 4. Embedding
        texts_to_embed = [chunk.page_content for chunk in chunks]
        # Batch embedding nếu quá nhiều (tùy API)
        embeddings = await ai_engine.get_embedding(texts_to_embed)
        
        # 5. Lưu vào Qdrant
        points = []
        for i, emb in enumerate(embeddings):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": emb,
                "payload": {
                    "botId": bot_id,
                    "text": chunks[i].page_content,
                    "metadata": chunks[i].metadata
                }
            })
            
        # Xóa dữ liệu cũ của bot này trước khi nạp mới (giống Node.js dropIndex)
        await ai_engine.delete_points_by_bot(bot_id)
        
        # Upsert points mới
        await ai_engine.upsert_points(points)

        # 6. Cập nhật trạng thái Done và lưu History
        await db["BotDataSource"].update_many(
            {"_id": {"$in": [ObjectId(id) for id in source_ids]}},
            {"$set": {"trainingStatus": "Done", "updatedAt": datetime.now(timezone.utc)}}
        )
        
        await db["TrainingHistory"].insert_one({
            "botId": bot_id,
            "sourcesIds": source_ids,
            "createdAt": datetime.now(timezone.utc)
        })
        
        await db["BotInstance"].update_one(
            {"_id": ObjectId(bot_id)},
            {"$set": {"characterUsage": total_chars}}
        )

        logger.bind(context="Training").success(f"Huấn luyện thành công cho bot {bot_id}. Tổng số chunks: {len(points)}")

    except Exception as e:
        logger.bind(context="Training").error(f"Lỗi khi huấn luyện bot {bot_id}: {e}")
        # Cập nhật trạng thái Failed
        from bson import ObjectId
        await db["BotDataSource"].update_many(
            {"_id": {"$in": [ObjectId(id) for id in source_ids]}},
            {"$set": {"trainingStatus": "Failed", "updatedAt": datetime.now(timezone.utc)}}
        )
