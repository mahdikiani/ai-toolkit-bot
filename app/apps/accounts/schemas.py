import uuid

from fastapi_mongo_base.schemas import UserOwnedEntitySchema
from pydantic import BaseModel


class ProfileData(BaseModel):
    pass


class Profile(UserOwnedEntitySchema):
    profile_data: ProfileData = ProfileData()


class ProfileCreate(BaseModel):
    user_id: uuid.UUID
    profile_data: ProfileData = ProfileData()
