from datetime import datetime, timezone
from typing import List, Optional
from app.repositories.bot_source_repository import BotDataSourceRepository
from app.repositories.bot_repository import BotRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.training_history_repository import TrainingHistoryRepository
from app.repositories.member_repository import MemberRepository
from app.schemas.source import (
    SourceUpsertRequest,
    SourceResponse,
    TrainingHistoryResponse,
    DataSourceType,
    TrainingStatus
)
from app.services.subscription_service import get_subscription_by_id
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.db.redis import redis_manager, get_arq_pool
from app.core.config import settings

class BotSourceService:
    def __init__(
        self,
        source_repo: BotDataSourceRepository,
        bot_repo: BotRepository,
        project_repo: ProjectRepository,
        training_repo: TrainingHistoryRepository,
        member_repo: MemberRepository
    ):
        self._source_repo = source_repo
        self._bot_repo = bot_repo
        self._project_repo = project_repo
        self._training_repo = training_repo
        self._member_repo = member_repo

    async def get_bot_sources(self, user_id: str, bot_id: str) -> List[SourceResponse]:
        """Lấy danh sách nguồn dữ liệu của bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You do not have permission to view this bot's sources")

        sources = await self._source_repo.get_by_bot(bot_id)
        response_sources = []

        for source in sources:
          validated_source = SourceResponse.model_validate(source)
          response_sources.append(validated_source)

        return response_sources

    async def upsert_sources(self, user_id: str, request: SourceUpsertRequest):
        """
        Cập nhật hoặc thêm mới các nguồn dữ liệu cho bot.
        """
        bot_id = request.bot_id
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # 1. Kiểm tra quyền
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not authorized to update this bot")

        # 2. Kiểm tra giới hạn ký tự (Subscription)
        project = await self._project_repo.get_by_id(bot["projectId"])
        subscription = get_subscription_by_id(project.get("subscriptionId"))
        char_limit = subscription.services.characters_per_bot

        # Tính toán số ký tự hiện tại và mới
        existing_sources = await self._source_repo.get_by_ids(request.existing_source_ids)
        current_characters = 0

        for source in existing_sources:
          number_of_characters = source.get(
            "numberOfCharacters",
            0
          )
          current_characters = current_characters + number_of_characters

        new_chars = 0
        new_sources_data = []

        # Xử lý Text
        for text in request.texts:
            count = len(text)
            new_chars += count
            new_sources_data.append({
                "type": DataSourceType.TEXT,
                "name": "Text",
                "botId": bot_id,
                "text": text,
                "numberOfCharacters": count,
                "trainingStatus": TrainingStatus.TRAINING
            })

        # Xử lý Website
        for url_in in request.fetched_urls:
            count = len(url_in.content) + len(url_in.title)
            new_chars += count
            new_sources_data.append({
                "type": DataSourceType.WEBSITE,
                "name": url_in.url,
                "botId": bot_id,
                "fetchedUrl": url_in.url,
                "text": f"{url_in.title} - {url_in.content}",
                "numberOfCharacters": count,
                "trainingStatus": TrainingStatus.TRAINING
            })

        # Xử lý File
        for file_in in request.files:
            new_chars += file_in.number_of_characters
            new_sources_data.append({
                "type": DataSourceType.FILE,
                "name": file_in.name,
                "botId": bot_id,
                "filePath": file_in.file_path,
                "numberOfCharacters": file_in.number_of_characters,
                "trainingStatus": TrainingStatus.TRAINING
            })

        # Xử lý QA
        for qa in request.qnas:
            count = len(qa.question) + len(qa.answer)
            new_chars += count
            new_sources_data.append({
                "type": DataSourceType.QA,
                "name": qa.question,
                "botId": bot_id,
                "qna": qa.model_dump(),
                "numberOfCharacters": count,
                "trainingStatus": TrainingStatus.TRAINING
            })

        # Xử lý Notion
        for notion in request.notions:
            new_chars += notion.number_of_characters
            new_sources_data.append({
                "type": DataSourceType.NOTION,
                "name": notion.name,
                "botId": bot_id,
                "notion": {
                    "id": notion.page_id,
                    "token": notion.token,
                    "type": "page"
                },
                "numberOfCharacters": notion.number_of_characters,
                "trainingStatus": TrainingStatus.TRAINING
            })

        total_chars = current_characters + new_chars
        if total_chars > char_limit:
            raise BadRequestException(
                detail=f"Total characters exceed the limit. Total: {total_chars}, Limit: {char_limit}."
            )

        # 3. Lưu vào DB và kích hoạt Training
        created_sources = []
        for data in new_sources_data:
            data["createdAt"] = datetime.now(timezone.utc)
            data["updatedAt"] = datetime.now(timezone.utc)
            s = await self._source_repo.create(data)
            created_sources.append(s)

        # IDs cần train = IDs cũ giữ lại + IDs mới tạo
        sources_to_train_ids = []

        # Thêm source cũ
        for existing_id in request.existing_source_ids:
          sources_to_train_ids.append(existing_id)

        # Thêm source mới
        for source in created_sources:
          source_id = str(source["_id"])
          sources_to_train_ids.append(source_id)

        # Đẩy vào Queue Training
        await self._enqueue_training_job(bot_id, sources_to_train_ids)

        return {"message": "Sources upserted successfully and training started."}

    async def delete_source(self, user_id: str, source_id: str):
        """Xóa một nguồn dữ liệu."""
        source = await self._source_repo.get_by_id(source_id)
        if not source:
            raise NotFoundException(detail="Source not found")

        bot = await self._bot_repo.get_by_id(source["botId"])
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not authorized to delete this source")

        await self._source_repo.delete(source_id)
        return {"message": "Source deleted successfully"}

    async def trigger_training(self, user_id: str, bot_id: str):
        """Kích hoạt lại quá trình training cho bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not authorized to train this bot")

        sources = await self._source_repo.get_by_bot(bot_id)
        source_ids = [str(s["_id"]) for s in sources]

        if not source_ids:
            raise BadRequestException(detail="No sources to train")

        await self._enqueue_training_job(bot_id, source_ids)
        return {"message": "Training started successfully"}

    async def get_training_history(self, user_id: str, bot_id: str) -> List[TrainingHistoryResponse]:
        """Lấy lịch sử training."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not authorized to view this bot's training history")

        history = await self._training_repo.get_by_bot(bot_id)
        return [TrainingHistoryResponse.model_validate(h) for h in history]

    async def _enqueue_training_job(self, bot_id: str, source_ids: List[str]):
        """Đẩy job trainBot vào Arq."""
        try:
            # Sử dụng pool có sẵn từ app.state (thông qua helper)
            arq_pool = get_arq_pool()
            await arq_pool.enqueue_job('train_bot_task', bot_id, source_ids)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to enqueue train_bot_task: {e}")
