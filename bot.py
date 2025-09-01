# bot.py
import logging
import html
import os
from http import HTTPStatus

# Веб-сервер
from aiohttp import web

# Бот
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"  # ← Замени!
GROUP_ID = -1003033000994  # ← Замени!
PORT = int(os.environ.get("PORT", 10000))  # Render передаёт PORT

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Веб-сервер: раздаёт простой ответ ===
async def handle_root(request):
    return web.Response(text="Bot is running", status=HTTPStatus.OK)

# === Запуск веб-сервера ===
async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"🌐 Веб-сервер запущен на порту {PORT}")

# === Бот: /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Получен /start от {user.full_name}")
    keyboard = [[{"text": "🎥 Открыть камеры", "web_app": {"url": "https://cameri-github-io.onrender.com"}}]]
    reply_markup = {"inline_keyboard": keyboard}
    await update.message.reply_text("👋 Добро пожаловать!", reply_markup=reply_markup)

# === Обработка web_app_data ===
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.effective_message.web_app_data.data
        logger.info(f"📩 Получены данные: {data}")
        import json
        data = json.loads(data)
        event_type = data.get("type", "неизвестно")
        camera = data.get("camera", "неизвестна")
        timestamp = data.get("timestamp", "неизвестно")
        user = update.effective_user

        text = (
            f"🚨 <b>Событие:</b> {html.escape(event_type)}\n"
            f"📹 <b>Камера:</b> {html.escape(camera)}\n"
            f"👤 <b>Пользователь:</b> {html.escape(user.full_name)}\n"
            f"🆔 <b>ID:</b> {user.id}\n"
            f"🕒 <b>Время:</b> {timestamp}"
        )

        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
        await update.message.reply_text("✅ Событие отправлено в группу!")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")

# === Запуск всего ===
async def main():
    # Запускаем веб-сервер
    await run_web_server()

    # Создаём приложение бота
    application = Application.builder().token(API_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    logger.info("🚀 Бот запущен. Ожидаем сообщения...")

    # Запускаем polling без попытки закрыть loop
    try:
        await application.updater.start_polling()
        await application.start()
        # Держим бота в работе
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Polling остановлен: {e}")
    finally:
        await application.stop()
        await application.updater.stop()


# === Запуск (совместимо с Render) ===
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
