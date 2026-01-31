import logging

import singleton
from fastapi_mongo_base.utils import basic
from telebot import async_telebot

from apps.bots import base_bot, middlewares
from server.config import Settings

from .bot_actions import callback, inline_query, inline_query_ai, message


def get_bot(bot_name: str) -> base_bot.BaseBot:
    for bot_cls in basic.get_all_subclasses(base_bot.BaseBot):
        bot: base_bot.BaseBot = bot_cls()
        if bot.me == bot_name:
            return bot
    else:
        logging.error("base_bot not found by name: %s", bot_name)
        raise ValueError("base_bot not found by name")


def get_bot_by_route(bot_route: str) -> base_bot.BaseBot:
    for bot_cls in basic.get_all_subclasses(base_bot.BaseBot):
        bot: base_bot.BaseBot = bot_cls()
        if bot.webhook_route == bot_route:
            return bot
    else:
        logging.error("base_bot not found by route: %s", bot_route)
        raise ValueError("base_bot not found by route")


class BotHandler(metaclass=singleton.Singleton):
    is_setup = False

    # def __init__(self):
    #     asyncio.run(self.setup())

    async def setup(self) -> None:
        if self.is_setup:
            return

        for bot_cls in basic.get_all_subclasses(base_bot.BaseBot):
            bot: base_bot.BaseBot = bot_cls()

            await self.setup_webhook(bot)
            await self.setup_bot(bot)

        self.is_setup = True

    async def setup_webhook(self, bot: base_bot.BaseBot) -> None:
        from apps.bots import routes

        reverse_url = routes.router.url_path_for("bot_update", bot=bot.webhook_route)
        webhook_url = f"https://{Settings.root_url}{Settings.base_path}{reverse_url}"
        if (await bot.get_webhook_info()).url != webhook_url:
            logging.info("set webhook for %s with url: %s", bot, webhook_url)
            await bot.delete_webhook()
            res = await bot.set_webhook(url=webhook_url, timeout=10)
            logging.info("set webhook for %s with result: %s", bot, res)

    async def setup_bot(self, bot: base_bot.BaseBot) -> None:
        middleware = middlewares.UserMiddleware(bot)
        bot.setup_middleware(middleware)
        bot.register_callback_query_handler(
            callback, func=lambda _: True, pass_bot=True
        )
        bot.register_message_handler(
            message,
            func=lambda _: True,
            content_types=["text", "voice", "photo", "document", "audio"],
            pass_bot=True,
        )
        if bot.bot_type == "telegram":
            bot.register_inline_handler(
                inline_query, func=lambda _: True, pass_bot=True
            )
            bot.register_chosen_inline_handler(
                inline_query_ai, func=lambda _: True, pass_bot=True
            )


@basic.try_except_wrapper
async def update_bot(
    bot_route: str, update_dict: dict[str, object], **kwargs: object
) -> None:
    bot = get_bot_by_route(bot_route)
    update = async_telebot.types.Update.de_json(update_dict)

    if update:
        await bot.process_new_updates([update])


def main() -> None:
    import asyncio

    BotHandler()
    bot = base_bot.TelegramBot()
    asyncio.run(bot.delete_webhook())
    asyncio.run(bot.polling())


if __name__ == "__main__":
    main()
