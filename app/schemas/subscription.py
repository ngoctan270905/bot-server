from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import List, Optional

class TokenSubscriptionPrice(BaseModel):
    currency: str
    price: int
    reccuring_interval: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TokenSubscriptionService(BaseModel):
    tokens_per_bot_per_month: int
    characters_per_bot: int
    team_members: int = 1

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TokenSubscription(BaseModel):
    id: str
    name: str
    description: str
    is_free: bool = False
    prices: List[TokenSubscriptionPrice]
    features: List[str]
    services: TokenSubscriptionService
    tax_code: Optional[str] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
