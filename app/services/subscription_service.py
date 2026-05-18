from typing import List, Optional
from app.schemas.subscription import TokenSubscription, TokenSubscriptionService

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

def get_subscription_by_id(subscription_id: Optional[str] = None) -> TokenSubscription:
    if not subscription_id:
        return DEFAULT_SUBSCRIPTION
    
    for sub in TOKEN_SUBSCRIPTIONS:
        if sub.id == subscription_id:
            return sub
            
    return DEFAULT_SUBSCRIPTION
