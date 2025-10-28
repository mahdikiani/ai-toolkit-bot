from telebot import async_telebot
from usso import UserData

from apps.accounts.handlers import get_usso_user
from apps.bots import base_bot, schemas


class UserMiddleware(async_telebot.BaseMiddleware):
    def __init__(self, bot: base_bot.BaseBot, **kwargs: object) -> None:
        self.update_sensitive = True
        self.update_types = [
            "message",
            #  "edited_message",
            "callback_query",
            # "inline_query"
        ]
        self.bot = bot
        self.bot_type = bot.bot_type
        super().__init__(**kwargs)

    async def pre_process_message(
        self, message: async_telebot.types.Message, data: object
    ) -> None:
        messenger = self.bot_type
        from_user = message.from_user if message.from_user else message.chat
        if from_user.id == (await self.bot.get_me()).id:
            from_user = message.chat

        credentials = {
            "auth_method": messenger,
            "representor": f"{from_user.id}",
        }
        user: UserData = await get_usso_user(credentials)
        message_owned: schemas.MessageOwned = message  # type: ignore
        message_owned.user = user
        return

    async def pre_process_callback_query(
        self, call: async_telebot.types.CallbackQuery, data: object
    ) -> None:
        await self.pre_process_message(call.message, data)

    async def post_process_message(
        self,
        message: async_telebot.types.Message,
        data: object,
        exception: Exception | None,
    ) -> None:
        pass

    async def post_process_callback_query(
        self,
        call: async_telebot.types.CallbackQuery,
        data: object,
        exception: Exception | None,
    ) -> None:
        pass
