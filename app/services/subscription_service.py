import json
import os
from typing import List, Optional
from app.schemas.subscription import TokenSubscription

class SubscriptionService:
    def __init__(self):
        # Đường dẫn tới file JSON chứa dữ liệu gói cước
        self._data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "datas", 
            "subscriptions.json"
        )
        self.default_subscription = None
        self.paid_subscriptions = []
        self._load_data()

    def _load_data(self):
        """Load dữ liệu từ file JSON vào memory"""
        if not os.path.exists(self._data_path):
            # Fallback nếu không tìm thấy file
            from app.schemas.subscription import TokenSubscriptionService
            self.default_subscription = TokenSubscription(
                id="package_starter",
                name="Starter",
                description="Starter package",
                is_free=True,
                prices=[],
                features=[],
                services=TokenSubscriptionService(
                    tokens_per_bot_per_month=10000,
                    characters_per_bot=400000,
                    team_members=1
                )
            )
            self.paid_subscriptions = []
            return

        with open(self._data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.default_subscription = TokenSubscription(**data["default"])
            self.default_subscription.is_free = True
            self.paid_subscriptions = [
                TokenSubscription(**item) for item in data["paid"]
            ]

    def get_subscriptions(self) -> List[TokenSubscription]:
        """Lấy tất cả các gói subscription (Free + Paid)"""
        return [self.default_subscription] + self.paid_subscriptions

    def get_subscription_by_id(
        self, 
        subscription_id: Optional[str] = None
    ) -> TokenSubscription:
        """Lấy thông tin subscription theo ID"""
        if not subscription_id or subscription_id == self.default_subscription.id:
            return self.default_subscription
        
        for sub in self.paid_subscriptions:
            if sub.id == subscription_id:
                return sub
        
        return self.default_subscription

# Global instance để sử dụng trong app
_service = SubscriptionService()

async def get_subscription_by_id(
    subscription_id: Optional[str] = None
) -> TokenSubscription:
    """Hàm helper async để lấy subscription (tương thích với code cũ)"""
    return _service.get_subscription_by_id(subscription_id)

async def get_all_subscriptions() -> List[TokenSubscription]:
    """Hàm helper async để lấy tất cả gói cước"""
    return _service.get_subscriptions()
