from io import BytesIO

import httpx
import openai

from apps.accounts.schemas import Profile
from apps.bots import handlers
from server.config import Settings


def get_openai() -> openai.AsyncOpenAI:
    openai.api_key = Settings.OPENAI_API_KEY
    proxy_url = Settings.PROXY

    if proxy_url:
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        httpx.AsyncClient(proxies=proxies)
    else:
        httpx.AsyncClient()

        # client = openai.AsyncOpenAI(
        #     api_key=openai.api_key, http_client=http_client
        # )
        client = openai.AsyncOpenAI(
            # base_url="https://api.avalai.ir/v1", api_key=Settings.AVVALAI_API_KEY
            base_url="https://api.metisai.ir/openai/v1",
            api_key=Settings.METIS_API_KEY,
        )

    return client


def ai_response(
    *,
    message: str,
    profile: Profile,
    chat_id: str | None = None,
    response_id: str | None = None,
    inline_message_id: str | None = None,
    bot_name: str = "telegram",
    **kwargs: object,
) -> None:
    handlers.get_bot(bot_name)


async def stt_response(voice_bytes: BytesIO, **kwargs: object) -> str:
    client = get_openai()
    transcription = await client.audio.transcriptions.create(
        model="whisper-1", file=voice_bytes
    )
    return transcription.text


async def tts_response(text: str, **kwargs: object) -> BytesIO:
    client = get_openai()

    response = await client.audio.speech.create(
        model="tts-1", voice="alloy", input=text
    )

    buffer = BytesIO()
    for data in response.response.iter_bytes():
        buffer.write(data)
    buffer.seek(0)
    return buffer
