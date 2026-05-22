from telegram import Update
from telegram.ext import ContextTypes
import db, screens
from keyboards import ik
from config import PASS_MIN, PASS_MAX, ADMIN_HANDLE, OWNER_BALANCE, RESET_USE_MIDDLEWARE, RESET_MAX_TOTAL, RESET_COOLDOWN_H

def _login(ctx):  return ctx.user_data.get('login')
def _owner(ctx):  return bool(ctx.user_data.get('is_owner'))

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aw   = ctx.user_data.get('aw')
    text = update.message.text.strip()
    lgn  = _login(ctx)
    own  = _owner(ctx)
    if not lgn: return

    if aw == 'key_text':
        kt_id = ctx.user_data.get('kt_id')
        if kt_id:
            db.add_key(kt_id, text)
            await update.message.reply_text("✅ Added keys: 1\n📝 Send keys, one by one:")
        return

    elif aw == 'status_text':
        pos_id = ctx.user_data.get('pos_id')
        db.set_position_status(pos_id, text)
        await update.message.reply_text("✅ Status updated!")
        ctx.user_data['aw'] = None
        await screens.show_pos_detail(update.message, pos_id, own)

    elif aw == 'cat_name':
        ok = db.create_category(text)
        if not ok:
            await update.message.reply_text(f"❌ Category '{text}' <b>already exists</b>!")
            return
        cat = db.q1("SELECT id FROM categories WHERE name=?", (text,))
        if cat:
            ctx.user_data['cat_id']   = cat['id']
            ctx.user_data['cat_name'] = text
        ctx.user_data['aw'] = 'pos_name'
        await update.message.reply_text(
            "📝 Type position name:",
            reply_markup=ik([[("❌ Cancel", f"GO_POS_{ctx.user_data['cat_id']}")]])
        )

    elif aw == 'pos_name':
        cat_id = ctx.user_data.get('cat_id')
        db.create_position(cat_id, text)
        pos = db.q1("SELECT id FROM positions WHERE cat_id=? AND name=? ORDER BY id DESC LIMIT 1", (cat_id, text))
        if pos:
            ctx.user_data['pos_id'] = pos['id']
        ctx.user_data['aw'] = None
        await screens.show_pos_detail(update.message, ctx.user_data['pos_id'], own)

    elif aw == 'kt_name':
        ctx.user_data['new_kt_name'] = text
        ctx.user_data['aw']          = 'kt_price'
        await update.message.reply_text("📝 Type price for key:")

    elif aw == 'kt_price':
        try:
            price = float(text); assert price >= 0
        except Exception:
            await update.message.reply_text("❌ Incorrect format. Input price:")
            return
        pos_id = ctx.user_data.get('pos_id')
        name   = ctx.user_data.get('new_kt_name', 'Key')
        kt_id  = db.create_key_type(pos_id, name, price)
        ctx.user_data['kt_id'] = kt_id
        ctx.user_data['aw']    = 'key_text'
        await update.message.reply_text(
            "📝 Send keys, one by one:\n\n/done — finish",
            reply_markup=ik([[("❌ Cancel", f"GO_KT_{pos_id}")]])
        )

    elif aw == 'price_edit':
        try:
            price = float(text); assert price >= 0
        except Exception:
            await update.message.reply_text("❌ Incorrect format. Input price:"); return
        kt_id = ctx.user_data.get('kt_id')
        db.update_key_price(kt_id, price)
        await update.message.reply_text(
            f"✅ <b>Price</b> updated: <code>{price:.2f}$</code>",
            parse_mode="HTML"
        )
        ctx.user_data['aw'] = None
        await screens.show_kt_detail(update.message, kt_id, ctx.user_data.get('cat_name', ''), own)

    elif aw == 'price_init':
        try:
            price = float(text); assert price >= 0
        except Exception:
            await update.message.reply_text("❌ Incorrect format. Input price:"); return
        kt_id = ctx.user_data.get('kt_id')
        db.update_key_init_price(kt_id, price)
        await update.message.reply_text(
            f"✅ <b>Initial price</b> updated: <code>{price:.2f}$</code>",
            parse_mode="HTML"
        )
        ctx.user_data['aw'] = None
        await screens.show_kt_detail(update.message, kt_id, ctx.user_data.get('cat_name', ''), own)

    elif aw == 'acc_login':
        ctx.user_data['new_acc_login'] = text
        ctx.user_data['aw']            = 'acc_pass'
        await update.message.reply_text("🔒 Type password for account:")

    elif aw == 'acc_pass':
        if len(text) < PASS_MIN or len(text) > PASS_MAX:
            await update.message.reply_text(
                f"❌ The password must be between {PASS_MIN} and {PASS_MAX} characters long! Please try again."
            ); return
        new_login = ctx.user_data.get('new_acc_login', '')
        ok = db.create_account(new_login, text)
        if ok:
            await update.message.reply_text(
                f"✅ <b>Account Created</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 Login:     <code>{new_login}</code>\n"
                f"🔑 Password:  <code>{text}</code>\n"
                f"💳 Balance:   <code>0.00$</code>\n\n"
                f"<i>👆 Tap to copy credentials</i>",
                parse_mode="HTML",
                reply_markup=ik([
                    [("📧 Send credentials", f"ACC_CREDS_{new_login}"),
                     ("⬅️ Back to accounts",  "GO_ACCOUNTS")],
                ])
            )
        else:
            await update.message.reply_text(f"❌ Login '{new_login}' <b>already exists</b>!")
        ctx.user_data['aw'] = None

    elif aw == 'add_balance':
        try:
            amount = float(text); assert amount > 0
        except Exception:
            await update.message.reply_text("❌ Enter a valid positive number:"); return
        sel = ctx.user_data.get('sel_acc')
        db.add_balance(sel, amount)
        db.add_topup(sel, amount, "Admin top-up")
        acc = db.get_account(sel)

        await update.message.reply_text(
            f"✅ <b>Top-up Successful</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Account:        <code>{sel}</code>\n"
            f"➕ Amount added:   <code>{amount:.2f}$</code>\n"
            f"💳 New balance:    <code>{acc['balance']:.2f}$</code>",
            parse_mode="HTML"
        )

        if acc.get('tg_id'):
            try:
                from datetime import datetime
                now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                await update.get_bot().send_message(
                    acc['tg_id'],
                    f"💰 <b>Balance Topped Up!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎉 Your account has received a top-up.\n\n"
                    f"➕ Amount:       <code>{amount:.2f}$</code>\n"
                    f"💳 New balance:  <code>{acc['balance']:.2f}$</code>\n"
                    f"🕐 Date:          {now}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛍 Use 🛍️ <b>Buy keys</b> to start shopping!",
                    parse_mode="HTML"
                )
            except Exception:
                pass

        ctx.user_data['aw'] = None
        await screens.show_acc_detail(update.message, sel)

    elif aw == 'buy_qty':
        try:
            qty = int(text); assert qty > 0 and qty <= 100
        except Exception:
            await update.message.reply_text("❌ Enter a valid number (1-100):"); return
        kt_id = ctx.user_data.get('buy_kt_id')
        ctx.user_data['aw'] = None
        from handlers.callbacks import _do_buy

        class FakeQ:
            def __init__(self, m, b):
                self.message = m
                self.bot = b
            async def answer(self, *args, **kwargs):
                pass

        await _do_buy(FakeQ(update.message, update.get_bot()), ctx, kt_id, qty=qty)

    elif aw == 'mpurch_search':
        ctx.user_data['aw'] = None
        purchases = db.get_all_purchases(500)
        results = [p for p in purchases if p['key_val'] and text.lower() in p['key_val'].lower()]
        if not results:
            await update.message.reply_text("❌ <b>No results found</b>.")
            return
        rows = []
        for p in results[:20]:
            key_short = p['key_val']
            cat_pos = f"{p['cat_name']}/{p['pos_name']}"
            label = f"{key_short} ({cat_pos})"
            if len(label) > 40: label = label[:37] + "..."
            rows.append([(label, f"MPURCH_VIEW_{p['id']}")])
        rows.append([("⬅️ Go back", "MANAGE_PURCH")])
        await update.message.reply_text(
            f"🔍 Results for '{text}':",
            reply_markup=ik(rows)
        )

    elif aw == 'bc_collect':
        items = ctx.user_data.get('bc_items', [])
        items.append({'type': 'text', 'c': text})
        ctx.user_data['bc_items'] = items
        ctx.user_data['aw']       = None
        await update.message.reply_text(
            f"✅ Added! Total items: {len(items)}",
            reply_markup=ik([
                [("➕ Add more", "BC_ADD"), ("👁️ Preview", "BC_PREV")],
                [("🚀 Send now", "BC_SEND"), ("❌ Cancel",  "BC_CANCEL")],
                [(f"🧺 Items: {len(items)}", "BC_COUNT")],
            ])
        )

