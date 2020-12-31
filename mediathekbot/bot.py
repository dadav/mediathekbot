import logging
import re
import threading
from time import sleep
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler,\
    CallbackContext, ConversationHandler
from .db import SqlBackend
from typing import Dict
from datetime import datetime, timedelta
from .mediathek import query_feed
from .utils import secs_to_hhmmss
from random import randint

log = logging.getLogger('rich')


MULTICHOICE_CALLBACK = 0

BACKEND = None

SPAM_MEMORY: Dict[str, datetime] = dict()


def is_spam(chatid):
    chatid = str(chatid)

    if chatid not in SPAM_MEMORY:
        SPAM_MEMORY[chatid] = datetime.utcnow()
        return False

    if SPAM_MEMORY[chatid] + timedelta(seconds=5) > datetime.utcnow():
        return True

    SPAM_MEMORY[chatid] = datetime.utcnow()
    return False


def cmd_add(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    if is_spam(chat_id):
        update.message.reply_text('Hey, hey, don\'t type so fast...')
        return

    given_text = " ".join(update.message.text.split()[1:])

    if not given_text:
        update.message.reply_text('This is not how it works. Do it like this: /add <search terms>')
        return

    BACKEND.save(chat_id, given_text)

    update.message.reply_text('Added to watchlist!')


def cmd_list(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    if is_spam(chat_id):
        update.message.reply_text('Hey, hey, don\'t type so fast...')
        return

    entries = BACKEND.load(chat_id)
    if not entries:
        update.message.reply_text('No entries found!')
        return

    txt = list()
    for entry in entries:
        _, chat_id, query, data = entry
        txt.append('{} ({} hits)'.format(query, len(data)))
    update.message.reply_text('\n'.join(txt))

def cmd_del(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat.id
    if is_spam(chat_id):
        update.message.reply_text('Hey, hey, don\'t type so fast...')
        return ConversationHandler.END

    entries = BACKEND.load(chat_id)

    if not entries:
        update.message.reply_text('No entries found')
        return ConversationHandler.END

    options = list()
    for entry in entries:
        entryid, chat_id, query, data = entry
        options.append([InlineKeyboardButton(
            '{} ({} hits)'.format(query, len(data)),
            callback_data=entryid)])
    reply_markup = InlineKeyboardMarkup(options)
    update.message.reply_text('Which entry do you want to delete?', reply_markup=reply_markup)
    return MULTICHOICE_CALLBACK

def multichoice_callback(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat.id
    BACKEND.delete(chat_id, int(query.data))
    query.edit_message_text(text='Deleted the selected entry!')
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    update.message.reply_text('Bye')

def cmd_help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''Use /add <search terms> watch the search results for this search terms. \
Use /list to list the already given search terms. You can delete them with /del.
''')

def fetcher(updater: Updater, backend: SqlBackend, config: Dict):
    while True:
        for entry in backend.load():
            entryid, chat_id, query, data = entry

            try:
                current_feed = query_feed(query)
            except Exception as query_err:
                log.debug(query_err)
                continue

            for video in current_feed:
                video_id, title, author, duration, summary, video_url, website_url, published = video
                if video_id not in data:
                    updater.bot.send_message(chat_id,
                                             'New video found!\n\n[{}]{}({})\nUploaded: {}\nUrl: {}'
                                             .format(author,
                                                     title,
                                                     secs_to_hhmmss(duration),
                                                     published.strftime('%m/%d/%Y, %H:%M:%S'),
                                                     website_url))
                    updater.bot.send_video(chat_id, video_url)
                    data.append(video_id)
            BACKEND.set_data(entryid, data)
            sleep(randint(0, 1))
        sleep(config['fetcher']['interval'] + randint(0, 10))


def start(token: str, backend: SqlBackend, config: Dict):
    global BACKEND

    BACKEND = backend

    updater = Updater(token, use_context=True)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('del', cmd_del),
        ],
        states={
            MULTICHOICE_CALLBACK: [CallbackQueryHandler(multichoice_callback)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # add commands
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CommandHandler('list', cmd_list))
    updater.dispatcher.add_handler(CommandHandler('add', cmd_add))
    updater.dispatcher.add_handler(CommandHandler('help', cmd_help))

    # Start the Bot
    updater.start_polling()

    th = threading.Thread(target=fetcher, args=(updater, backend, config,))
    th.start()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()
