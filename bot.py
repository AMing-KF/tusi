import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, ContextTypes, filters

# 获取机器人TOKEN
TOKEN = os.getenv('TOKEN')

# 设置日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


# /start命令处理函数，发送自定义键盘
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_keyboard(update, context, send_message=True)


# 发送自定义键盘的函数
async def send_keyboard(update: Update,
                        context: ContextTypes.DEFAULT_TYPE,
                        send_message=True) -> None:
    keyboard = [['查看资源', '吐司推荐'], ['查看报告', '提交报告'], ['抽奖活动', '开通会员'],
                ['囡囡点此免费认证上榜']]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)

    if send_message:
        await update.message.reply_text('请选择一个选项:', reply_markup=reply_markup)


# 删除消息的函数，根据 response_type 删除特定消息
async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    response_type = job.data.get('response_type')
    if response_type in {'bot_response',
                         'user_text'}:  # 确保只删除标志为 bot_response 和 user_text 的消息
        try:
            await context.bot.delete_message(chat_id=job.data['chat_id'],
                                             message_id=job.data['message_id'])
            logger.info(
                f"Deleted {response_type} message with message_id {job.data['message_id']}"
            )
        except Exception as e:
            logger.error(f"无法删除消息: {e}")


# 处理自定义键盘按钮点击事件的函数
async def handle_message(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    sent_message = None

    logger.info(f"Received message: {text}")

    # 如果消息是通过点击自定义键盘按钮生成的，将其计划删除
    valid_texts = [
        '查看资源', '吐司推荐', '查看报告', '提交报告', '抽奖活动', '开通会员', '囡囡点此免费认证上榜'
    ]
    if text in valid_texts:
        context.job_queue.run_once(delete_message,
                                   20,
                                   data={
                                       'chat_id': chat_id,
                                       'message_id': message_id,
                                       'response_type': 'user_text'
                                   })
        logger.info(
            f"Scheduled user text message deletion for message_id {message_id}"
        )

    # 处理特定的按钮点击事件并发送相应的消息
    def create_reply_markup(buttons):
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(name, url=url) for name, url in button_row]
             for button_row in buttons])

    responses = {
        '查看资源': {
            'text':
            '吐司.正在努力收录全市资源！争取将客栈仓库塞满！',
            'buttons': [[("罗湖区", "https://t.me/lmkzgather/9"),
                         ("福田区", "https://t.me/lmkzgather/5"),
                         ("南山区", "https://t.me/lmkzgather/7")],
                        [("龙岗区", "https://t.me/lmkzgather/13"),
                         ("宝安区", "https://t.me/szpages/2767"),
                         ("龙华区", "https://t.me/lmkzgather/15")],
                        [("抽奖活动专区", "https://t.me/lmkzgather/21")],
                        [("电报注册/解禁/科学上网", "https://t.me/lmkzgather/21")]]
        },
        '吐司推荐': {
            'text': '推荐的都是经过客栈认证的老师！',
            'buttons': [[("吐司推荐榜单", "https://t.me/tusisz")]]
        },
        '查看报告': {
            'text': '虽然审核很严格，但还是要自辩真假哦！',
            'buttons': [[("龙门报告", "https://t.me/szhyChat")]]
        },
        '提交报告': {
            'text': '提交报告需要提供预约记录哦！',
            'buttons': [[("提交报告", "https://t.me/lmkzgather/1/36")]]
        },
        '抽奖活动': {
            'text': '万一中奖了呢！',
            'buttons': [[("抽奖活动专区", "https://t.me/lmkzgather/21")]]
        },
        '开通会员': {
            'text': '可使用支付宝、微信和USDT进行支付，并在24小时内自动到账。',
            'buttons': [[("自助开启电报会员", "https://t.me/TPGift_BOT")]]
        },
        '囡囡点此免费认证上榜': {
            'text': '让我们一起互相成就吧！',
            'buttons': [[("感谢你的支持", "https://t.me/lmkzgather/1/35")]]
        }
    }

    if text in responses:
        reply_markup = create_reply_markup(responses[text]['buttons'])
        sent_message = await update.message.reply_text(
            responses[text]['text'], reply_markup=reply_markup)
        # 计划删除由机器人响应生成的消息
        context.job_queue.run_once(delete_message,
                                   15,
                                   data={
                                       'chat_id': chat_id,
                                       'message_id': sent_message.message_id,
                                       'response_type': 'bot_response'
                                   })
        logger.info(
            f"Scheduled bot response message deletion for message_id {sent_message.message_id}"
        )


# 处理新成员加入群组事件的函数，发送自定义键盘但不发送消息
async def new_member(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("New member joined")
    await send_keyboard(update, context, send_message=False)


# 主函数，设置Telegram应用和处理程序
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(
        ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER))

    application.run_polling()


if __name__ == '__main__':
    main()
