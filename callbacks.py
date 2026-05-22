from telegram import Update
from telegram.ext import ContextTypes
import db, screens
from keyboards import ik, login_kb
from config import ADMIN_HANDLE, PASS_MIN, PASS_MAX, OWNER_BALANCE

def _login(ctx):  return ctx.user_data.get('login')
def _owner(ctx):  return bool(ctx.user_data.get('is_owner'))

async def _no_perm(q):
    await q.answer("❌ <b>Access Denied</b>", show_alert=True)

async def router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = update.callback_query
    await q.answer()
    d   = q.data
    lgn = _login(ctx)
    own = _owner(ctx)

    if d == "LOGIN_BACK":
        await q.message.edit_text(
            f"❌ <b>Access Denied</b>, please /login\n"
            f"You don't have permission to use this feature.\n"
            f"For access or support, please contact admin → {ADMIN_HANDLE}",
        )
        return

    if not lgn:
        await q.message.reply_text(
            f"❌ <b>Access Denied</b>, please /login\n"
            f"For access or support, please contact admin → {ADMIN_HANDLE}"
        )
        return

    if d == "GO_CATS":
        await screens.show_cats(q, own)

    elif d.startswith("GO_POS_"):
        cat_id = int(d[7:])
        ctx.user_data['cat_id'] = cat_id
        await screens.show_positions(q, cat_id, own)

    elif d.startswith("GO_KT_"):
        pos_id = int(d[6:])
        ctx.user_data['pos_id'] = pos_id
        await screens.show_pos_detail(q, pos_id, own)

    elif d == "GO_ACCOUNTS":
        if not own: await _no_perm(q); return
        await screens.show_accounts(q)

    elif d == "GO_MANAGE_BACK":
        if not own: await _no_perm(q); return
        await screens.show_manage(q)

    elif d == "GO_MANAGE":
        if not own: await _no_perm(q); return
        await screens.show_manage(q)

    elif d == "CAT_ADD":
        if not own: await _no_perm(q); return
        ctx.user_data['aw']      = 'cat_name'
        ctx.user_data['aw_msg']  = q.message.message_id
        await q.message.edit_text(
            "📝 New name for category:",
            reply_markup=ik([[("❌ Cancel", "GO_CATS")]])
        )

    elif d.startswith("CAT_DEL_"):
        if not own: await _no_perm(q); return
        db.delete_category(int(d[8:]))
        await screens.show_cats(q, own)

    elif d.startswith("CAT_"):
        cat_id = int(d[4:])
        ctx.user_data['cat_id'] = cat_id
        cat = db.get_category(cat_id)
        if cat: ctx.user_data['cat_name'] = cat['name']
        await screens.show_positions(q, cat_id, own)

    elif d.startswith("POS_ADD_"):
        if not own: await _no_perm(q); return
        cat_id = int(d[8:])
        ctx.user_data['cat_id']  = cat_id
        ctx.user_data['aw']      = 'pos_name'
        ctx.user_data['aw_msg']  = q.message.message_id
        await q.message.edit_text(
            "📝 Type position name:",
            reply_markup=ik([[("❌ Cancel", f"GO_POS_{cat_id}")]])
        )

    elif d.startswith("POS_DEL_"):
        if not own: await _no_perm(q); return
        pos_id = int(d[8:])
        pos    = db.get_position(pos_id)
        cat_id = pos['cat_id'] if pos else ctx.user_data.get('cat_id', 0)
        db.delete_position(pos_id)
        await screens.show_positions(q, cat_id, own)

    elif d.startswith("POS_"):
        pos_id = int(d[4:])
        ctx.user_data['pos_id'] = pos_id
        pos = db.get_position(pos_id)
        if pos: ctx.user_data['cat_id'] = pos['cat_id']
        await screens.show_pos_detail(q, pos_id, own)

    elif d.startswith("KT_ADD_"):
        if not own: await _no_perm(q); return
        pos_id = int(d[7:])
        ctx.user_data['pos_id'] = pos_id
        ctx.user_data['aw']     = 'kt_name'
        ctx.user_data['aw_msg'] = q.message.message_id
        await q.message.edit_text(
            "📝 Type key type name:",
            reply_markup=ik([[("❌ Cancel", f"GO_KT_{pos_id}")]])
        )

    elif d.startswith("KT_DEL_"):
        if not own: await _no_perm(q); return
        kt_id = int(d[7:])
        kt    = db.get_key_type(kt_id)
        pos_id = kt['pos_id'] if kt else ctx.user_data.get('pos_id', 0)
        db.delete_key_type(kt_id)
        await screens.show_pos_detail(q, pos_id, own)

    elif d.startswith("KT_"):
        kt_id = int(d[3:])
        kt    = db.get_key_type(kt_id)
        if kt:
            ctx.user_data['kt_id']  = kt_id
            ctx.user_data['pos_id'] = kt['pos_id']
        await screens.show_kt_detail(q, kt_id, ctx.user_data.get('cat_name', ''), own)

    elif d.startswith("BUY_"):
        kt_id = int(d[4:])
        kt    = db.get_key_type(kt_id)
        if not kt:
            await q.answer("❌ <b>Key type not found</b>.", show_alert=True); return
        cnt = db.count_stock(kt_id)
        if cnt == 0:
            await q.answer("❌ <b><b>Out of stock</b>!</b>", show_alert=True); return
        pos = db.get_position(kt['pos_id'])
        await q.message.edit_text(
            f"❓ Buy key in {pos['name'] if pos else ''} ({kt['name']})?",
            reply_markup=ik([
                [("Buy one", f"BUY1_{kt_id}"), ("Buy multiple", f"BUYM_{kt_id}")],
                [("⬅️ Go back", f"KT_{kt_id}")],
            ])
        )

    elif d.startswith("BUY1_"):
        kt_id = int(d[5:])
        await _do_buy(q, ctx, kt_id, qty=1)

    elif d.startswith("BUYM_"):
        kt_id = int(d[5:])
        ctx.user_data['buy_kt_id'] = kt_id
        ctx.user_data['aw']        = 'buy_qty'
        await q.message.edit_text(
            "Type, how much keys u want to buy (number):",
            reply_markup=ik([[("❌ Cancel", f"KT_{kt_id}")]])
        )

    elif d.startswith("FILE_ADD_"):
        if not own: await _no_perm(q); return
        pos_id = int(d[9:])
        ctx.user_data['pos_id'] = pos_id
        ctx.user_data['aw']     = 'file_upload'
        await q.message.edit_text(
            "📨 Send files for this position. Send one by one. When done, type /done",
            reply_markup=ik([[("❌ Cancel", f"GO_KT_{pos_id}")]])
        )

    elif d.startswith("FILE_GET_"):
        pos_id = int(d[9:])
        files  = db.get_all_files(pos_id)
        if not files:
            await q.message.reply_text("❌ No files found for this item.")
        else:
            for f in files:
                try: await q.message.reply_document(f['file_id'])
                except: await q.message.reply_text(f"File: {f['file_id']}")

    elif d.startswith("STS_EDIT_"):
        if not own: await _no_perm(q); return
        pos_id = int(d[9:])
        ctx.user_data['pos_id'] = pos_id
        ctx.user_data['aw']     = 'status_text'
        await q.message.edit_text(
            "⚙️ Send new status for this position:",
            reply_markup=ik([[("❌ Cancel", f"GO_KT_{pos_id}")]])
        )

    elif d.startswith("STS_CHK_"):
        pos = db.get_position(int(d[8:]))
        if pos:
            await q.message.reply_text(f"🛡️ Current status: {pos['status']}")

    elif d.startswith("KEYS_ADD_"):
        if not own: await _no_perm(q); return
        kt_id = int(d[9:])
        ctx.user_data['kt_id'] = kt_id
        ctx.user_data['aw']    = 'key_text'
        await q.message.edit_text(
            "📝 Send keys, one by one:\n\n/done — finish",
            reply_markup=ik([[("❌ Cancel", f"GO_KT_{db.get_key_type(kt_id)['pos_id'] if db.get_key_type(kt_id) else 0}")]])
        )

    elif d.startswith("KEYS_CLR_"):
        if not own: await _no_perm(q); return
        kt_id = int(d[9:])
        db.clear_keys(kt_id)
        await screens.show_kt_detail(q, kt_id, ctx.user_data.get('cat_name', ''), own)

    elif d.startswith("PRICE_EDIT_"):
        if not own: await _no_perm(q); return
        kt_id = int(d[11:])
        ctx.user_data['kt_id'] = kt_id
        ctx.user_data['aw']    = 'price_edit'
        await q.message.edit_text(
            "📝 Type new price:",
            reply_markup=ik([[("❌ Cancel", f"KT_{kt_id}")]])
        )

    elif d.startswith("PRICE_INIT_"):
        if not own: await _no_perm(q); return
        kt_id = int(d[11:])
        ctx.user_data['kt_id'] = kt_id
        ctx.user_data['aw']    = 'price_init'
        await q.message.edit_text(
            "💼 Enter <b>initial price</b> (ex: 2.5):",
            parse_mode="HTML",
            reply_markup=ik([[("❌ Cancel", f"KT_{kt_id}")]])
        )

    elif d == "MY_PURCH":
        purchases = db.get_purchases(lgn)
        if not purchases:
            await q.answer("❌ No purchases yet", show_alert=True); return
        ctx.user_data['purch_page'] = 0
        await _render_purch(q, ctx, lgn, 0)

    elif d.startswith("PURCH_PAGE_"):
        page = int(d[11:])
        ctx.user_data['purch_page'] = page
        await _render_purch(q, ctx, lgn, page)

    elif d == "MY_TOPUPS":
        topups = db.get_topups(lgn)
        if not topups:
            await q.answer("❌ No top-up history", show_alert=True); return
        ctx.user_data['topup_page'] = 0
        await _render_topup(q, ctx, lgn, 0)

    elif d.startswith("TOPUP_PAGE_"):
        page = int(d[11:])
        ctx.user_data['topup_page'] = page
        await _render_topup(q, ctx, lgn, page)

    elif d == "MY_BACK":
        acc = db.get_account(lgn)
        bal = OWNER_BALANCE if own else acc['balance']
        await q.message.edit_text(
            f"👤 Your account:\n"
            f"- Login: <code>{acc['login']}</code>\n"
            f"- Balance: <code>{bal:.2f}$</code>",
            parse_mode="HTML",
            reply_markup=ik([
                [("📜 Purchase History", "MY_PURCH"),
                 ("💳 Top-up History",   "MY_TOPUPS")],
            ])
        )

    elif d == "MANAGE_ACCS":
        if not own: await _no_perm(q); return
        await screens.show_accounts(q)

    elif d == "MANAGE_PURCH":
        if not own: await _no_perm(q); return
        ctx.user_data['manage_purch_page'] = 0
        await _render_manage_purch(q, ctx)

    elif d.startswith("MPURCH_PAGE_"):
        if not own: await _no_perm(q); return
        ctx.user_data['manage_purch_page'] = int(d[12:])
        await _render_manage_purch(q, ctx)

    elif d == "MPURCH_NOOP":
        pass

    elif d == "MPURCH_SEARCH":
        if not own: await _no_perm(q); return
        ctx.user_data['aw'] = 'mpurch_search'
        await q.message.edit_text(
            "🔍 Enter key to search:",
            reply_markup=ik([[("❌ Cancel", "MANAGE_PURCH")]])
        )

    elif d.startswith("MPURCH_VIEW_"):
        if not own: await _no_perm(q); return
        purch_id = int(d[12:])
        p = db.q1("SELECT * FROM purchases WHERE id=?", (purch_id,))
        if not p:
            await q.answer("Not found", show_alert=True); return
        date_str = p['created_at']
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception: pass
        txt = (
            f"📦🔑 Information about last purchases [page 1/1]\n\n"
            f"🧾 Purchase (x1)\n"
            f"🔑 Keys:\n• <code>{p['key_val'] or '—'}</code>\n"
            f"💰 Total: <code>{p['price']:.2f}$</code> ( 1 × {p['price']:.2f}$ )\n"
            f"📁 Category: {p['cat_name']}\n"
            f"📌 Position: {p['pos_name']}\n"
            f"👤 Account: <code>{p['login']}</code>\n"
            f"🕐 Date: {date_str}"
        )
        await q.message.edit_text(
            txt, parse_mode="HTML",
            reply_markup=ik([[("⬅️ Go back", "MANAGE_PURCH")]])
        )

    elif d == "MANAGE_BC":
        if not own: await _no_perm(q); return
        ctx.user_data['bc_items'] = []
        ctx.user_data['aw']       = 'bc_collect'
        await q.message.edit_text(
            "💬 <b>Broadcast</b>\n"
            "Send a message (text / photo / document / video).\n"
            "After each item I'll ask if you're ready to send.",
            reply_markup=ik([
                [("➕ Add more", "BC_ADD"), ("👁️ Preview", "BC_PREV")],
                [("🚀 Send now", "BC_SEND"), ("❌ Cancel",  "BC_CANCEL")],
                [(f"🧺 Items: 0", "BC_COUNT")],
            ])
        )

    elif d == "ACC_ADD":
        if not own: await _no_perm(q); return
        ctx.user_data['aw'] = 'acc_login'
        await q.message.edit_text(
            "🔒 Type login for new account:",
            reply_markup=ik([[("❌ Cancel", "GO_ACCOUNTS")]])
        )

    elif d.startswith("ACC_DETAIL_"):
        if not own: await _no_perm(q); return
        await screens.show_acc_detail(q, d[11:])

    elif d.startswith("ACC_ADDBAL_"):
        if not own: await _no_perm(q); return
        login = d[11:]
        ctx.user_data['sel_acc'] = login
        ctx.user_data['aw']      = 'add_balance'
        await q.message.edit_text(
            f"💰 Enter amount to add for {login}:",
            reply_markup=ik([[("❌ Cancel", f"ACC_DETAIL_{login}")]])
        )

    elif d.startswith("ACC_RSTBAL_"):
        if not own: await _no_perm(q); return
        login = d[11:]
        db.reset_balance(login)
        await screens.show_acc_detail(q, login)

    elif d.startswith("ACC_PURCH_"):
        if not own: await _no_perm(q); return
        login = d[10:]
        purchases = db.get_purchases(login)
        if not purchases:
            await q.message.edit_text(
                f"No purchases for {login}.",
                reply_markup=ik([[("⬅️ Back", f"ACC_DETAIL_{login}")]])
            ); return
        msg = f"📦 Purchases of <code>{login}</code>:\n\n"
        for p in purchases[:15]:
            msg += (f"🧾 {p['pos_name']} ({p['kt_name']}) — <code>{p['price']:.2f}$</code>\n"
                    f"🔑 <code>{p['key_val'] or 'file'}</code>\n"
                    f"🕐 {p['created_at']}\n───\n")
        await q.message.edit_text(
            msg, parse_mode="HTML",
            reply_markup=ik([
                [("⬅️ Back", f"ACC_DETAIL_{login}"),
                 (f"📤 Send all keys ({len(purchases)})", f"ACC_KEYS_{login}")],
            ])
        )

    elif d.startswith("ACC_KEYS_"):
        if not own: await _no_perm(q); return
        login = d[9:]
        keys  = [p['key_val'] for p in db.get_purchases(login) if p['key_val']]
        txt   = ("🔑 All keys for " + login + ":\n\n" + "\n".join(f"• {k}" for k in keys)) if keys else "No keys."
        await q.message.reply_text(txt)

    elif d.startswith("ACC_DEL_"):
        if not own: await _no_perm(q); return
        db.delete_account(d[8:])
        await screens.show_accounts(q)

    elif d.startswith("ACC_CREDS_"):
        if not own: await _no_perm(q); return
        login = d[10:]
        acc   = db.get_account(login)
        if acc and acc.get('tg_id'):
            try:
                await q.bot.send_message(
                    acc['tg_id'],
                    f"🔒 <b>Your Account <b>Credentials</b></b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 Login:     <code>{acc['login']}</code>\n"
                    f"🔑 Password:  <code>{acc['password']}</code>\n\n"
                    f"<i>👆 Tap to copy</i>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 Use /login to sign in.",
                    parse_mode="HTML"
                )
                await q.message.reply_text("✅ <b>Credentials</b> sent successfully!")
            except Exception:
                await q.message.reply_text("❌ Could not send — user hasn't started the bot yet.")
        else:
            await q.message.reply_text("❌ User hasn't logged in yet, no Telegram ID stored.")

    elif d == "BC_ADD":
        ctx.user_data['aw'] = 'bc_collect'
        await q.message.reply_text("Send your message (text, photo, document, video):")

    elif d == "BC_PREV":
        items = ctx.user_data.get('bc_items', [])
        if not items: await q.message.reply_text("No items yet.")
        else:
            for item in items: await _bc_send(q.message, item)

    elif d == "BC_SEND":
        items = ctx.user_data.get('bc_items', [])
        if not items: await q.message.reply_text("❌ No items to send!"); return
        accs  = [a for a in db.get_all_accounts() if not a['is_owner'] and a['tg_id']]
        await q.message.reply_text(
            f"💬 Starting broadcast to {len(accs)} authorized users...\nItems: {len(items)}"
        )
        sent = 0
        for acc in accs:
            try:
                for item in items: await _bc_send_to(q.bot, acc['tg_id'], item)
                sent += 1
            except Exception: pass
        ctx.user_data['bc_items'] = []
        ctx.user_data['aw']       = None
        await q.message.reply_text(f"✅ <b>Broadcast</b> sent to {sent} users.")

    elif d == "BC_CANCEL":
        ctx.user_data['bc_items'] = []
        ctx.user_data['aw']       = None
        await screens.show_manage(q)

    elif d == "BC_COUNT":
        pass

    elif d.startswith("STATS_"):
        if not own: await _no_perm(q); return
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        act = d[6:]
        if act == "DAY":
            rev = db.revenue_since((now-timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"))
            await q.message.reply_text(f"📅 <b>Daily revenue</b>: {rev:.2f}$")
        elif act == "WEEK":
            rev = db.revenue_since((now-timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"))
            await q.message.reply_text(f"📅 <b>Weekly revenue</b>: {rev:.2f}$")
        elif act == "MONTH":
            rev = db.revenue_since((now-timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"))
            await q.message.reply_text(f"📅 <b>Monthly revenue</b>: {rev:.2f}$")
        elif act == "TOP":
            tops = db.top_buyers()
            if not tops: await q.message.reply_text("No data yet.")
            else:
                msg = "🏆 <b>Top buyers</b>:\n\n"
                for i, t in enumerate(tops, 1):
                    msg += f"{i}. {t['login']} — {t['spent']:.2f}$ ({t['orders']} orders)\n"
                await q.message.reply_text(msg)
        elif act == "PROFIT":
            total = db.total_revenue()
            cost  = 0.0
            for cat in db.get_categories():
                for pos in db.get_positions(cat['id']):
                    for kt in db.get_key_types(pos['id']):
                        sold = len([p for p in db.get_all_purchases() if p.get('kt_name') == kt['name']])
                        cost += sold * kt['init_price']
            await q.message.reply_text(
                f"💰 <b>Net Profit</b>:\nRevenue: {total:.2f}$\nCost: {cost:.2f}$\nProfit: {total-cost:.2f}$"
            )

async def _bc_send(msg, item):
    t = item['type']
    if   t=='text':  await msg.reply_text(item['c'])
    elif t=='photo': await msg.reply_photo(item['f'], caption=item.get('cap',''))
    elif t=='doc':   await msg.reply_document(item['f'], caption=item.get('cap',''))
    elif t=='video': await msg.reply_video(item['f'], caption=item.get('cap',''))

async def _bc_send_to(bot, cid, item):
    t = item['type']
    if   t=='text':  await bot.send_message(cid, item['c'])
    elif t=='photo': await bot.send_photo(cid, item['f'], caption=item.get('cap',''))
    elif t=='doc':   await bot.send_document(cid, item['f'], caption=item.get('cap',''))
    elif t=='video': await bot.send_video(cid, item['f'], caption=item.get('cap',''))

async def _do_buy(q, ctx, kt_id, qty=1):
    from datetime import datetime
    lgn = ctx.user_data.get('login')
    own = bool(ctx.user_data.get('is_owner'))
    acc = db.get_account(lgn)
    kt  = db.get_key_type(kt_id)
    if not kt:
        await q.message.reply_text("❌ <b>Key type not found</b>."); return

    cnt = db.count_stock(kt_id)
    if cnt < qty:
        await q.message.reply_text(
            f"❌ <b><b>Out of stock</b>!</b>\n"
            f"Available: {cnt} | Requested: {qty}"
        ); return

    total = kt['price'] * qty
    if not own and acc['balance'] < total:
        needed = total - acc['balance']
        await q.message.reply_text(
            f"❌ <b>Insufficient Balance</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Your balance:  <code>{acc['balance']:.2f}$</code>\n"
            f"💵 Required:      <code>{total:.2f}$</code>\n"
            f"📉 Missing:       <code>{needed:.2f}$</code>\n\n"
            f"💬 Contact admin {ADMIN_HANDLE} to top up.",
            parse_mode="HTML"
        ); return

    keys = []
    for _ in range(qty):
        k = db.pop_key(kt_id)
        if k: keys.append(k['value'])
    if not keys:
        await q.message.reply_text("❌ <b><b>Out of stock</b>!</b>"); return

    pos      = db.get_position(kt['pos_id'])
    cat_name = ctx.user_data.get('cat_name', '')
    pos_name = pos['name'] if pos else ''
    actual_total = kt['price'] * len(keys)

    if not own:
        db.add_balance(lgn, -actual_total)
        new_bal  = acc['balance'] - actual_total
        bal_line = f"💳 Remaining balance: <code>{new_bal:.2f}$</code>"
    else:
        bal_line = f"💳 Balance: <code>{OWNER_BALANCE:.2f}$</code>"

    for k in keys:
        db.add_purchase(lgn, cat_name, pos_name, kt['name'], k, None, kt['price'])

    if len(keys) == 1:
        msg = (
            f"🔑 Your key {pos_name} ({kt['name']}) : <code>{keys[0]}</code>"
        )
        try:
            await q.message.edit_text(
                msg, parse_mode="HTML",
                reply_markup=ik([[("⬅️ Go back", f"KT_{kt_id}")]])
            )
        except Exception:
            await q.message.reply_text(
                msg, parse_mode="HTML",
                reply_markup=ik([[("⬅️ Go back", f"KT_{kt_id}")]])
            )
    else:
        keys_block = "\n".join(f"<code>{k}</code>" for k in keys)
        msg = (
            f"🔑 You bought {len(keys)} key(s) {pos_name} ({kt['name']}):\n"
            f"{keys_block}"
        )
        await q.message.reply_text(msg, parse_mode="HTML")

async def _render_purch(q, ctx, lgn, page):
    purchases = db.get_purchases(lgn)
    if not purchases:
        await q.answer("❌ No purchases yet", show_alert=True); return
    per = 4
    total_pages = max(1, (len(purchases) + per - 1) // per)
    page = max(0, min(page, total_pages - 1))
    slice_ = purchases[page*per:(page+1)*per]

    parts = []
    for p in slice_:
        date_str = p['created_at']
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass
        block = (
            f"🔒 <b>{p['kt_name']}</b> | <code>{p['key_val'] or '—'}</code>\n"
            f"📦 {p['cat_name']} / {p['pos_name']}\n"
            f"💰 <b>{p['price']:.2f}$</b>\n"
            f"🕐 {date_str}"
        )
        parts.append(block)
    msg = "\n\n".join(parts)
    msg += f"\n\n<i>Page {page+1}/{total_pages}</i>"

    nav = []
    if page > 0:
        nav.append(("⬅️ Prev", f"PURCH_PAGE_{page-1}"))
    nav.append(("🏠", "MY_BACK"))
    if page + 1 < total_pages:
        nav.append(("➡️ Next", f"PURCH_PAGE_{page+1}"))
    try:
        await q.message.edit_text(msg, parse_mode="HTML", reply_markup=ik([nav]))
    except Exception:
        await q.message.reply_text(msg, parse_mode="HTML", reply_markup=ik([nav]))

async def _render_topup(q, ctx, lgn, page):
    topups = db.get_topups(lgn)
    if not topups:
        await q.answer("❌ No top-up history", show_alert=True); return
    per = 8
    total_pages = max(1, (len(topups) + per - 1) // per)
    page = max(0, min(page, total_pages - 1))
    slice_ = topups[page*per:(page+1)*per]

    parts = []
    for t in slice_:
        date_str = t['created_at']
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass
        block = (
            f"➕ <b>{t['amount']:.2f}$</b>\n"
            f"📝 {t['note'] or 'Balance added'}\n"
            f"🕐 {date_str}"
        )
        parts.append(block)
    msg = "\n\n".join(parts)
    msg += f"\n\n<i>Page {page+1}/{total_pages}</i>"

    nav = []
    if page > 0:
        nav.append(("⬅️ Prev", f"TOPUP_PAGE_{page-1}"))
    nav.append(("🏠", "MY_BACK"))
    if page + 1 < total_pages:
        nav.append(("➡️ Next", f"TOPUP_PAGE_{page+1}"))
    try:
        await q.message.edit_text(msg, parse_mode="HTML", reply_markup=ik([nav]))
    except Exception:
        await q.message.reply_text(msg, parse_mode="HTML", reply_markup=ik([nav]))

async def _render_manage_purch(q, ctx):
    
    purchases = db.get_all_purchases(500)
    if not purchases:
        try:
            await q.message.edit_text(
                "No purchases yet.",
                reply_markup=ik([[("⬅️ Go back", "GO_ACCOUNTS")]])
            )
        except Exception:
            await q.message.reply_text(
                "No purchases yet.",
                reply_markup=ik([[("⬅️ Go back", "GO_ACCOUNTS")]])
            )
        return

    per = 12
    page = ctx.user_data.get('manage_purch_page', 0)
    total_pages = max(1, (len(purchases) + per - 1) // per)
    page = max(0, min(page, total_pages - 1))
    slice_ = purchases[page*per:(page+1)*per]

    rows = [[("🔍 Search by key", "MPURCH_SEARCH")]]
    for p in slice_:
        key_short = (p['key_val'] or '—')
        cat_pos = f"{p['cat_name']}/{p['pos_name']}"
        label = f"{key_short} ({cat_pos})"
        if len(label) > 40:
            label = label[:37] + "..."
        rows.append([(label, f"MPURCH_VIEW_{p['id']}")])

    nav = []
    if page > 0:
        nav.append(("⏮️", f"MPURCH_PAGE_{page-1}"))
    nav.append((f"{page+1}/{total_pages}", "MPURCH_NOOP"))
    if page + 1 < total_pages:
        nav.append(("⏭️", f"MPURCH_PAGE_{page+1}"))
    rows.append(nav)
    rows.append([("⬅️ Go back", "GO_ACCOUNTS")])

    try:
        await q.message.edit_text(
            "🔑 Choose purchase to get info:",
            reply_markup=ik(rows)
        )
    except Exception:
        await q.message.reply_text(
            "🔑 Choose purchase to get info:",
            reply_markup=ik(rows)
        )
