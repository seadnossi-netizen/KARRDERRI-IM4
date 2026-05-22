import db
from keyboards import ik
from telegram import CallbackQuery, Message, InlineKeyboardMarkup

async def edit(msg, text, markup=None, parse_mode="HTML"):
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode=parse_mode)
    except Exception:
        await msg.reply_text(text, reply_markup=markup, parse_mode=parse_mode)

async def get_msg(target):
    if isinstance(target, CallbackQuery):
        return target.message
    return target

async def show_cats(target, is_owner):
    msg  = await get_msg(target)
    cats = db.get_categories()
    rows = []
    if is_owner:
        rows.append([("➕ Add category", "CAT_ADD")])
    for c in cats:
        rows.append([(c['name'], f"CAT_{c['id']}")])
    txt = "📋 Choose a category:" if (cats or is_owner) else "📋 <b>No categories yet</b>."
    await edit(msg, txt, ik(rows) if rows else None)

async def show_positions(target, cat_id, is_owner):
    msg  = await get_msg(target)
    cat  = db.get_category(cat_id)
    if not cat:
        await edit(msg, "❌ <b>Category not found</b>."); return
    poss = db.get_positions(cat_id)
    rows = []
    if is_owner:
        rows.append([
            ("➕ Add position",    f"POS_ADD_{cat_id}"),
            ("🗑️ Delete category", f"CAT_DEL_{cat_id}"),
        ])
    for p in poss:
        rows.append([(p['name'], f"POS_{p['id']}")])
    rows.append([("⬅️ Go back", "GO_CATS")])
    await edit(msg, f"📋 Choose a product in category {cat['name']}:", ik(rows))

async def show_pos_detail(target, pos_id, is_owner):
    msg  = await get_msg(target)
    pos  = db.get_position(pos_id)
    if not pos:
        await edit(msg, "❌ <b>Position not found</b>."); return
    kts  = db.get_key_types(pos_id)
    fcnt = db.count_files(pos_id)
    rows = []
    if is_owner:
        rows.append([("📁 Add files",       f"FILE_ADD_{pos_id}"),
                     ("⚙️ Edit status",     f"STS_EDIT_{pos_id}")])
        rows.append([("➕ Add key type",    f"KT_ADD_{pos_id}"),
                     ("🗑️ Delete position", f"POS_DEL_{pos_id}")])
    rows.append([("📤 Get files",    f"FILE_GET_{pos_id}"),
                 ("🛡️ Check status", f"STS_CHK_{pos_id}")])
    for kt in kts:
        rows.append([(f"{kt['name']} - {kt['price']:.2f}$", f"KT_{kt['id']}")])
    rows.append([("⬅️ Go back", f"GO_POS_{pos['cat_id']}")])

    if kts:
        header = f"📋 Choose a key type for {pos['name']}:\nFiles: {fcnt}"
    else:
        header = f"❌ <b>No key types</b> for {pos['name']}!\nFiles: {fcnt}"

    await edit(msg, header, ik(rows))

async def show_kt_detail(target, kt_id, cat_name, is_owner):
    msg = await get_msg(target)
    kt  = db.get_key_type(kt_id)
    if not kt:
        await edit(msg, "❌ <b>Key type not found</b>."); return
    pos = db.get_position(kt['pos_id'])
    cnt = db.count_stock(kt_id)
    pos_name = pos['name'] if pos else ''
    if is_owner:
        txt = (
            f"🔑 Key {pos_name} ({kt['name']}):\n"
            f"- Category: {cat_name}\n"
            f"- Price: {kt['price']:.2f}$\n"
            f"- Keys in stock: {cnt}\n"
            f"- Initial price: {kt['init_price']:.2f}$"
        )
    else:
        txt = (
            f"🔑 Key {pos_name} ({kt['name']}):\n"
            f"- Category: {cat_name}\n"
            f"- Price: {kt['price']:.2f}$\n"
            f"- Keys in stock: {cnt}"
        )
    rows = [[(("🔑 Buy", f"BUY_{kt_id}"))]]
    if is_owner:
        rows.append([("🗑️ Delete key type", f"KT_DEL_{kt_id}")])
        rows.append([("➕ Add keys",   f"KEYS_ADD_{kt_id}"),
                     ("❌ Clear keys", f"KEYS_CLR_{kt_id}")])
        rows.append([("💰 Edit price",  f"PRICE_EDIT_{kt_id}"),
                     ("📦 Init price",  f"PRICE_INIT_{kt_id}")])
    rows.append([("⬅️ Go back", f"GO_KT_{kt['pos_id']}")])
    await edit(msg, txt, ik(rows))

async def show_accounts(target):
    msg  = await get_msg(target)
    accs = [a for a in db.get_all_accounts() if not a['is_owner']]
    rows = [[("➕ Add account", "ACC_ADD")]]
    pairs = [accs[i:i+2] for i in range(0, len(accs), 2)]
    for pair in pairs:
        rows.append([
            (f"{a['login']} ({a['balance']:.2f}$)", f"ACC_DETAIL_{a['login']}")
            for a in pair
        ])
    rows.append([("⬅️ Go back", "GO_MANAGE_BACK")])
    await edit(msg, "👤 Choose account to manage:", ik(rows))

async def show_acc_detail(target, login):
    msg = await get_msg(target)
    acc = db.get_account(login)
    if not acc:
        await edit(msg, "❌ <b>Account not found</b>."); return
    txt = (
        f"👤 Info about account:\n"
        f"- Login: <code>{acc['login']}</code>\n"
        f"- Password: <code>{acc['password']}</code>\n"
        f"- Balance: <code>{acc['balance']:.2f}$</code>\n"
        f"- Created: {acc['created_at']}"
    )
    rows = [
        [("➕ Add balance",    f"ACC_ADDBAL_{login}"),
         ("❌ Reset balance",  f"ACC_RSTBAL_{login}")],
        [("📦 View purchases", f"ACC_PURCH_{login}")],
        [("🗑️ Delete account", f"ACC_DEL_{login}")],
        [("⬅️ Go back",        "GO_ACCOUNTS")],
    ]
    await edit(msg, txt, ik(rows))

async def show_manage(target):
    msg = await get_msg(target)
    await edit(msg, "🔧 Choose action", ik([
        [("🔒 Manage accounts",   "MANAGE_ACCS")],
        [("🔍 Look at purchases", "MANAGE_PURCH")],
        [("📢 <b>Broadcast</b>",         "MANAGE_BC")],
    ]))
