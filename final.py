import json
import logging
import os
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Загружаем переменные окружения из файла .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Логирование для отслеживания ошибок
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

FILE_PATH = "user.json"

# Состояния для пошагового диалога профиля
NAME, AGE, COLOR, HOBBY, FOOD = range(5)

# Состояния для пошагового диалога добавления подписки
SUB_NAME, SUB_AMOUNT = range(10, 12)


# --- Функции для работы с JSON-файлом ---


def load_all_data() -> dict:
    """Загружает все данные пользователей из файла user.json."""
    if not os.path.exists(FILE_PATH):
        return {}
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return {}


def save_all_data(data: dict) -> None:
    """Сохраняет все данные в файл user.json."""
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_user_data(user_id: str) -> dict:
    """Возвращает данные конкретного пользователя, гарантируя наличие всех ключей."""
    data = load_all_data()
    if user_id not in data:
        data[user_id] = {"profile": {}, "subscriptions": []}
    if "profile" not in data[user_id]:
        data[user_id]["profile"] = {}
    if "subscriptions" not in data[user_id]:
        data[user_id]["subscriptions"] = []
    return data[user_id]


# --- Главная клавиатура (5 Reply-кнопок) ---


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает основную клавиатуру бота."""
    reply_keyboard = [
        [
            KeyboardButton("➕ Добавить подписку"),
            KeyboardButton("📋 Мои подписки"),
        ],
        [KeyboardButton("👤 Мой профиль"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("🗑 Удалить подписку")],
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)


# --- Базовые команды ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text(
        "Привет! Я твой ассистент по подпискам и личным настройкам.\n"
        "Выбери нужный раздел на клавиатуре ниже:",
        reply_markup=get_main_keyboard(),
    )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик команды /help с 2 Inline-кнопками."""
    inline_keyboard = [
        [
            InlineKeyboardButton(
                "💬 Написать в поддержку", url="https://t.me/telegram"
            ),
            InlineKeyboardButton("❓ FAQ", callback_data="btn_faq"),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard)
    await update.message.reply_text(
        "Нужна помощь? Воспользуйся кнопками ниже:", reply_markup=markup
    )


async def button_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработка нажатий на Inline-кнопки (FAQ и удаление подписок)."""
    query = update.callback_query
    await query.answer()

    if query.data == "btn_faq":
        await query.message.reply_text(
            "📌 **Часто задаваемые вопросы:**\n\n"
            "1. Как заполнить профиль? — Нажми «👤 Мой профиль».\n"
            "2. Как добавить подписку? — Нажми «➕ Добавить подписку».\n"
            "3. Как удалить подписку? — Нажми «🗑 Удалить подписку» и выбери её из списка.\n"
            "4. Где хранятся данные? — В файле user.json.",
            parse_mode="Markdown",
        )
    elif query.data.startswith("del_"):
        # Логика удаления выбранной подписки по индексу
        try:
            index = int(query.data.split("_")[1])
            user_id = str(query.from_user.id)
            all_data = load_all_data()

            if (
                user_id in all_data
                and "subscriptions" in all_data[user_id]
                and len(all_data[user_id]["subscriptions"]) > index
            ):
                removed = all_data[user_id]["subscriptions"].pop(index)
                save_all_data(all_data)
                await query.message.edit_text(
                    f"✅ Подписка **{removed['name']}** ({removed['amount']}) успешно удалена!",
                    parse_mode="Markdown",
                )
            else:
                await query.message.edit_text(
                    "⚠️ Подписка не найдена или уже была удалена."
                )
        except Exception:
            await query.message.edit_text(
                "❌ Произошла ошибка при удалении подписки."
            )


# --- Диалог профиля (/profile или кнопка) ---


async def profile_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Вход в диалог профиля (5 аспектов)."""
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    profile = user_data.get("profile", {})

    if profile:
        text = (
            "👤 **Твой профиль:**\n\n"
            f"1. **Имя:** {profile.get('name')}\n"
            f"2. **Возраст:** {profile.get('age')}\n"
            f"3. **Любимый цвет:** {profile.get('color')}\n"
            f"4. **Хобби:** {profile.get('hobby')}\n"
            f"5. **Любимая еда:** {profile.get('food')}\n\n"
            "Хочешь перезаписать профиль? Отправь своё **имя** прямо сейчас.\n"
            "Для отмены отправь команду /cancel."
        )
    else:
        text = (
            "📝 Давай заполним твой профиль!\n\n"
            "**Шаг 1 из 5:** Как тебя зовут?\n"
            "(Для отмены введи /cancel)"
        )

    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def profile_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["p_name"] = update.message.text
    await update.message.reply_text("**Шаг 2 из 5:** Сколько тебе лет?")
    return AGE


async def profile_age(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["p_age"] = update.message.text
    await update.message.reply_text("**Шаг 3 из 5:** Какой твой любимый цвет?")
    return COLOR


async def profile_color(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["p_color"] = update.message.text
    await update.message.reply_text(
        "**Шаг 4 из 5:** Какое у тебя главное хобби?"
    )
    return HOBBY


async def profile_hobby(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["p_hobby"] = update.message.text
    await update.message.reply_text(
        "**Шаг 5 из 5:** Какая твоя любимая еда? 🍕"
    )
    return FOOD


async def profile_food(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["p_food"] = update.message.text
    user_id = str(update.effective_user.id)

    profile_data = {
        "name": context.user_data.get("p_name"),
        "age": context.user_data.get("p_age"),
        "color": context.user_data.get("p_color"),
        "hobby": context.user_data.get("p_hobby"),
        "food": context.user_data.get("p_food"),
    }

    all_data = load_all_data()
    if user_id not in all_data:
        all_data[user_id] = {"profile": {}, "subscriptions": []}
    all_data[user_id]["profile"] = profile_data
    save_all_data(all_data)

    await update.message.reply_text(
        "✅ **Профиль успешно сохранен в user.json!**\n\n"
        f"• Имя: {profile_data['name']}\n"
        f"• Возраст: {profile_data['age']}\n"
        f"• Цвет: {profile_data['color']}\n"
        f"• Хобби: {profile_data['hobby']}\n"
        f"• Любимая еда: {profile_data['food']}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )
    return ConversationHandler.END


# --- Диалог добавления подписки ---


async def sub_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Вход в диалог добавления подписки."""
    await update.message.reply_text(
        "➕ **Добавление новой подписки**\n\n"
        "Введите название сервиса (например, *Netflix*, *Spotify*, *VPN*):\n"
        "(Для отмены введи /cancel)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SUB_NAME


async def sub_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["sub_name"] = update.message.text
    await update.message.reply_text(
        "Введите стоимость и период списания (например, *499 руб/мес* или *$5/месяц*):",
        parse_mode="Markdown",
    )
    return SUB_AMOUNT


async def sub_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    sub_name_val = context.user_data.get("sub_name")
    sub_amount_val = update.message.text
    user_id = str(update.effective_user.id)

    all_data = load_all_data()
    if user_id not in all_data:
        all_data[user_id] = {"profile": {}, "subscriptions": []}
    if "subscriptions" not in all_data[user_id]:
        all_data[user_id]["subscriptions"] = []

    all_data[user_id]["subscriptions"].append(
        {"name": sub_name_val, "amount": sub_amount_val}
    )
    save_all_data(all_data)

    await update.message.reply_text(
        f"✅ Подписка **{sub_name_val}** ({sub_amount_val}) успешно сохранена!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )
    return ConversationHandler.END


async def cancel_dialog(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Общая отмена для диалогов."""
    await update.message.reply_text(
        "Действие отменено.", reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


# --- Обработчики основных кнопок ---


async def list_subscriptions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Вывод списка подписок пользователя из JSON."""
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    subs = user_data.get("subscriptions", [])

    if not subs:
        await update.message.reply_text(
            "📋 У вас пока нет сохраненных подписок.\n"
            "Нажмите «➕ Добавить подписку», чтобы создать первую!",
            reply_markup=get_main_keyboard(),
        )
        return

    text = "📋 **Ваши подписки:**\n\n"
    for i, sub in enumerate(subs, 1):
        text += f"{i}. **{sub['name']}** — {sub['amount']}\n"

    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=get_main_keyboard()
    )


async def show_stats(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Отображение статистики."""
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    count = len(user_data.get("subscriptions", []))

    await update.message.reply_text(
        "📊 **Статистика:**\n\n"
        f"• Всего активных подписок: {count}\n"
        "• Все данные надежно хранятся и переживают перезапуск бота.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )


async def delete_sub_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Меню выбора подписки для удаления с помощью Inline-кнопок."""
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    subs = user_data.get("subscriptions", [])

    if not subs:
        await update.message.reply_text(
            "📋 У вас нет подписок для удаления.",
            reply_markup=get_main_keyboard(),
        )
        return

    inline_keyboard = []
    for index, sub in enumerate(subs):
        inline_keyboard.append([
            InlineKeyboardButton(
                f"❌ Удалить: {sub['name']} ({sub['amount']})",
                callback_data=f"del_{index}",
            )
        ])

    markup = InlineKeyboardMarkup(inline_keyboard)
    await update.message.reply_text(
        "🗑 **Удаление подписки**\nВыберите подписку из списка ниже:",
        parse_mode="Markdown",
        reply_markup=markup,
    )


async def handle_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработка текстовых кнопок и защита от непонятных сообщений."""
    text = update.message.text

    if text == "📋 Мои подписки":
        await list_subscriptions(update, context)
    elif text == "📊 Статистика":
        await show_stats(update, context)
    elif text == "🗑 Удалить подписку":
        await delete_sub_menu(update, context)
    else:
        # Если бот вообще ничего не понял
        await update.message.reply_text(
            "Извини, я тебя не понял 🤖\n"
            "Воспользуйся кнопками меню или введи команду /help!"
        )


def main() -> None:
    """Запуск приложения бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Диалог настройки профиля
    profile_handler = ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_entry),
            MessageHandler(filters.Regex("^👤 Мой профиль$"), profile_entry),
        ],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, profile_name
                )
            ],
            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, profile_age
                )
            ],
            COLOR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, profile_color
                )
            ],
            HOBBY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, profile_hobby
                )
            ],
            FOOD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, profile_food
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_dialog)],
    )

    # Диалог добавления подписки
    sub_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^➕ Добавить подписку$"), sub_entry
            )
        ],
        states={
            SUB_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sub_name)
            ],
            SUB_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, sub_amount
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_dialog)],
    )

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(profile_handler)
    application.add_handler(sub_handler)

    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    print("Бот успешно запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()