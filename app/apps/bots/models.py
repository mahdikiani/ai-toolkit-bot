from fastapi_mongo_base.models import UserOwnedEntity


class Message(UserOwnedEntity):
    content: str = ""
