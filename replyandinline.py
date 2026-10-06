import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Логирование для отслеживания ошибок
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Укажите ваш токен от @BotFather
BOT_TOKEN = "8984547798:AAGRG64kGgwmJOQ9tFauTui8ZDaM_XnA9xw"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик /start: отправляет приветствие и 5 Reply-кнопок."""
    # Создаем 5 Reply-кнопок (размещаем их в 3 ряда для удобства)
    reply_keyboard = [
        [KeyboardButton("➕ Добавить подписку"), KeyboardButton("📋 Мои подписки")],
        [KeyboardButton("🔔 Ближайшие оплаты"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("⚙️ Настройки")],
    ]

    # resize_keyboard=True делает кнопки компактными под размер экрана
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Привет! Я твой ассистент по подпискам.\n"
        "Выбери нужный раздел на клавиатуре ниже:",
        reply_markup=markup,
    )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик /help: отправляет сообщение с 2 Inline-кнопками."""
    # Создаем 2 Inline-кнопки под сообщением
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
    await query.answer()  # Убираем статус «загрузки» на кнопке

    if query.data == "btn_faq":
        await query.message.reply_text(
            "📌 **Часто задаваемые вопросы:**\n\n"
            "1. Как добавить подписку? — Нажми кнопку «➕ Добавить подписку».\n"
            "2. Когда приходит напоминание? — За 2 дня до даты списания.",
            parse_mode="Markdown",
        )


async def handle_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработка нажатий на Reply-кнопки и неизвестного текста."""
    text = update.message.text

    # Реагируем на 5 Reply-кнопок
    if text == "➕ Добавить подписку":
        await update.message.reply_text("Введите название сервиса и сумму:")
    elif text == "📋 Мои подписки":
        await update.message.reply_text("У вас пока нет активных подписок.")
    elif text == "🔔 Ближайшие оплаты":
        await update.message.reply_text("В ближайшие 7 дней списаний не планируется.")
    elif text == "📊 Статистика":
        await update.message.reply_text("Общие расходы в месяц: 0 руб.")
    elif text == "⚙️ Настройки":
        await update.message.reply_text("Раздел настроек бота.")
    else:
        # Если текст не совпал ни с одной кнопкой
        await update.message.reply_text(
            "Извини, я тебя не понял 🤖\n"
            "Воспользуйся кнопками меню или введи команду /help!"
        )


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчик Inline-кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

    # Обработчик любого текста (для Reply-кнопок и неизвестных команд)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()