async def file_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aw  = ctx.user_data.get('aw')
    lgn = _login(ctx)
    if not lgn: return
    msg = update.message

    if aw == 'file_upload':
        pos_id = ctx.user_data.get('pos_id')
        if msg.document:
            db.add_file(pos_id, msg.document.file_id, msg.document.file_name or "")
            await msg.reply_text("✅ File added. Send more or /done")
        else:
            await msg.reply_text("Please send a document file, or /done to finish.")

    elif aw == 'bc_collect':
        items = ctx.user_data.get('bc_items', [])
        if   msg.photo:    items.append({'type':'photo', 'f': msg.photo[-1].file_id, 'cap': msg.caption or ''})
        elif msg.document: items.append({'type':'doc',   'f': msg.document.file_id,  'cap': msg.caption or ''})
        elif msg.video:    items.append({'type':'video', 'f': msg.video.file_id,     'cap': msg.caption or ''})
        ctx.user_data['bc_items'] = items
        ctx.user_data['aw']       = None
        await msg.reply_text(
            f"✅ Added! Total items: {len(items)}",
            reply_markup=ik([
                [("➕ Add more", "BC_ADD"), ("👁️ Preview", "BC_PREV")],
                [("🚀 Send now", "BC_SEND"), ("❌ Cancel",  "BC_CANCEL")],
                [(f"🧺 Items: {len(items)}", "BC_COUNT")],
            ])
        )

