from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings
from loguru import logger

class MailerService:
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.sender = settings.SENDGRID_SENDER
        self.domain_url = settings.DOMAIN_URL

    async def send_forgot_password_email(self, email: str, new_password: str):
        """
        Gửi email thông báo mật khẩu mới cho người dùng
        """
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY chưa được cấu hình. Không thể gửi email.")
            return

        subject = "Thiết lập lại mật khẩu!"
        content = (
            f"Chào mừng bạn đến với hệ thống Chăm sóc khách hàng của chúng tôi!\n"
            f"Bạn đã được thiết lập lại mật khẩu cho {email}, vui lòng đăng nhập lại tại link: {self.domain_url}\n"
            f"Mật khẩu cấp lại: {new_password}"
        )

        message = Mail(
            from_email=self.sender,
            to_emails=email,
            subject=subject,
            plain_text_content=content
        )

        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            logger.info(f"Đã gửi email reset password tới {email}. Status code: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Lỗi khi gửi email qua SendGrid: {e}")
            return None

mailer_service = MailerService()
