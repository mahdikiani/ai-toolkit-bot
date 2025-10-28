import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aiocache import cached
from usso import UserData
from usso.session import AsyncUssoSession

from apps.accounts.schemas import Profile
from server.config import Settings


@asynccontextmanager
async def get_usso_session() -> AsyncGenerator[AsyncUssoSession]:
    async with AsyncUssoSession(
        usso_base_url=Settings.USSO_URL, api_key=Settings.API_KEY
    ) as session:
        yield session


@cached(ttl=60 * 60 * 24)
async def get_usso_user(credentials: dict) -> UserData:
    return
    async with get_usso_session() as session:
        u = await session.get_user_by_credentials(credentials)
        return u


@cached(ttl=60 * 60 * 24)
async def get_user_profile(user_id: str, **kwargs: object) -> Profile:
    return
    async with get_usso_session() as session:
        response = await session.get(
            f"{Settings.profile_service_url}/profiles/{user_id}", timeout=20
        )
        if response.status_code == 200:
            return Profile(**response.json())
        elif response.status_code >= 400 and response.status_code != 404:
            logging.error(response.text)
            response.raise_for_status()

        profile = await session.create_profile(user_id=user_id)
        return Profile(**profile)
