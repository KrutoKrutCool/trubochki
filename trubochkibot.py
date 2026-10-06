import json
import logging
import os
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

# Логирование для отслеживания ошибок
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
FILE_PATH = "user.json"

# Состояния для диалога заполнения профиля (ConversationHandler)
NAME, AGE, COLOR, HOBBY, SUBSCRIPTION = range(5)


# --- Функции для работы с JSON-файлом ---


def load_users_data() -> dict:
    """Загружает данные всех пользователей из JSON файла."""
    if not os.path.exists(FILE_PATH):
        return {}
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return {}


def save_user_profile(user_id: str, profile_data: dict) -> None:
    """Сохраняет или обновляет профиль конкретного пользователя в JSON файле."""
    data = load_users_data()
    data[user_id] = profile_data
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_user_profile(user_id: str) -> dict | None:
    """Возвращает профиль пользователя по его ID."""
    data = load_users_data()
    return data.get(str(user_id))


# --- Основное меню (Reply-клавиатура) ---


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает главную клавиатуру с 5 Reply-кнопками."""
    reply_keyboard = [
        [
            KeyboardButton("➕ Добавить подписку"),
            KeyboardButton("📋 Мои подписки"),
        ],
        [KeyboardButton("👤 Мой профиль"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("⚙️ Настройки")],
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)


# --- Обработчики базовых команд ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /start: отправляет приветствие и 5 Reply-кнопок."""
    await update.message.reply_text(
        "Привет! Я твой ассистент по подпискам и личным настройкам.\n"
        "Выбери нужный раздел на клавиатуре ниже:",
        reply_markup=get_main_keyboard(),
    )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик /help: отправляет сообщение с 2 Inline-кнопками."""
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
        "Нужна помощь? Воспользуйся кнопками ниже:",
        reply_markup=markup,
    )


async def button_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработка нажатий на Inline-кнопки."""
    query = update.callback_query
    await query.answer()

    if query.data == "btn_faq":
        await query.message.reply_text(
            "📌 **Часто задаваемые вопросы:**\n\n"
            "1. Как заполнить профиль? — Введи команду /profile или нажми «👤 Мой профиль».\n"
            "2. Где хранятся данные? — Все данные надежно сохраняются в файле user.json.",
            parse_mode="Markdown",
        )


# --- Диалог заполнения/просмотра профиля (/profile) ---


async def profile_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Запуск команды /profile или кнопки '👤 Мой профиль'."""
    user_id = str(update.effective_user.id)
    profile = get_user_profile(user_id)

    # Если профиль уже существует — показываем его
    if profile:
        text = (
            "👤 **Твой профиль:**\n\n"
            f"1. **Имя:** {profile.get('name')}\n"
            f"2. **Возраст:** {profile.get('age')}\n"
            f"3. **Любимый цвет:** {profile.get('color')}\n"
            f"4. **Хобби:** {profile.get('hobby')}\n"
            f"5. **Любимое блюдо:** {profile.get('subscription')}\n\n"
            "Хочешь перезаписать профиль заново? Отправь своё **имя** прямо сейчас.\n"
            "Для отмены отправь команду /cancel."
        )
    else:
        text = (
            "📝 Давай закроем пару вопросов и заведем твой профиль!\n\n"
            "**Шаг 1 из 5:** Как тебя зовут?\n"
            "(Для отмены введи /cancel)"
        )

    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 1: Получаем имя."""
    context.user_data["profile_name"] = update.message.text
    await update.message.reply_text("**Шаг 2 из 5:** Сколько тебе лет?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 2: Получаем возраст."""
    context.user_data["profile_age"] = update.message.text
    await update.message.reply_text(
        "**Шаг 3 из 5:** Какой твой любимый цвет?"
    )
    return COLOR


async def get_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 3: Получаем любимый цвет."""
    context.user_data["profile_color"] = update.message.text
    await update.message.reply_text(
        "**Шаг 4 из 5:** Какое у тебя главное хобби?"
    )
    return HOBBY


async def get_hobby(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Шаг 4: Получаем хобби."""
    context.user_data["profile_hobby"] = update.message.text
    await update.message.reply_text(
        "**Шаг 5 из 5:** Какая твоя любимая еда?"
    )
    return SUBSCRIPTION


async def get_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Шаг 5: Получаем главную подписку и сохраняем всё в user.json."""
    context.user_data["profile_subscription"] = update.message.text
    user_id = str(update.effective_user.id)

    # Собираем данные
    profile_data = {
        "name": context.user_data.get("profile_name"),
        "age": context.user_data.get("profile_age"),
        "color": context.user_data.get("profile_color"),
        "hobby": context.user_data.get("profile_hobby"),
        "subscription": context.user_data.get("profile_subscription"),
    }

    # Сохраняем в JSON
    save_user_profile(user_id, profile_data)

    await update.message.reply_text(
        "✅ **Профиль успешно сохранен в user.json!**\n\n"
        f"• Имя: {profile_data['name']}\n"
        f"• Возраст: {profile_data['age']}\n"
        f"• Цвет: {profile_data['color']}\n"
        f"• Хобби: {profile_data['hobby']}\n"
        f"• Еда: {profile_data['subscription']}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )
    return ConversationHandler.END


async def cancel_profile(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Отмена заполнения профиля."""
    await update.message.reply_text(
        "Заполнение профиля отменено.", reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


# --- Обработка обычного текста ---


async def handle_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработка нажатий на Reply-кнопки и нераспознанного текста."""
    text = update.message.text

    if text == "➕ Добавить подписку":
        await update.message.reply_text("Введите название сервиса и сумму:")
    elif text == "📋 Мои подписки":
        await update.message.reply_text("У вас пока нет активных подписок.")
    elif text == "📊 Статистика":
        await update.message.reply_text("Общие расходы в месяц: 0 руб.")
    elif text == "⚙️ Настройки":
        await update.message.reply_text("Раздел настроек бота.")
    else:
        # Если команда/текст не распознаны
        await update.message.reply_text(
            "Извини, я тебя не понял 🤖\n"
            "Воспользуйся кнопками меню или введи команду /help!"
        )


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Пошаговый диалог для профиля
    profile_handler = ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_entry),
            MessageHandler(filters.Regex("^👤 Мой профиль$"), profile_entry),
        ],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_name
                )
            ],
            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_age
                )
            ],
            COLOR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_color
                )
            ],
            HOBBY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_hobby
                )
            ],
            SUBSCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, get_subscription
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_profile)],
    )

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(profile_handler)

    # Inline-кнопки
    application.add_handler(CallbackQueryHandler(button_callback))

    # Текстовые сообщения
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()