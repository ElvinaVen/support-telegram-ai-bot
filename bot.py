"""
Бот, который отвечает на сообщения в Telegram.
Сначала определяются несколько функций-обработчиков.
Затем эти функции передаются в приложение и регистрируются в соответствующих местах.
После этого бот запускается и работает до тех пор, пока вы не нажмете Ctrl-C в командной строке.
"""

import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

from telegram import ForceReply, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from model import chat_with_llm

import dotenv
# Загружаем переменные окружения из файла .env
try:
    env = dotenv.dotenv_values(".env")
    TELEGRAM_BOT_TOKEN = env["TELEGRAM_BOT_TOKEN"]
except FileNotFoundError:
    raise FileNotFoundError("Файл .env не найден. Убедитесь, что он существует в корневой директории проекта.")
except KeyError as e:
    raise KeyError(f"Переменная окружения {str(e)} не найдена в файле .env. Проверьте его содержимое.")


# Определим команды и функции-обработчики сообщений
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. При старте бота пользователь получает приветственное сообщение."""
    user = update.effective_user
    await update.message.reply_html(
        rf"👋 Приветствуем Вас {user.mention_html()} в службе поддержки электроснабжения!"
    
    "⚡ Мы ценим Ваше обращение и готовы помочь в решении возникшей проблемы.\n\n"
    
    "📝 Для оперативного решения вопроса, пожалуйста:\n"
    "* Опишите ситуацию\n"
    "* Укажите адрес помещения (город, улица, дом, квартира/офис)\n\n"
    
    "Мы обработаем Ваше обращение в кратчайшие сроки и сообщим о дальнейших действиях. 🔧",
        reply_markup=ForceReply(selective=True),
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основная функция для обработки текстовых сообщений от пользователя с целью ответа на них с помощью AI."""
    user_message = update.message.text

    # Получаем историю сообщений из context.chat_data
    history = context.chat_data.get("history", [])
    logger.debug(f"History: {history}")

    # Передаем текущий запрос и историю сообщений в llm_service
    llm_response = chat_with_llm(user_message, history=history)
    context.chat_data["history"] = history  # сохраняем обновленную историю
    await update.message.reply_text(llm_response)


def main() -> None:
    """Функция инициализации бот-приложения."""
    # Создание основного объекта приложения Telegram API
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчик всех текстовых сообщений без команды
    chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, chat)  

    # Регистрируем обработчики:
    # Команда /start
    application.add_handler(CommandHandler("start", start))
    # Все остальные текстовые сообщения обрабатываются chat_handler
    application.add_handler(chat_handler)

    # Запуск бота в режиме постоянного ожидания команд.
    # Бот работает до прекращения программы (нажатие Ctrl-C или завершение по другому сигналу)
    application.run_polling(allowed_updates=Update.ALL_TYPES)  


if __name__ == "__main__":
    main()
