from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import db
from keyboards import main_kb, login_kb, ik
from config import ADMIN_HANDLE, OWNER_BALANCE

WAIT_CREDS = 10

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    login = ctx.user_data.get('login')

    if not login:
        from db import qa
        rows = qa("SELECT * FROM accounts WHERE tg_id=? LIMIT 1", (tg_id,))
        if rows:
            acc = rows[0]
            ctx.user_data['login']    = acc['login']
            ctx.user_data['is_owner'] = bool(acc['is_owner'])
            login = acc['login']

    if login and db.get_account(login):
        await update.message.reply_text(
            "👋 Hello, welcome to panel!",
            reply_markup=main_kb(ctx.user_data.get('is_owner', False))
        )
    else:
        ctx.user_data.clear()
        await update.message.reply_text(
            f"❌ <b>Access Denied</b>, please /login\n"
            f"You don't have permission to use this feature.\n"
            f"For access or support, please contact admin → {ADMIN_HANDLE}",
            reply_markup=login_kb()
        )
    return ConversationHandler.END

async def login_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 Enter the credentials provided by the administrator in the following format:\n\n"
        "LOGIN\nPASSWORD",
        reply_markup=ik([
            [("❌ Cancel", "LOGIN_BACK")]
        ])
    )
    return WAIT_CREDS

async def receive_creds(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.strip().split()
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ <b>Invalid format</b>! Please try again.\n\nLOGIN\nPASSWORD",
            reply_markup=ik([[("❌ Cancel", "LOGIN_BACK")]])
        )
        return WAIT_CREDS

    login, password = parts[0], parts[1]
    acc = db.get_account_by_creds(login, password)
    if not acc:
        await update.message.reply_text(
            "❌ <b>Invalid credentials</b>! Please try again.",
            reply_markup=ik([[("❌ Cancel", "LOGIN_BACK")]])
        )
        return WAIT_CREDS

    ctx.user_data['login']    = login
    ctx.user_data['is_owner'] = bool(acc['is_owner'])
    db.set_tg_id(login, update.effective_user.id)

    await update.message.reply_text(
        "🔓 You have been <b>successfully authorized</b>!",
        reply_markup=main_kb(bool(acc['is_owner']))
    )
    return ConversationHandler.END

async def logout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "🔓 You have <b>successfully logged out</b>!\n"
        "To log in again, use the /login command",
        reply_markup=login_kb()
    )
    return ConversationHandler.END

STATES = {
    WAIT_CREDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_creds)]
}
