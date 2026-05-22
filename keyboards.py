from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def ik(rows):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t, callback_data=c) for t, c in row]
        for row in rows
    ])

def main_kb(is_owner=False):
    if is_owner:
        return ReplyKeyboardMarkup([
            ["🛍️ Buy keys"],
            ["🏛️ Account", "🚀 Log out"],
            ["🔧 Manage",  "📦 Stock"],
            ["📊 Statistics"],
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup([
        ["🛍️ Buy keys"],
        ["🏛️ Account", "🚀 Log out"],
    ], resize_keyboard=True)

def login_kb():
    return ReplyKeyboardMarkup([["🔒 Login"]], resize_keyboard=True)
