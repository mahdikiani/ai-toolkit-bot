from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from utils import b64tools


def main_keyboard() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        KeyboardButton("راهنما"),
        KeyboardButton("ناحیه کاربری"),
        KeyboardButton("خرید اعتبار"),
    )

    return markup


def read_keyboard(message_id: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("خواندن", callback_data=f"read_{message_id}"),
    )
    return markup


def answer_keyboard(message_id: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("جواب دادن", callback_data=f"answer_{message_id}"),
    )
    return markup


def inline_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("رفتن به بات", url="https://t.me/tgyt_bot"),
    )
    return markup


def url_keyboard(url: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("معرفی برند", callback_data=f"url_brief_{url}"),
        InlineKeyboardButton("رپورتاژ", callback_data=f"url_reportage_{url}"),
    )
    markup.add(
        InlineKeyboardButton("ترجمه", callback_data=f"url_translate_{url}"),
        InlineKeyboardButton("خلاصه", callback_data=f"url_abstract_{url}"),
    )
    return markup


def brief_keyboard(webpage_uid: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "پیشنهاد متن با هوش مصنوعی",
            callback_data=f"brief_textai_{webpage_uid}",
        ),
    )
    return markup


def content_keyboard(
    uid: str, select_state: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
) -> InlineKeyboardMarkup:
    content_titles = ["Title", "Subtitle", "Description", "CTA", "Image"]
    markup = InlineKeyboardMarkup(row_width=6)
    uid = b64tools.b64_encode_uuid_strip(uid)

    for i in range(5):
        krow = [
            InlineKeyboardButton(content_titles[i], callback_data=content_titles[i]),
        ]
        for j in range(5):
            new_state = (*select_state[:i], j, *select_state[i + 1 :])
            # new_state = "_".join(map(str, new_state))
            if select_state[i] == j:
                krow.append(
                    InlineKeyboardButton(
                        f"✅ {j + 1}",
                        callback_data=f"content:select:{uid}:{new_state}",
                    ),
                )
            else:
                krow.append(
                    InlineKeyboardButton(
                        f"{j + 1}",
                        callback_data=f"content:select:{uid}:{new_state}",
                    ),
                )
        markup.add(*krow)

    markup.add(
        InlineKeyboardButton(
            "Generate", callback_data=f"content:submit:{uid}:{select_state}"
        )
    )
    return markup
