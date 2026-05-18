from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class TokenSubscriptionService(BaseModel):
    tokens_per_bot_per_month: int
    characters_per_bot: int
    team_members: int
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TokenSubscription(BaseModel):
    id: str
    name: str
    description: str
    is_free: bool = False
    services: TokenSubscriptionService
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
