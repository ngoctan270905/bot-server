from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.exceptions import (
    UnauthorizedException, 
    BadRequestException, 
    ForbiddenException
)
from app.core.security import decode_token
from app.db.mongodb import get_database

# Repositories
from app.repositories.user_repository import UserRepository
from app.repositories.email_password_repository import EmailPasswordUserRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.billing_repository import BillingRepository
from app.repositories.bot_repository import BotRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.chat_history_repository import ChatHistoryRepository
from app.repositories.leads_repository import LeadsRepository
from app.repositories.chat_analytics_repository import ChatAnalyticsRepository

# Services
from app.services.auth_service import AuthService
from app.services.profile_service import ProfileService
from app.services.project_service import ProjectService
from app.services.bot_service import BotService
from app.services.chat_service import ChatService
from app.services.bot_analytics_service import BotAnalyticsService
from app.services.lead_service import LeadService

# Schemas
from app.schemas.user import UserDetailResponse

# Định nghĩa scheme xác thực OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# --- Repository Dependencies ---

async def get_user_repository(db = Depends(get_database)) -> UserRepository:
    """Dependency cung cấp UserRepository."""
    return UserRepository(collection=db["User"])

async def get_email_password_repository(db = Depends(get_database)) -> EmailPasswordUserRepository:
    """Dependency cung cấp EmailPasswordUserRepository."""
    return EmailPasswordUserRepository(collection=db["EmailPasswordUser"])

async def get_project_repository(db = Depends(get_database)) -> ProjectRepository:
    """Dependency cung cấp ProjectRepository."""
    return ProjectRepository(collection=db["Project"])

async def get_member_repository(db = Depends(get_database)) -> MemberRepository:
    """Dependency cung cấp MemberRepository."""
    return MemberRepository(collection=db["Member"])

async def get_billing_repository(db = Depends(get_database)) -> BillingRepository:
    """Dependency cung cấp BillingRepository."""
    return BillingRepository(collection=db["Billing"])

async def get_bot_repository(db = Depends(get_database)) -> BotRepository:
    """Dependency cung cấp BotRepository."""
    return BotRepository(collection=db["BotInstance"])

async def get_customer_repository(db = Depends(get_database)) -> CustomerRepository:
    """Dependency cung cấp CustomerRepository."""
    return CustomerRepository(collection=db["Customer"])

async def get_conversation_repository(db = Depends(get_database)) -> ConversationRepository:
    """Dependency cung cấp ConversationRepository."""
    return ConversationRepository(collection=db["Conversation"])

async def get_chat_history_repository(db = Depends(get_database)) -> ChatHistoryRepository:
    """Dependency cung cấp ChatHistoryRepository."""
    return ChatHistoryRepository(collection=db["ChatHistory"])

async def get_leads_repository(db = Depends(get_database)) -> LeadsRepository:
    """Dependency cung cấp LeadsRepository."""
    return LeadsRepository(collection=db["Leads"])

async def get_chat_analytics_repository(db = Depends(get_database)) -> ChatAnalyticsRepository:
    """Dependency cung cấp ChatAnalyticsRepository."""
    return ChatAnalyticsRepository(collection=db["ChatAnalytics"])

# --- Service Dependencies ---

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_pw_repo: EmailPasswordUserRepository = Depends(get_email_password_repository)
) -> AuthService:
    """Dependency cung cấp AuthService."""
    return AuthService(user_repository=user_repo, email_pw_repository=email_pw_repo)

async def get_profile_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_pw_repo: EmailPasswordUserRepository = Depends(get_email_password_repository)
) -> ProfileService:
    """Dependency cung cấp ProfileService."""
    return ProfileService(user_repository=user_repo, email_pw_repository=email_pw_repo)

async def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    member_repo: MemberRepository = Depends(get_member_repository),
    billing_repo: BillingRepository = Depends(get_billing_repository),
    bot_repo: BotRepository = Depends(get_bot_repository),
    chat_history_repo: ChatHistoryRepository = Depends(get_chat_history_repository)
) -> ProjectService:
    """Dependency cung cấp ProjectService."""
    return ProjectService(
        project_repo=project_repo,
        member_repo=member_repo,
        billing_repo=billing_repo,
        bot_repo=bot_repo,
        chat_history_repo=chat_history_repo
    )

async def get_bot_service(
    bot_repo: BotRepository = Depends(get_bot_repository),
    member_repo: MemberRepository = Depends(get_member_repository)
) -> BotService:
    """Dependency cung cấp BotService."""
    return BotService(bot_repo=bot_repo, member_repo=member_repo)

async def get_chat_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    chat_history_repo: ChatHistoryRepository = Depends(get_chat_history_repository),
    bot_repo: BotRepository = Depends(get_bot_repository)
) -> ChatService:
    """Dependency cung cấp ChatService."""
    return ChatService(
        customer_repo=customer_repo,
        conversation_repo=conversation_repo,
        chat_history_repo=chat_history_repo,
        bot_repo=bot_repo
    )

async def get_bot_analytics_service(
    analytics_repo: ChatAnalyticsRepository = Depends(get_chat_analytics_repository),
    bot_repo: BotRepository = Depends(get_bot_repository),
    member_repo: MemberRepository = Depends(get_member_repository),
    chat_history_repo: ChatHistoryRepository = Depends(get_chat_history_repository),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
) -> BotAnalyticsService:
    """Dependency cung cấp BotAnalyticsService."""
    return BotAnalyticsService(
        analytics_repo=analytics_repo,
        bot_repo=bot_repo,
        member_repo=member_repo,
        chat_history_repo=chat_history_repo,
        conversation_repo=conversation_repo
    )

async def get_lead_service(
    leads_repo: LeadsRepository = Depends(get_leads_repository),
    bot_repo: BotRepository = Depends(get_bot_repository),
    member_repo: MemberRepository = Depends(get_member_repository)
) -> LeadService:
    """Dependency cung cấp LeadService."""
    return LeadService(
        leads_repo=leads_repo,
        bot_repo=bot_repo,
        member_repo=member_repo
    )

# --- Auth Dependencies ---

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> UserDetailResponse:
    """
    Dependency lấy thông tin user hiện tại từ access token.
    Thực hiện truy vấn DB để đảm bảo user vẫn tồn tại và token là mới nhất.
    """
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user_repo = UserRepository(collection=db["User"])
    user_raw = await user_repo.get_user_by_id(user_id)

    if user_raw is None:
        raise UnauthorizedException(detail="Người dùng không tồn tại")

    # Cơ chế Single Session (giống dự án gốc)
    if user_raw.get("token") != token:
        raise UnauthorizedException(detail="Phiên đăng nhập đã hết hạn hoặc đã đăng nhập ở nơi khác")

    if not user_raw.get("active", True):
        raise BadRequestException(detail="Tài khoản đã bị vô hiệu hóa")

    return UserDetailResponse.model_validate(user_raw)
