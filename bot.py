import os
import logging
import pytz
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, JobQueue, filters
from datetime import datetime
import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config

# 初始化Flask应用和日志记录
app = Flask(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://tusi-wesroig870.replit.app')
TOKEN = os.getenv('TOKEN')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

message_history = {}
group_message_counts = {}
lock = asyncio.Lock()  # 用于保护共享资源的全局锁


@app.route('/')
def index():
    # 检查机器人是否在运行
    return "Bot is running!"


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # 处理 Telegram Webhook 请求
    if request.method == "POST":
        payload = request.get_json(force=True)
        if 'message' in payload:
            update = Update.de_json(payload, application.bot)
            application.update_queue.put(update)
            return 'ok'
    return 'invalid method'


# 启动Web服务器
async def run_web_server():
    config = Config()
    port = int(os.environ.get('PORT', 5000))
    config.bind = [f"0.0.0.0:{port}"]
    await serve(app, config)


# 设置Webhook
async def set_webhook(application, webhook_url):
    # 设置Telegram机器人的Webhook URL
    await application.bot.set_webhook(url=webhook_url)


# 处理/start命令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 发送自定义键盘
    await send_keyboard(update, context)


# 发送自定义键盘
async def send_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 自定义键盘按钮
    keyboard = [['查看资源', '吐司推荐'], ['查看报告', '提交报告'], ['抽奖活动', '开通会员'],
                ['囡囡点此免费认证上榜']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)
    await update.message.reply_text('请选择一个选项:', reply_markup=reply_markup)


# 处理普通文本消息
async def handle_message(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    chat_id = update.effective_chat.id
    sent_message = None

    logger.info(f"Received message: {text}")

    if text == '查看资源':
        keyboard = [[
            InlineKeyboardButton("罗湖区", url="https://t.me/szpages/2764"),
            InlineKeyboardButton("福田区", url="https://t.me/szpages/2668"),
            InlineKeyboardButton("南山区", url="https://t.me/szpages/2777")
        ],
                    [
                        InlineKeyboardButton("龙岗区",
                                             url="https://t.me/szpages/2774"),
                        InlineKeyboardButton("宝安区",
                                             url="https://t.me/szpages/2767"),
                        InlineKeyboardButton("龙华区",
                                             url="https://t.me/szpages/2683")
                    ],
                    [
                        InlineKeyboardButton("抽奖活动专区",
                                             url="https://t.me/szpages/2837")
                    ],
                    [
                        InlineKeyboardButton("账号注册 / 账号解禁 / 科学上网",
                                             url="https://t.me/szpages/2760")
                    ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '所有资源都在下方分区哦！', reply_markup=reply_markup)

    elif text == '吐司推荐':
        keyboard = [[
            InlineKeyboardButton("吐司推荐榜单", url="https://t.me/tusisz")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '当老师正在忙碌无法回复消息时，可通过客栈店小二“吐司”代为预约。', reply_markup=reply_markup)

    elif text == '查看报告':
        keyboard = [[
            InlineKeyboardButton("龙门报告", url="https://t.me/szhyChat")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '提交报告需要提供预约记录和支付记录哦！', reply_markup=reply_markup)

    elif text == '提交报告':
        keyboard = [[
            InlineKeyboardButton("提交报告", url="https://t.me/spappraise_bot")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '提交报告需要提供预约记录哦！', reply_markup=reply_markup)

    elif text == '抽奖活动':
        keyboard = [[
            InlineKeyboardButton("抽奖活动专区", url="https://t.me/szpages/2837")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '来试试手气吧！', reply_markup=reply_markup)

    elif text == '开通会员':
        keyboard = [[
            InlineKeyboardButton("自助开启电报会员", url="https://t.me/TPGift_BOT")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '可使用支付宝、微信和USDT进行支付，并在24小时内自动到账。', reply_markup=reply_markup)

    elif text == '囡囡点此免费认证上榜':
        keyboard = [[
            InlineKeyboardButton("点此联系管理", url="https://t.me/SZpages_bot")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.message.reply_text(
            '本群永久免费认证、上榜/推广！', reply_markup=reply_markup)

    # 删除临时消息
    if sent_message:
        context.job_queue.run_once(delete_message,
                                   10,
                                   data={
                                       'chat_id': chat_id,
                                       'message_id': sent_message.message_id
                                   })


# 处理群组消息
async def handle_group_message(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    user = message.from_user

    # 过滤掉不需要统计的消息
    if user.is_bot:  # 过滤机器人消息
        return

    # 获取管理员列表，确保过滤出管理员消息。如果没有缓存，可以通过API获取。
    member_status = await context.bot.get_chat_member(chat_id, user.id)
    if member_status.status in ["administrator", "creator"]:  # 过滤管理员消息
        return

    # 过滤消息中的贴纸和动画，以及特定的关键词
    if message.sticker or message.animation or message.text in [
            "查看资源", "吐司推荐", "查看报告", "提交报告", "抽奖活动", "开通会员", "囡囡点此免费认证上榜"
    ]:
        return

    async with lock:
        # 记录发言并统计每个用户的消息数量
        user_id = user.id
        if chat_id not in group_message_counts:
            group_message_counts[chat_id] = {}
        if user_id not in group_message_counts[chat_id]:
            group_message_counts[chat_id][user_id] = {
                "count": 0,
                "name": user.full_name,
                "username": user.username
            }
        group_message_counts[chat_id][user_id]["count"] += 1


# 删除消息
async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.data['chat_id'],
                                         message_id=job.data['message_id'])
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")


# 获取聊天用户数据
def get_user_data(chat_id):
    return group_message_counts.get(chat_id, {})


# 每小时发送统计数据
async def send_hourly_statistics(context: ContextTypes.DEFAULT_TYPE):
    chat_id = int(TARGET_CHAT_ID)
    user_data = get_user_data(chat_id)
    if not user_data:
        return

    sorted_users = sorted(user_data.items(),
                          key=lambda x: x[1]["count"],
                          reverse=True)
    message_lines = [
        f'{i+1}. {v["name"]} @{v["username"]} {v["count"]}条'
        for i, (_, v) in enumerate(sorted_users[:10])
    ]
    message = "截止到当前发送消息数量最多的是：\n" + '\n'.join(message_lines)

    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logger.error(f"Failed to send hourly statistics: {e}")


# 每晚23:59发送最终统计数据
async def send_final_statistics(context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if now.hour == 23 and now.minute == 59:
        for chat_id, user_data in group_message_counts.items():
            # 按消息数量从多到少排序
            sorted_users = sorted(user_data.items(),
                                  key=lambda x: x[1]["count"],
                                  reverse=True)
            top_10_users = sorted_users[:10]

            if top_10_users:
                message = "今天发言数量最多的10人：\n\n"
                for i, (user_id, data) in enumerate(top_10_users, 1):
                    message += f"{i}. {data['name']} @{data['username']}  {data['count']}条\n"
                message += "\n以上是今天发言数量最多的人"

                try:
                    sent_message = await context.bot.send_message(
                        chat_id=chat_id, text=message)
                    await context.bot.pin_chat_message(
                        chat_id=chat_id, message_id=sent_message.message_id)

                    # 延时24小时后取消置顶
                    asyncio.create_task(
                        unpin_message_after_24_hours(context, chat_id,
                                                     sent_message.message_id))
                except Exception as e:
                    logger.error(f"Failed to send final statistics: {e}")

            # 发送完统计消息后清除统计信息
            async with lock:
                group_message_counts[chat_id].clear()


async def unpin_message_after_24_hours(context: ContextTypes.DEFAULT_TYPE,
                                       chat_id: int, message_id: int):
    await asyncio.sleep(86400)
    try:
        await context.bot.unpin_chat_message(chat_id=chat_id,
                                             message_id=message_id)
    except Exception as e:
        logger.error(f"Failed to unpin message: {e}")


# 每天午夜清除统计数据
async def clear_statistics(context: ContextTypes.DEFAULT_TYPE):
    async with lock:
        message_history.clear()
        group_message_counts.clear()


# 每小时任务：从11:00开始每小时发送统计数据
async def hourly_task(context: ContextTypes.DEFAULT_TYPE):
    shanghai_time = pytz.timezone('Asia/Shanghai')
    while True:
        now = datetime.now(shanghai_time)
        if now.hour >= 11:
            await send_hourly_statistics(context)
        await asyncio.sleep(3600)  # 每小时检查一次


# 每日任务：每晚23:59发送最终统计数据，并清除每天的统计数据
async def daily_task(context: ContextTypes.DEFAULT_TYPE):
    shanghai_time = pytz.timezone('Asia/Shanghai')
    while True:
        now = datetime.now(shanghai_time)
        if now.hour == 23 and now.minute == 59:
            await send_final_statistics(context)
        if now.hour == 0 and now.minute == 0:
            await clear_statistics(context)

        await asyncio.sleep(60)  # 每分钟检查一次


# 启动Telegram Bot轮询
async def telegram_bot_polling():
    global application
    job_queue = JobQueue()
    application = Application.builder().token(TOKEN).job_queue(
        job_queue).build()

    await application.initialize()
    await set_webhook(application, f'{WEBHOOK_URL}/webhook')

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUP & filters.TEXT & ~filters.COMMAND,
            handle_message))
    application.add_handler(
        MessageHandler(filters.ChatType.GROUP & filters.TEXT,
                       handle_group_message))

    job_queue.run_repeating(send_hourly_statistics, interval=3600, first=0)
    job_queue.run_repeating(send_final_statistics, interval=86400, first=23400)
    job_queue.run_repeating(clear_statistics, interval=86400, first=0)

    await application.start()
    try:
        await application.updater.start_polling()
    finally:
        await application.stop()
        await application.shutdown()


async def main():
    await asyncio.gather(run_web_server(), telegram_bot_polling(),
                         hourly_task(ContextTypes.DEFAULT_TYPE),
                         daily_task(ContextTypes.DEFAULT_TYPE))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"发生错误: {e}")
