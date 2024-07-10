import os
import logging
import threading
import pytz
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from datetime import datetime
from werkzeug.utils import quote as url_quote
import asyncio

app = Flask(__name__)

# 读取环境变量
WEBHOOK_URL = 'https://tusi-wesroig870.replit.app'
TOKEN = os.getenv('TOKEN')

group_message_counts = {}
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

# 启用日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return "Bot is running!"


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        logging.debug("Webhook 路由被调用")
        update = Update.de_json(request.get_json(force=True))
        application.update_queue.put(update)
        return 'ok'


def run_web_server():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 443)))


# 启动命令处理函数
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_keyboard(update, context)


# 发送键盘按钮
async def send_keyboard(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [['查看资源', '吐司推荐'], ['查看报告', '提交报告'], ['抽奖活动', '开通会员'],
                ['囡囡点此免费认证上榜']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)

    if update.message.message_thread_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='请选择一个选项:',
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id)
    else:
        await update.message.reply_text('请选择一个选项:', reply_markup=reply_markup)


# 新成员加入时的处理函数
async def new_member(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("New member joined")
    await send_keyboard(update, context)


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

    elif text == '导航':
        inline_keyboard = [
            [
                InlineKeyboardButton("查看资源", callback_data='resource'),
                InlineKeyboardButton("吐司推荐", callback_data='recommend')
            ],
            [
                InlineKeyboardButton("查看报告", callback_data='view_report'),
                InlineKeyboardButton("提交报告", callback_data='submit_report')
            ],
            [
                InlineKeyboardButton("抽奖活动", callback_data='lottery'),
                InlineKeyboardButton("开通会员", callback_data='membership')
            ],
            [
                InlineKeyboardButton("囡囡点此免费认证上榜",
                                     callback_data='certification')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        sent_message = await update.message.reply_text(
            '文本广告位（可配图）：留待有缘人~', reply_markup=reply_markup)

    # Schedule a job to delete the message after 10 seconds
    if sent_message:
        context.job_queue.run_once(delete_message,
                                   10,
                                   data={
                                       'chat_id': chat_id,
                                       'message_id': sent_message.message_id
                                   })
        logger.info(
            f"Scheduled message deletion for message_id {sent_message.message_id}"
        )


# 处理群组中的消息
async def handle_group_message(update: Update,
                               context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat_id = message.chat_id
    user = message.from_user
    # 不统计通过按钮发送的消息
    if message.text in [
            "查看资源", "吐司推荐", "查看报告", "提交报告", "抽奖活动", "开通会员", "导航", "囡囡点此免费认证上榜"
    ]:
        logger.info("Ignored message as part of statistics blacklisted texts")
        logger.info("Ignored message from bot/channel/chat")
        return
    # 不统计群管理员、频道和机器人发送的消息
    if user.is_bot or user.is_channel or user.is_chat:
        return
    # 不统计贴纸消息和GIF消息
    if message.sticker or message.animation:
        logger.info("Ignored sticker/animation message")
        return
    # 检查消息是否重复
    if message.text in message_history.get(chat_id, []):
        logger.info("Ignored repeated message")
        return
    message_history.setdefault(chat_id, []).append(message.text)
    if chat_id not in group_message_counts:
        group_message_counts[chat_id] = {}
    user_id = user.id
    user_name = user.full_name
    user_username = user.username
    if user_id not in group_message_counts[chat_id]:
        group_message_counts[chat_id][user_id] = {
            "name": user_name,
            "username": user_username,
            "count": 0
        }
    group_message_counts[chat_id][user_id]["count"] += 1


# 处理回调查询
async def handle_callback_query(update: Update,
                                context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'resource':
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
        await query.edit_message_text('所有资源都在下方分区哦！',
                                      reply_markup=reply_markup)

    elif query.data == 'recommend':
        keyboard = [[
            InlineKeyboardButton("吐司推荐榜单", url="https://t.me/tusisz")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('当老师正在忙碌无法回复消息时，可通过客栈店小二“吐司”代为预约。',
                                      reply_markup=reply_markup)

    elif query.data == 'view_report':
        keyboard = [[
            InlineKeyboardButton("龙门报告", url="https://t.me/szhyChat")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('提交报告需要提供预约记录和支付记录哦！',
                                      reply_markup=reply_markup)

    elif query.data == 'submit_report':
        keyboard = [[
            InlineKeyboardButton("提交报告", url="https://t.me/spappraise_bot")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('提交报告需要提供预约记录哦！',
                                      reply_markup=reply_markup)

    elif query.data == 'lottery':
        keyboard = [[
            InlineKeyboardButton("抽奖活动专区", url="https://t.me/szpages/2837")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('来试试手气吧！', reply_markup=reply_markup)

    elif query.data == 'membership':
        keyboard = [[
            InlineKeyboardButton("自助开启电报会员", url="https://t.me/TPGift_BOT")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('可使用支付宝、微信和USDT进行支付，并在24小时内自动到账。',
                                      reply_markup=reply_markup)

    elif query.data == 'certification':
        keyboard = [[
            InlineKeyboardButton("点此联系管理", url="https://t.me/SZpages_bot")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('本群永久免费认证、上榜/推广！',
                                      reply_markup=reply_markup)


# 删除消息的回调函数
async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.data['chat_id']
    message_id = job.data['message_id']
    try:
        await context.bot.delete_message(chat_id=chat_id,
                                         message_id=message_id)
        logger.info(f"Deleted message_id {message_id}")
    except Exception as e:
        logger.error(f"Failed to delete message_id {message_id}: {e}")


async def send_hourly_statistics(context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if 11 <= now.hour <= 23:
        for chat_id, user_data in group_message_counts.items():
            sorted_users = sorted(user_data.items(),
                                  key=lambda x: x[1]["count"],
                                  reverse=True)
            top_10_users = sorted_users[:10]

            if top_10_users:
                message = "当前说话最大声的人：\n"
                for i, (user_id, data) in enumerate(top_10_users, 1):
                    message += f"{i}. {data['name']} @{data['username']}  {data['count']}条\n"
                message += "\n以上是今天发言数量最多的人"

                await context.bot.send_message(chat_id=chat_id, text=message)


async def send_final_statistics(context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if now.hour == 23 and now.minute == 59:
        for chat_id, user_data in group_message_counts.items():
            sorted_users = sorted(user_data.items(),
                                  key=lambda x: x[1]["count"],
                                  reverse=True)
            top_10_users = sorted_users[:10]

            if top_10_users:
                message = "今天发言数量最多的10人：\n"
                for i, (user_id, data) in enumerate(top_10_users, 1):
                    message += f"{i}. {data['name']} @{data['username']}  {data['count']}条\n"
                message += "\n以上是今天发言数量最多的人"

                sent_message = await context.bot.send_message(chat_id=chat_id,
                                                              text=message)
                await context.bot.pin_chat_message(
                    chat_id=chat_id, message_id=sent_message.message_id)

                # 延时24小时后取消置顶
                await asyncio.sleep(86400)
                await context.bot.unpin_chat_message(
                    chat_id=chat_id, message_id=sent_message.message_id)

            # 发送完统计消息后清除统计信息
            group_message_counts[chat_id].clear()


async def clear_statistics(context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if now.hour == 0 and now.minute == 0:
        # 任务已经在 send_final_statistics 中完成
        pass


# 设置Webhook
async def set_webhook(application, webhook_url):
    await application.bot.set_webhook(url=webhook_url)


def main() -> None:
    global application
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUP & filters.TEXT & ~filters.COMMAND,
            handle_message))
    application.add_handler(
        MessageHandler(filters.ChatType.GROUP & filters.TEXT,
                       handle_group_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    job_queue = application.job_queue
    job_queue.run_repeating(send_hourly_statistics, interval=3600,
                            first=0)  # 每小时执行一次
    job_queue.run_daily(send_final_statistics,
                        time=datetime.now(
                            pytz.timezone('Asia/Shanghai')).replace(hour=23,
                                                                    minute=59))
    job_queue.run_daily(clear_statistics,
                        time=datetime.now(
                            pytz.timezone('Asia/Shanghai')).replace(hour=0,
                                                                    minute=0))

    # 为运行Flask应用创建新线程
    threading.Thread(target=run_web_server).start()

    # 设置异步Webhook
    asyncio.run(set_webhook(application, f'{WEBHOOK_URL}/webhook/{TOKEN}'))


if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        main()
        logging.info("Bot started successfully")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
