from app.repositories.user_repository import UserRepository
from app.repositories.email_password_repository import EmailPasswordUserRepository
from app.schemas.user import UserDetailResponse, UserUpdate
from app.schemas.base import UnifiedResponse
from app.core.exceptions import NotFoundException

class ProfileService:
    """
    Service xử lý logic liên quan đến hồ sơ người dùng.
    """
    def __init__(
        self, 
        user_repository: UserRepository,
        email_pw_repository: EmailPasswordUserRepository
    ):
        self._user_repo = user_repository
        self._email_pw_repo = email_pw_repository

    async def get_my_profile(self, user_id: str) -> UserDetailResponse:
        """
        Lấy thông tin cá nhân (me).
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="Profile not found.")
        
        # Lấy thêm thông tin email_pw để trả về (đồng bộ với schema)
        email_pw = await self._email_pw_repo.find_one({"userId": user_id})
        if email_pw:
            user["emailPw"] = email_pw
            
        return UserDetailResponse.model_validate(user)

    async def get_profile_by_id(self, id: str) -> UserDetailResponse:
        """
        Lấy thông tin cá nhân theo ID.
        """
        user = await self._user_repo.get_by_id(id)
        if not user:
            raise NotFoundException(detail="Profile not found.")

        # Lấy thêm thông tin email_pw để trả về
        email_pw = await self._email_pw_repo.find_one({"userId": id})
        if email_pw:
            user["emailPw"] = email_pw

        return UserDetailResponse.model_validate(user)

    async def update_profile(self, user_id: str, profile_in: UserUpdate) -> UserDetailResponse:
        """
        Cập nhật thông tin cá nhân.
        """
        update_data = profile_in.model_dump(exclude_unset=True)

        updated_user = await self._user_repo.update(user_id, update_data)
        if not updated_user:
            raise NotFoundException(detail="Profile not found.")

        # Lấy lại đầy đủ thông tin sau khi update
        email_pw = await self._email_pw_repo.find_one({"userId": user_id})
        if email_pw:
            updated_user["emailPw"] = email_pw

        return UserDetailResponse.model_validate(updated_user)
