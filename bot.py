import os
import logging
import asyncio
import requests
from replit import db
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 创建 Flask 应用
app = Flask(__name__)

# 获取 TOKEN 和 group ID
TOKEN = os.getenv('TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# 初始化 Telegram bot 和 application
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    logger.debug("Home route called")
    return "Hello, World!"

@app.route('/health', methods=['GET'])
def health_check():
    logger.debug("/health route called")
    return jsonify(status='OK'), 200

@app.route('/trigger_stats', methods=['GET'])
def trigger_stats_route():
    logger.debug("/trigger_stats route called")
    try:
        asyncio.run(trigger_stats_internal())
        return jsonify(status='Statistics triggered successfully!'), 200
    except asyncio.CancelledError:
        return jsonify(status='Failed to trigger statistics.'), 500

async def trigger_stats_internal():
    await send_statistics_internal()
    logger.debug("Statistics sent via manual trigger.")

@app.route('/debug', methods=['GET'])
def debug():
    logger.debug("/debug route called")
    return "Debug route working!", 200

def setup_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    data = {"url": WEBHOOK_URL}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        logger.error(f"设置Webhook失败: {response.text}")
    else:
        logger.info("Webhook设置成功！")

# 检查是否是管理员
async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        administrators = await bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in administrators)
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

# 检查消息是否为 emoji
def is_emoji_message(message: str) -> bool:
    from emoji import is_emoji
    return all(is_emoji(char) for char in message)

# 处理消息
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.effective_message

    logger.debug(f"Received message from user {user.id} in chat {chat_id}")

    if await is_admin(chat_id, user.id):
        logger.debug(f"User {user.id} is admin, ignoring message.")
        return

    if update.effective_chat.type in ['channel', 'group', 'supergroup']:
        logger.debug(f"Message in {update.effective_chat.type} ignored。")
        return

    if message.sticker or message.photo or message.animation or is_emoji_message(message.text):
        logger.debug("Message contains sticker/photo/animation/emoji, ignoring。")
        return

    user_key = f"user:{user.id}"
    user_messages_key = f"user_msgs:{user.id}"

    if message.text in db.get(user_messages_key, []):
        logger.debug("Message text already recorded, ignoring。")
        return

    db[user_messages_key] = db.get(user_messages_key, []) + [message.text]
    logger.debug(f"Updated user messages: {db[user_messages_key]}")

    user_data = db.get(user_key, {"name": user.name, "username": user.username, "count": 0})
    user_data["count"] += 1
    db[user_key] = user_data
    logger.debug(f"Updated user data: {user_data}")

# 发送统计数据
async def send_statistics_internal() -> None:
    users = sorted([(db[key]["name"], db[key]["username"], db[key]["count"]) for key in db.keys() if key.startswith("user:")],
                    key=lambda x: x[2], reverse=True)[:10]

    if not users:
        logger.debug("No users to send statistics for。")
        return

    msg = "现在发送消息最多的是：\n\n"
    for i, (name, username, count) in enumerate(users, 1):
        msg += f"{i}. {name} @{username} {count} 条\n"

    logger.debug(f"Sending statistics message: {msg}")
    await bot.send_message(chat_id=GROUP_ID, text=msg)

# 每天00:00发送统计结果并清空数据
async def reset_and_send_statistics() -> None:
    await send_statistics_internal()

    msg = "今天发送消息最多的人是：\n\n"
    users = sorted([(db[key]["name"], db[key]["username"], db[key]["count"]) for key in db.keys() if key.startswith("user:")],
                    key=lambda x: x[2], reverse=True)[:10]

    for i, (name, username, count) in enumerate(users, 1):
        msg += f"{i}. {name} @{username} {count} 条\n"
    
    msg += "\n恭喜他们！"
    logger.debug(f"Sending daily reset message: {msg}")
    await bot.send_message(chat_id=GROUP_ID, text=msg)
    logger.debug("Resetting user data in Replit Database。")
    for key in db.keys():
        del db[key]

def schedule_jobs():
    from threading import Timer

    def cron_job():
        now = datetime.now(tz=timezone(timedelta(hours=8)))
        if now.hour == 0 and now.minute == 0:
            asyncio.run(reset_and_send_statistics())
        elif 11 <= now.hour <= 23 and now.minute == 0:
            asyncio.run(send_statistics_internal())
        next_run = now + timedelta(minutes=1)
        Timer((next_run - now).total_seconds(), cron_job).start()

    cron_job()

if __name__ == '__main__':
    setup_webhook()
    schedule_jobs()
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting app on port {port}")
    logger.info(f"Environment variables: TOKEN={TOKEN}, GROUP_ID={GROUP_ID}, WEBHOOK_URL={WEBHOOK_URL}")
    app.run(host="0.0.0.0", port=port, debug=True)
