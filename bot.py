import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ChatMemberHandler, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

WHISPER_DB = {}
counter = 0
ALLOWED_GROUP = "@yapholics"

async def check_group_access(update: Update) -> bool:
    chat = update.effective_chat
    if chat.type == "private":
        return True
    group_identifier = chat.username or str(chat.id)
    if f"@{group_identifier}" != ALLOWED_GROUP and str(chat.id) != ALLOWED_GROUP:
        return False
    return True

async def auto_leave_unauthorized_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result:
        new_status = result.new_chat_member.status
        chat = result.chat
        if new_status in ["member", "administrator"]:
            group_identifier = chat.username or str(chat.id)
            if f"@{group_identifier}" != ALLOWED_GROUP and str(chat.id) != ALLOWED_GROUP:
                try:
                    await context.bot.leave_chat(chat.id)
                except Exception:
                    pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update):
        return
    await update.message.reply_text("Whisper Bot Active.\n\nUsage:\n@YapholicsWhisperBot @username message")

async def handle_whisper_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_access(update):
        return

    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()
    bot_username = "@YapholicsWhisperBot"
    
    if text.startswith(bot_username):
        parts = text.split(" ", 2)
        if len(parts) < 3:
            await message.reply_text("Error: Format is @YapholicsWhisperBot @username message")
            return
        target_username = parts[1]
        whisper_text = parts[2]
    elif text.startswith("/whisper"):
        parts = text.split(" ", 2)
        if len(parts) < 3:
            await message.reply_text("Error: Format is /whisper @username message")
            return
        target_username = parts[1]
        whisper_text = parts[2]
    else:
        return

    if not target_username.startswith("@"):
        await message.reply_text("Error: Please specify target username starting with @")
        return

    global counter
    counter += 1
    whisper_key = f"whisper_{counter}"
    
    WHISPER_DB[whisper_key] = {
        "target_username": target_username.lower(),
        "target_name": target_username,
        "text": whisper_text
    }

    keyboard = [[InlineKeyboardButton("Read Whisper", callback_data=whisper_key)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    public_text = f"Whisper message for {target_username}."
    await message.reply_text(public_text, reply_markup=reply_markup)

    try:
        await message.delete()
    except Exception:
        pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_key = query.data
    if data_key not in WHISPER_DB:
        await query.answer("Error: Whisper has expired or does not exist.", show_alert=True)
        return

    whisper_data = WHISPER_DB[data_key]
    user_username = query.from_user.username
    target_username = whisper_data["target_username"].lstrip("@")
    target_name = whisper_data["target_name"]
    whisper_text = whisper_data["text"]

    if not user_username or user_username.lower() != target_username.lower():
        await query.answer("This whisper is not for you.", show_alert=True)
        return

    await query.answer(f"Whisper content:\n\n{whisper_text}", show_alert=True)

    new_public_text = f"Whisper read by {target_name}."
    try:
        await query.edit_message_text(text=new_public_text, reply_markup=None)
    except Exception:
        pass

    del WHISPER_DB[data_key]

def main():
    TOKEN = "8625381734:AAEQL6MsW3uw-qB1J_fLPhpPnCt1DxH1Qn4"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_whisper_text))
    app.add_handler(ChatMemberHandler(auto_leave_unauthorized_groups, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
