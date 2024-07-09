import os
import logging
import threading
import pytz
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ChatMemberHandler
from datetime import datetime, time as dt_time
from werkzeug.utils import quote as url_quote
import time

# 创建 Flask Web 服务器
app = Flask(__name__)


# 运行 Flask 服务器的函数
def run_web_server():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))


@app.route('/')
def index():
    return "Bot is running!"


TOKEN = os.getenv('TOKEN')


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        logging.debug("Webhook route called")
        update = Update.de_json(request.get_json(force=True))
        application.update_queue.put(update)
        return 'ok'


group_message_counts = {}

# 启用日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


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

    # 检查是否在话题模式下
    if update.message.message_thread_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='请选择一个选项:',
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id)
    else:
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


# 删除消息
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


# 处理机器人加入的群组
async def handle_chat_member(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.chat_member.chat
    new_status = update.chat_member.new_chat_member.status
    if new_status == "member":
        chat_id = chat.id
        if chat_id not in group_message_counts:
            group_message_counts[chat_id] = {}
        logger.info(f"Bot added to group {chat.title} (id: {chat_id})")


# 每小时更新统计信息
def send_hourly_statistics(context):
    while True:
        now = datetime.now(pytz.timezone('Asia/Shanghai'))
        if 11 <= now.hour <= 23:
            for chat_id, user_data in group_message_counts.items():
                sorted_users = sorted(user_data.items(),
                                      key=lambda x: x[1]["count"],
                                      reverse=True)
                top_10_users = sorted_users[:10]

                if top_10_users:
                    message = "当前说话最大声的是：\n"
                    for i, (user_id, data) in enumerate(top_10_users, 1):
                        message += f"{i}. {data['name']} @{data['username']}  {data['count']}条\n"
                    message += "\n多发言有机会获得由吐司推荐榜单提供的优惠券哦！"

                    context.bot.send_message(chat_id=chat_id, text=message)

        time.sleep(3600)


# 发送最终统计信息
def send_final_statistics(context):
    while True:
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

                    context.bot.send_message(chat_id=chat_id, text=message)

                    # 延时24小时后取消置顶
                    time.sleep(86400)
                    context.bot.unpin_chat_message(
                        chat_id,
                        context.bot.get_chat(
                            chat_id).pinned_message.message_id)

                # 发送完统计消息后清除统计信息
                group_message_counts[chat_id].clear()

        time.sleep(1)


# 每天午夜清除统计信息
def clear_statistics(context):
    while True:
        now = datetime.now(pytz.timezone('Asia/Shanghai'))
        if now.hour == 0 and now.minute == 0:
            # 任务已经在 send_final_statistics 中完成
            pass

        time.sleep(1)


# 启动定时任务线程
def start_statistics_thread(context):
    threading.Thread(target=send_hourly_statistics,
                     args=(context, ),
                     daemon=True).start()
    threading.Thread(target=send_final_statistics,
                     args=(context, ),
                     daemon=True).start()
    threading.Thread(target=clear_statistics, args=(context, ),
                     daemon=True).start()


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.job_queue.run_repeating(send_hourly_statistics,
                                        interval=3600,
                                        first=0)
    application.job_queue.run_daily(clear_statistics,
                                    time=dt_time(
                                        0,
                                        0,
                                        tzinfo=pytz.timezone('Asia/Shanghai')))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(
        ChatMemberHandler(handle_chat_member,
                          ChatMemberHandler.MY_CHAT_MEMBER))
    threading.Thread(target=run_web_server).start()
    application.run_polling()

    # Set the webhook
    replit_url = f"https://<YOUR-REPLIT-URL>/webhook"
    application.bot.set_webhook(replit_url)

    application.run_polling()


if __name__ == "__main__":
    main()