async def done_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aw  = ctx.user_data.get('aw')
    own = _owner(ctx)
    if aw == 'key_text':
        ctx.user_data['aw'] = None
        await update.message.reply_text("✅ <b>Upload complete</b>.")
        kt_id = ctx.user_data.get('kt_id')
        if kt_id:
            await screens.show_kt_detail(update.message, kt_id, ctx.user_data.get('cat_name', ''), own)
    elif aw == 'file_upload':
        ctx.user_data['aw'] = None
        await update.message.reply_text("✅ <b>Upload complete</b>.")
        pos_id = ctx.user_data.get('pos_id')
        if pos_id:
            await screens.show_pos_detail(update.message, pos_id, own)
    else:
        await update.message.reply_text("✅ Done.")

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['aw'] = None
    await update.message.reply_text("❌ Cancelled.")

async def reset_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timedelta
    lgn = _login(ctx)
    if not lgn:
        await update.message.reply_text(
            f"❌ <b>Access Denied</b>, please /login\n"
            f"For access or support, please contact admin → {ADMIN_HANDLE}",
            parse_mode="HTML"
        ); return

    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: /reset <KEY>"); return

    key_val = args[0].strip()
    own     = _owner(ctx)

    if not own:
        user_keys = [p['key_val'] for p in db.get_purchases(lgn) if p['key_val']]
        if key_val not in user_keys:
            await update.message.reply_text("❗ Error: <b>Not enough permissions</b>", parse_mode="HTML"); return

    total = db.count_resets(key_val)
    if total >= RESET_MAX_TOTAL:
        await update.message.reply_text(
            f"❌ <b>Reset limit reached</b>: {total}/{RESET_MAX_TOTAL}. "
            f"This key can no longer be reset.",
            parse_mode="HTML"
        ); return

    last = db.last_reset_time(key_val)
    if last:
        last_dt = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() - last_dt < timedelta(hours=RESET_COOLDOWN_H):
            await update.message.reply_text(
                f"❗ Error: Key <b>reset limit exceeded</b>. "
                f"You can only reset device on this key once every {RESET_COOLDOWN_H} hours.",
                parse_mode="HTML"
            ); return

    if RESET_USE_MIDDLEWARE:
        from middleware import send_reset_to_external

        wait_msg = await update.message.reply_text(
            f"⏳ <b>Processing your reset...</b>\n🔑 <code>{key_val}</code>",
            parse_mode="HTML"
        )

        response = await send_reset_to_external(key_val)

        try:
            await wait_msg.delete()
        except Exception:
            pass

        if response is None:
            await update.message.reply_text(
                f"⚠️ <b>Request Timeout</b>\n\n"
                f"🔑 Key: <code>{key_val}</code>\n"
                f"The external bot didn't respond. Please try again or contact {ADMIN_HANDLE}",
                parse_mode="HTML"
            )
            return

        db.add_reset(key_val, lgn)
        await update.message.reply_text(response)
        return

    db.add_reset(key_val, lgn)
    await update.message.reply_text(
        f"✅ <b>Key reset successfully</b>! ({total+1}/{RESET_MAX_TOTAL} resets used)",
        parse_mode="HTML"
    )
