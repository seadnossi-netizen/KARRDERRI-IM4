# EVANN IOS 
import asyncio
import logging
import nest_asyncio

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ConversationHandler
)

from config import BOT_TOKEN
from db import init_db
from handlers.auth      import start, login_cmd, logout, receive_creds, WAIT_CREDS
from handlers.menu      import buy_keys, account, manage, stock, statistics
from handlers.callbacks import router
from handlers.messages  import text_handler, file_handler, done_cmd, cancel_cmd, reset_cmd

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

nest_asyncio.apply()

def build_app():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('login', login_cmd),
            MessageHandler(filters.Regex('^🔒 Login$'), login_cmd),
        ],
        states={
            WAIT_CREDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_creds)]
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True,
    )
    app.add_handler(conv)

    app.add_handler(MessageHandler(filters.Regex('^🛍️ Buy keys$'),  buy_keys))
    app.add_handler(MessageHandler(filters.Regex('^🏛️ Account$'),   account))
    app.add_handler(MessageHandler(filters.Regex('^🚀 Log out$'),    logout))
    app.add_handler(MessageHandler(filters.Regex('^🔧 Manage$'),     manage))
    app.add_handler(MessageHandler(filters.Regex('^📦 Stock$'),      stock))
    app.add_handler(MessageHandler(filters.Regex('^📊 Statistics$'), statistics))

    app.add_handler(CommandHandler('reset',  reset_cmd))
    app.add_handler(CommandHandler('done',   done_cmd))
    app.add_handler(CommandHandler('cancel', cancel_cmd))

    app.add_handler(CallbackQueryHandler(router))

    app.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND,
        file_handler
    ))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    return app

async def async_main():
    
    init_db()

    app = build_app()
    logging.info("🤖 Bot started with Reset middleware!")

    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

def main():
    
    init_db()
    app = build_app()
    logging.info("🤖 Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
