import asyncio
import logging
import os
from io import BytesIO

import singleton
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException

from utils.texttools import split_text


class BaseBot(AsyncTeleBot):
    token = ""
    # bot_type = "telegram"
    me = ""
    webhook_route = ""

    @property
    def bot_type(self) -> str:
        return "bale" if len(self.token) == 51 else "telegram"

    @property
    def link(self) -> str:
        if self.bot_type == "telegram":
            base_link = "https://t.me"
        elif self.bot_type == "bale":
            base_link = "https://ble.ir"
        return f"{base_link}/{self.me}"

    def __init__(self, token: str | None = None, **kwargs: object) -> None:
        if token:
            self.token = token
        super().__init__(
            self.token,
            parse_mode="markdown",
            **kwargs,
        )
        self.lock = asyncio.Lock()

    def __str__(self) -> str:
        return self.link

    async def edit_message_text(
        self, text: str, *args: object, **kwargs: object
    ) -> None:
        try:
            await super().edit_message_text(text=text[:4096], **kwargs)
        except ApiTelegramException as e:
            if (
                "message is not modified:" in str(e)
                or "message text is empty" in str(e)
                or "MESSAGE_TOO_LONG" in str(e)
            ):
                logging.warning("edit_message_text error: %s", e)
            elif "can't parse entities" in str(e):
                kwargs["parse_mode"] = ""
                await self.edit_message_text(text, *args, **kwargs)
                logging.warning("edit_message_text error: %s", e)
            else:
                logging.exception("edit_message_text error")
                raise

    async def send_message(
        self, chat_id: int | str, text: str, *args: object, **kwargs: object
    ) -> None:
        try:
            messages = split_text(text)
            for msg in messages:
                sent = await super().send_message(chat_id, msg, *args, **kwargs)
        except ApiTelegramException as e:
            if "MESSAGE_TOO_LONG" in str(e):
                logging.warning("send_message error: %s", e)
            elif "can't parse entities" in str(e):
                kwargs["parse_mode"] = ""
                await self.send_message(chat_id, text, *args, **kwargs)
                logging.warning("send_message error: %s", e)
            else:
                logging.exception("send_message error")
                raise
        return sent

    async def get_file_telethon(self, chat_id: int, message_id: int) -> BytesIO:
        from telethon import TelegramClient

        async with self.lock:
            client = await TelegramClient(
                f"sessions/{self.me}",
                os.getenv("TELEGRAM_API_ID"),
                os.getenv("TELEGRAM_API_HASH"),
            ).start(bot_token=os.getenv("TELEGRAM_TOKEN"))
            # await client.start(bot_token=self.token)
            entity = await client.get_input_entity(chat_id)
            msg = await client.get_messages(entity, ids=message_id)
            if not msg:
                raise RuntimeError("Message not found or deleted.")

            return msg.media


class TelegramBot(BaseBot, metaclass=singleton.Singleton):
    token = os.getenv("TELEGRAM_TOKEN")
    bot_type = "telegram"
    me = "mdfier_bot"  # todo change the name
    webhook_route = "mdfier_bot"


# class BaleBot(BaseBot, metaclass=singleton.Singleton):
#     token = os.getenv("BALE_TOKEN")
#     bot_type = "bale"
#     me = "mdfier_bot"
#     webhook_route = "bale_mdfier_bot"
