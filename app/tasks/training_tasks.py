import uuid
import os
from datetime import datetime, timezone
from typing import List
from app.db.mongodb import get_database
from app.services.ai.engine import ai_engine
from app.helper.document_processor import document_processor
from langchain_core.documents import Document
from langchain_community.vectorstores import Redis as RedisVectorStore
from loguru import logger
from bson import ObjectId

async def train_bot_task(ctx, bot_id: str, source_ids: List[str]):
    """
    Task xử lý ngầm để huấn luyện bot.
    1. Lấy dữ liệu từ các sources (MongoDB).
    2. Cắt nhỏ văn bản (1000/100).
    3. Lưu vào Redis Vector Store
    4. Cập nhật trạng thái và lưu lịch sử.
    """
    db = get_database()
    try:
        logger.bind(context="Training").info(f"Bắt đầu huấn luyện cho bot {bot_id} với {len(source_ids)} sources.")

        # 1. Lấy danh sách sources từ DB
        sources_cursor = db["BotDataSource"].find({"_id": {"$in": [ObjectId(id) for id in source_ids]}})
        sources = [s async for s in sources_cursor]

        if not sources:
            logger.bind(context="Training").warning(f"Không tìm thấy sources nào để train cho bot {bot_id}.")
            return

        all_docs = []
        total_chars = 0

        # 2. Xử lý từng loại source
        for source in sources:
            s_type = source["type"]
            s_docs = []

            if s_type == "Text":
                s_docs.append(Document(page_content=source["text"]))
            elif s_type == "Website":
                s_docs.append(Document(
                    page_content=source["text"],
                    metadata={"source": source.get("fetchedUrl")}
                ))
            elif s_type == "QA":
                q = source["qna"]["question"]
                a = source["qna"]["answer"]
                s_docs.append(Document(page_content=f"Question: {q}\nAnswer: {a}"))
            elif s_type == "File":
                file_path = source["filePath"]
                # Đảm bảo đường dẫn đầy đủ tới file trong thư mục static/uploads
                # Nếu filePath chưa có tiền tố, ta cần join với đường dẫn gốc của project
                full_path = file_path if os.path.isabs(file_path) else os.path.join(os.getcwd(), file_path)
                s_docs = await document_processor.load_file(full_path)

            all_docs.extend(s_docs)
            total_chars += source.get("numberOfCharacters", 0)

        if not all_docs:
            logger.bind(context="Training").warning(f"Không trích xuất được nội dung nào từ các sources của bot {bot_id}.")
            return

        # 3. Cắt nhỏ văn bản (Sử dụng cấu hình 1000/100 trong document_processor)
        chunks = document_processor.chunk_documents(all_docs)

        # 4. Lưu vào Redis thông qua LangChain
        embeddings = ai_engine.get_embeddings()

        # Xóa dữ liệu cũ của bot này trên Redis trước khi nạp mới
        try:
            # Kiểm tra và xóa index nếu tồn tại
            RedisVectorStore.drop_index(
                index_name=bot_id,
                delete_documents=True,
                redis_url=ai_engine.redis_url
            )
            logger.bind(context="Training").info(f"Đã xóa index cũ: {bot_id}")
        except Exception as e:
            # Nếu index chưa tồn tại thì bỏ qua
            logger.bind(context="Training").debug(f"Không thể xóa index (có thể chưa tồn tại): {e}")

        # Nạp dữ liệu mới vào Redis
        RedisVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=bot_id,
            redis_url=ai_engine.redis_url
        )

        # Invalidate cache trong AI Engine để lần hỏi tiếp theo sẽ load dữ liệu mới
        ai_engine.invalidate_vs_cache(bot_id)

        # 5. Cập nhật trạng thái Done và lưu History vào MongoDB
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

        logger.bind(context="Training").success(f"Huấn luyện thành công cho bot {bot_id}. Tổng số chunks: {len(chunks)}")

    except Exception as e:
        logger.bind(context="Training").error(f"Lỗi khi huấn luyện bot {bot_id}: {e}")
        # Cập nhật trạng thái Failed
        await db["BotDataSource"].update_many(
            {"_id": {"$in": [ObjectId(id) for id in source_ids]}},
            {"$set": {"trainingStatus": "Failed", "updatedAt": datetime.now(timezone.utc)}}
        )
