import uuid
from io import BytesIO

from fastapi_mongo_base.utils.basic import try_except_wrapper
from telebot import async_telebot

from apps.accounts.handlers import get_user_profile, get_usso_user
from apps.bots import base_bot, keyboards, models, schemas, services
from utils.b64tools import b64_decode_uuid
from utils.texttools import is_valid_url

command_key = {
    "/start": "start",
    "/help": "help",
    "راهنما": "help",
    "/getuserid": "getuserid",
    "مکالمه جدید": "new_conversation",
    "نمایش مکالمه": "show_conversation",
    "مکالمه‌های قبلی": "conversations",
    "ناحیه کاربری": "profile",
    "خرید اعتبار": "purchase",
    "/profile": "profile",
    "profile": "profile",
    "/sessions": "conversations",
    "/purchase": "purchase",
}


async def command(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    format_dict = {
        "username": message.from_user.username,
        "id": message.chat.id,
        "first": message.from_user.first_name,
        "last": message.from_user.last_name,
        "language": message.from_user.language_code,
    }

    query = message.text if message.text in command_key else "/start"
    match command_key[query]:
        case "start":
            return await bot.reply_to(
                message,
                "Welcome to the bot!",
                reply_markup=keyboards.main_keyboard(),
            )
        case "help":
            return await bot.reply_to(
                message,
                "Just send a message or voice",
                reply_markup=keyboards.main_keyboard(),
            )
        case "getuserid" | "profile":
            template = "\n".join([
                "username: `{username}`",
                "id: `{id}`",
                "first name: {first}",
                "last name: {last}",
                "language: {language}",
            ])
            return await bot.reply_to(
                message,
                template.format(**format_dict),
                parse_mode="markdownV2",
            )


async def prompt(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    response = await bot.reply_to(message, "Please wait ...")
    await services.ai_response(
        message=message.text,
        profile=message.profile,
        chat_id=message.chat.id,
        response_id=response.message_id,
        bot_name=bot.me,
    )


async def voice(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    response: schemas.MessageOwned = await bot.reply_to(
        message, "Please wait voice ..."
    )
    voice_info = await bot.get_file(message.voice.file_id)
    voice_file = await bot.download_file(voice_info.file_path)
    voice_bytes = BytesIO(voice_file)
    voice_bytes.name = "voice.ogg"
    transcription = await services.stt_response(voice_bytes)

    msg = models.Message(user_id=message.user.uid, content=transcription)
    await msg.save()

    if message.forward_origin:
        return await bot.edit_message_text(
            text=transcription,
            chat_id=message.chat.id,
            message_id=response.message_id,
            reply_markup=keyboards.answer_keyboard(msg.uid),
        )

    await bot.edit_message_text(
        text=transcription,
        chat_id=message.chat.id,
        message_id=response.message_id,
    )

    response.text = transcription
    response.user = message.user
    response.profile = message.profile
    await prompt(response, bot)


async def photo(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    response = await bot.reply_to(message, "Please wait photo ...")
    photo_info = await bot.get_file(message.photo[-1].file_id)
    photo_file = await bot.download_file(photo_info.file_path)
    photo_bytes = BytesIO(photo_file)
    photo_bytes.name = "photo.jpg"
    await services.ocr_response(photo_bytes)


async def document(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    response = await bot.reply_to(message, "Please wait document ...")
    document_info = await bot.get_file(message.document.file_id)
    document_file = await bot.download_file(document_info.file_path)
    document_bytes = BytesIO(document_file)
    document_bytes.name = "document.pdf"
    await services.ocr_response(document_bytes)


async def url_response(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    response = await bot.reply_to(message, "Please wait url ...", reply_markup=None)
    await services.url_response(
        url=message.text,
        user_id=message.user.uid,
        chat_id=message.chat.id,
        response_id=response.message_id,
        bot_name=bot.me,
    )


async def message(message: schemas.MessageOwned, bot: base_bot.BaseBot) -> None:
    if message.voice:
        return await voice(message, bot)
    if (
        message.text.startswith("/")
        or message.text in command_key
        or message.text in command_key.values()
    ):
        return await command(message, bot)
    if message.photo:
        return await photo(message, bot)

    if is_valid_url(message.text):
        return await url_response(message, bot)

    return await prompt(message, bot)


async def callback_read(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    message_id = uuid.UUID(call.data.split("_")[1])
    message: models.Message = await models.Message.get_item(
        uid=message_id, user_id=call.message.user.uid
    )
    voice = await services.tts_response(message.content)
    await bot.send_voice(call.message.chat.id, voice)


async def callback_answer(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    message_id = uuid.UUID(call.data.split("_")[1])
    message: models.Message = await models.Message.get_item(
        uid=message_id, user_id=call.message.user.uid
    )
    call.message.text = message.content

    await prompt(call.message, bot)


async def callback_select_ai(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    profile = call.message.profile
    profile.ai_engine = call.data.split("_")[2]
    # TODO
    profile.save()
    await bot.edit_message_text(
        text="AI Engine selected",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboards.select_ai_keyboard(profile),
    )


async def callback_brief(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    wid = call.data.split("_")[2]
    response = await bot.reply_to(call.message, "Please wait for content ...")
    await services.content_response(
        wid=wid,
        profile=call.message.profile,
        chat_id=call.message.chat.id,
        response_id=response.id,
        bot_name=bot.me,
    )


async def callback_content_select(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    webpage_response_uid, tuple_string = call.data.split(":")[-2:]
    webpage_response_uid = b64_decode_uuid(webpage_response_uid)
    tuple_elements = tuple_string.strip("()").split(",")
    new_state = tuple(map(int, tuple_elements))
    await bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboards.content_keyboard(webpage_response_uid, new_state),
    )


async def callback_content_submit(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    response = await bot.reply_to(call.message, "Please wait for rendering ...")

    webpage_response_uid, tuple_string = call.data.split(":")[-2:]
    webpage_response_uid = b64_decode_uuid(webpage_response_uid)
    tuple_elements = tuple_string.strip("()").split(",")
    state = tuple(map(int, tuple_elements))
    await services.content_submit(
        wrid=webpage_response_uid,
        state=state,
        profile=call.message.profile,
        chat_id=call.message.chat.id,
        bot_name=bot.me,
        response_id=response.id,
    )


async def callback(
    call: async_telebot.types.CallbackQuery, bot: base_bot.BaseBot, **kwargs: object
) -> None:
    if bot.bot_type == "telegram":
        await bot.answer_callback_query(call.id, text="Processing ...")

    if call.data.startswith("read_"):
        return await callback_read(call, bot)
    elif call.data.startswith("answer_"):
        return await callback_answer(call, bot)
    elif call.data.startswith("select_ai_"):
        return await callback_select_ai(call, bot)
    elif call.data.startswith("brief_textai_"):
        return await callback_brief(call, bot)
    elif call.data.startswith("content:select:"):
        return await callback_content_select(call, bot)
    elif call.data.startswith("content:submit:"):
        return await callback_content_submit(call, bot)


@try_except_wrapper
async def inline_query(
    inline_query: async_telebot.types.InlineQuery, bot: base_bot.BaseBot
) -> None:
    credentials = {
        "auth_method": bot.bot_type,
        "representor": f"{inline_query.from_user.id}",
    }
    # TODO
    user = await get_usso_user(credentials)
    await get_user_profile(user.uid)

    # ai_thumbnail_url = AIEngines.thumbnail_url(profile.data.ai_engine)
    ai_thumbnail_url = (
        "https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg"
    )

    results = [
        async_telebot.types.InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Generate with AI",
            input_message_content=async_telebot.types.InputTextMessageContent(
                message_text=f"Answer with AI (⏳)\n\n{inline_query.query}"
            ),
            reply_markup=keyboards.inline_keyboard(),
            thumbnail_url=ai_thumbnail_url,
        )
    ]
    await bot.answer_inline_query(inline_query.id, results, cache_time=300)


async def inline_query_ai(
    inline_result: async_telebot.types.ChosenInlineResult, bot: base_bot.BaseBot
) -> None:
    credentials = {
        "auth_method": bot.bot_type,
        "representor": f"{inline_result.from_user.id}",
    }
    # TODO
    user = await get_usso_user(credentials)
    profile = await get_user_profile(user.uid)

    await services.ai_response(
        message=inline_result.query,
        profile=profile,
        inline_message_id=inline_result.inline_message_id,
        bot_name=bot.me,
    )
