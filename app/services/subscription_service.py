"""
Quản lý dữ liệu subscription/token package của hệ thống.

Bao gồm:
- Gói mặc định miễn phí
- Danh sách các gói subscription
- Hàm lấy thông tin subscription theo ID
"""

from typing import List, Optional

from app.schemas.subscription import (
    TokenSubscription,
    TokenSubscriptionService
)


"""
Gói subscription mặc định của hệ thống.

Được sử dụng khi:
- Project chưa có subscription
- Subscription ID không tồn tại
- Không truyền subscription ID
"""
DEFAULT_SUBSCRIPTION = TokenSubscription(
    id="package_starter",
    name="Starter",
    description="Starter package",
    is_free=True,
    services=TokenSubscriptionService(
        tokens_per_bot_per_month=10000,
        characters_per_bot=400000,
        team_members=1
    )
)


"""
Danh sách các gói subscription trả phí của hệ thống.
"""
TOKEN_SUBSCRIPTIONS = [
    TokenSubscription(
        id="package_basic",
        name="Basic",
        description="Basic package",
        services=TokenSubscriptionService(
            tokens_per_bot_per_month=100000,
            characters_per_bot=10000000,
            team_members=3
        )
    ),
    TokenSubscription(
        id="package_pro",
        name="Pro",
        description="Pro package",
        services=TokenSubscriptionService(
            tokens_per_bot_per_month=300000,
            characters_per_bot=20000000,
            team_members=5
        )
    ),
    TokenSubscription(
        id="package_enterprise",
        name="Enterprise",
        description="Enterprise package",
        services=TokenSubscriptionService(
            tokens_per_bot_per_month=1000000,
            characters_per_bot=50000000,
            team_members=10
        )
    ),
    TokenSubscription(
        id="package_developer",
        name="Developer",
        description="Developer package",
        services=TokenSubscriptionService(
            tokens_per_bot_per_month=9999999999,
            characters_per_bot=9999999999,
            team_members=99999999
        )
    )
]


def get_subscription_by_id(
    subscription_id: Optional[str] = None
) -> TokenSubscription:
    """
    Lấy thông tin subscription theo ID.

    Args:
        subscription_id:
            ID của gói subscription.

    Returns:
        TokenSubscription:
            Thông tin subscription tương ứng.

    Notes:
        - Nếu không truyền subscription_id,
          trả về gói mặc định.
        - Nếu không tìm thấy subscription,
          trả về gói mặc định.
    """

    if not subscription_id:
        return DEFAULT_SUBSCRIPTION

    for subscription in TOKEN_SUBSCRIPTIONS:

        if subscription.id == subscription_id:
            return subscription

    return DEFAULT_SUBSCRIPTION