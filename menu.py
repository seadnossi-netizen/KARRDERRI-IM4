from telegram import Update
from telegram.ext import ContextTypes
import db, screens
from keyboards import ik, login_kb
from config import ADMIN_HANDLE, OWNER_BALANCE

def _denied():
    return (f"❌ <b>Access Denied</b>, please /login\n"
            f"You don't have permission to use this feature.\n"
            f"For access or support, please contact admin → {ADMIN_HANDLE}")

def _login(ctx):  return ctx.user_data.get('login')
def _owner(ctx):  return bool(ctx.user_data.get('is_owner'))

async def buy_keys(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _login(ctx):
        await update.message.reply_text(_denied(), reply_markup=login_kb()); return
    await screens.show_cats(update.message, _owner(ctx))

async def account(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _login(ctx):
        await update.message.reply_text(_denied(), reply_markup=login_kb()); return
    login = _login(ctx)
    acc   = db.get_account(login)
    bal   = OWNER_BALANCE if _owner(ctx) else acc['balance']
    await update.message.reply_text(
        f"👤 Your account:\n"
        f"- Login: <code>{acc['login']}</code>\n"
        f"- Balance: <code>{bal:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=ik([
            [("📜 Purchase History", "MY_PURCH"),
             ("💳 Top-up History",   "MY_TOPUPS")],
        ])
    )

async def manage(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _login(ctx):
        await update.message.reply_text(_denied(), reply_markup=login_kb()); return
    if not _owner(ctx):
        await update.message.reply_text(_denied()); return
    await screens.show_manage(update.message)

async def stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _login(ctx):
        await update.message.reply_text(_denied(), reply_markup=login_kb()); return
    if not _owner(ctx):
        await update.message.reply_text(_denied()); return
    data = db.get_full_stock()
    if not data:
        await update.message.reply_text("📦 No stock data."); return
    from collections import defaultdict
    by_cat = defaultdict(list)
    for item in data:
        by_cat[item['cat']].append(item)
    pages = list(by_cat.values())
    total = len(pages)
    for i, items in enumerate(pages):
        msg = "📦 Current stock:\n\n"
        for item in items:
            msg += f"🛒 {item['pos']}\n"
            for kt in item['key_types']:
                icon = "✅" if kt['count'] > 0 else "❌"
                msg += f"• {kt['name']}: {kt['count']} {icon}\n"
            if item['files'] > 0:
                msg += f"• Files: {item['files']} ✅\n"
            msg += "\n"
        await update.message.reply_text(msg.strip() + f"\n[{i+1}/{total}]")

async def statistics(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _login(ctx):
        await update.message.reply_text(_denied(), reply_markup=login_kb()); return
    if not _owner(ctx):
        await update.message.reply_text(_denied()); return
    await update.message.reply_text(
        "📈 Statistics",
        reply_markup=ik([
            [("📅 Daily",      "STATS_DAY"),
             ("📅 Week",       "STATS_WEEK"),
             ("📅 Month",      "STATS_MONTH")],
            [("TOP",           "STATS_TOP"),
             ("💰 <b>Net Profit</b>", "STATS_PROFIT")],
        ])
    )
