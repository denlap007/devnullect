#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot for to-do lists
# Under GPLv3.0
"""
To do list Bot.

Usage:
The user can manage her to-do lists.
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from peewee import IntegrityError, DoesNotExist
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, BaseFilter
from models import resource, user, theList, resourceList, group, groupUser, db, dbConfig
from datetime import datetime
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
VERSION = '0.1.4'

# models assignments
db = db.DB
User = user.User
Group = group.Group
List = theList.List
Resource = resource.Resource
ResourceList = resourceList.ResourceList
GroupUser = groupUser.GroupUser

# inline keyboard patterns
entry_del_ptrn = 'e_del'
view_ptrn = 'view'
list_del_ptrn = 'l_del'
list_act_ptrn = 'l_act'

# errors
generic_error_msg = '❌ Oh no, an error occured, hang in there tight'


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text(
        '👶🏼 Hello there, I am going to help you manage your to-do lists')
    user_id = update.message.from_user.id
    User.get_or_create(id=user_id)


def help(bot, update):
    update.message.reply_text('👶🏼 All stuff is pretty straightforward!')


def echo(bot, update):
    update.message.reply_text(update.message.text)


def error(error):
    logger.error(error)


def add(bot, update):
    items = update.message.text.split("/add ")
    user_id = update.message.from_user.id

    if (is_valid_input(items)):
        item = toUTF8(' '.join(items[1:]))
    elif update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
        item = toUTF8(update.message.text)
    else:
        bot.send_message(
            chat_id=update.message.chat.id,
            text="What item?",
            reply_to_message_id=update.message.message_id,
            reply_markup=ForceReply(selective=True))
        return

    # start db transaction
    with db.atomic() as trx:
        try:
            # find active user list if any
            active_list = (
                List
                .select()
                .where((List.user_id == user_id) & (List.active == 1))
                .get()
            )
            # item = item.encode('utf-8') if isinstance(item, unicode) else item
            resource = Resource.create(
                rs_content=item, rs_date=datetime.utcnow())
            ResourceList.create(resource_id=resource.id,
                                list_id=active_list.id)

            update.message.reply_text('✅ OK, added {}'.format(item))
        except DoesNotExist:
            db.rollback()
            update.message.reply_text('❗ No active or available list, '
                                      'create a list or set one as active')
        except Exception as e:
            db.rollback()
            update.message.reply_text(generic_error_msg)
            error(str(e))


def version(bot, update):
    update.message.reply_text('🐚 Current bot version {}'.format(VERSION))


def create_list(bot, update):
    items = update.message.text.split("/create_list ")
    user_id = update.message.from_user.id

    if (is_valid_input(items)):
        listTitle = toUTF8(items[1].strip())
    elif update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
        listTitle = toUTF8(update.message.text)
    else:
        bot.send_message(
            chat_id=update.message.chat.id,
            text="List title?",
            reply_to_message_id=update.message.message_id,
            reply_markup=ForceReply(selective=True))
        return

    try:
        active_list = (
            List
            .select()
            .where((List.user_id == user_id) & (List.active == 1))
        )

        if active_list.exists():
            List.create(title=listTitle, user_id=user_id)
        else:
            List.create(title=listTitle, user_id=user_id, active=1)

        update.message.reply_text('✅ OK, created list {}'.format(listTitle))
    except IntegrityError:
        update.message.reply_text(
            '❗ Be careful now, list {} already exists'.format(listTitle))
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


def is_valid_input(input):
    # list must have at least two items and the second must not be empty string
    return (len(input) >= 2 and input[1].strip())


def show(bot, update):
    user_id = update.message.from_user.id

    try:
        active_list = (
            List
            .select()
            .where((List.user_id == user_id) & (List.active == 1))
            .get()
        )

        resources = (
            Resource
            .select()
            .join(ResourceList)
            .where(ResourceList.list_id == active_list.id)
            .order_by(Resource.rs_date.desc())
        )

        if len(list(resources)):
            if update.message.text.startswith("/show"):
                reply_msg = '🗃 Your precious items in {}'.format(
                    toUTF8(active_list.title))
                cb_dt_pfx = view_ptrn
            else:
                cb_dt_pfx = entry_del_ptrn
                reply_msg = '🗑 Time for some maintenance in {}'.format(
                    toUTF8(active_list.title))

            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=rs.rs_content,
                    url=rs.rs_content if (rs.rs_content.startswith('http') or rs.rs_content.startswith(
                        'www') or rs.rs_content.startswith('https://')) and cb_dt_pfx == view_ptrn else '',
                    callback_data='{} {}'.format(cb_dt_pfx, rs.id)
                )] for rs in resources
            ]
            markup = InlineKeyboardMarkup(keyboard_buttons)
            update.message.reply_text(reply_msg, reply_markup=markup)
        else:
            update.message.reply_text(
                '😢 This is a sad reality, your list is empty')
    except DoesNotExist:
        update.message.reply_text('❗ No active list, just set one as active')
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


def remove(bot, update):
    # get data attached to callback and extract resourse id and user id
    cb_data = update.callback_query.data
    rs_id = cb_data.split()[1]
    user_id = update.callback_query.from_user.id

    # start db transaction
    with db.atomic() as trx:
        try:
            # find active user list
            active_list = (
                List
                .select()
                .where((List.user_id == user_id) & (List.active == 1))
                .get()
            )

            # delete resource and associated data
            rs = Resource.get(id=rs_id)
            rs_title = rs.rs_content
            rsList = ResourceList.get(
                resource_id=rs_id, list_id=active_list.id)
            rsList.delete_instance()
            rs.delete_instance()

            # retrive resources for active list
            resources = (
                Resource
                .select()
                .join(ResourceList)
                .where(ResourceList.list_id == active_list.id)
                .order_by(Resource.rs_date.desc())
            )

            # update keyboard markup with new values and send to user
            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=rs.rs_content,
                    callback_data='{} {}'.format(entry_del_ptrn, rs.id)
                )] for rs in resources
            ]
            markup = InlineKeyboardMarkup(keyboard_buttons)

            bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text='Deleted ' + rs_title
            )
            bot.edit_message_reply_markup(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id,
                reply_markup=markup
            )
        except Exception as e:
            db.rollback()
            bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=generic_error_msg
            )
            error(str(e))


def view_entry_handler(bot, update):
    # After the user presses an inline button, Telegram clients will display a
    # progress bar until you call answer. It is, therefore, necessary to react
    # by calling telegram.Bot.answer_callback_query even if no notification to
    # the user is needed
    bot.answer_callback_query(update.callback_query.id)


def show_lists(bot, update):
    user_id = update.message.from_user.id

    try:
        lists = (
            List
            .select()
            .where(List.user_id == user_id)
        )

        if len(list(lists)):
            if update.message.text.startswith("/show_lists"):
                reply_msg = '📚 Check out all your lists'
                cb_dt_pfx = view_ptrn
            elif update.message.text.startswith("/delete_list"):
                reply_msg = '🗑 Throw away lists of the past'
                cb_dt_pfx = list_del_ptrn
            elif update.message.text.startswith("/activate_list"):
                reply_msg = '📌 Activate your list of desire'
                cb_dt_pfx = list_act_ptrn

            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=ls.title,
                    callback_data='{} {}'.format(cb_dt_pfx, ls.id)
                )] if ls.active == 0 else [InlineKeyboardButton(
                    text='✅  {}'.format(toUTF8(ls.title)),
                    callback_data='{} {}'.format(cb_dt_pfx, ls.id)
                )] for ls in lists
            ]

            markup = InlineKeyboardMarkup(keyboard_buttons)
            update.message.reply_text(reply_msg, reply_markup=markup)
        else:
            update.message.reply_text(
                '❗ Too bad, no lists available. Wait no more, start being creative')
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


def delete_list(bot, update):
    # get data attached to callback and extract list id and user id
    cb_data = update.callback_query.data
    list_id = cb_data.split()[1]
    user_id = update.callback_query.from_user.id

    # start db transaction
    with db.atomic() as trx:
        try:
            # get all resources associated with list to delete
            resources_in_list = (
                ResourceList
                .select()
                .where(ResourceList.list_id == list_id)
            )

            rs_list_ids = []

            for rs_list in resources_in_list:
                rs_list_ids.append(rs_list.resource_id.id)

            # # delete entries from associative table
            (ResourceList
                .delete()
                .where(ResourceList.list_id == list_id)
                .execute())

            #  delete resources
            (Resource
                .delete()
                .where(Resource.id << rs_list_ids)
                .execute())

            # delete list entry
            the_list = List.get(id=list_id)
            the_list.delete_instance()

            # retrieve lists
            lists = (
                List
                .select()
                .where(List.user_id == user_id)
            )

            # update keyboard markup with new values and send to user
            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=ls.title,
                    callback_data='{} {}'.format(list_del_ptrn, ls.id)
                )] for ls in lists
            ]
            markup = InlineKeyboardMarkup(keyboard_buttons)

            bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text='Deleted list'
            )
            bot.edit_message_reply_markup(
                chat_id=update.callback_query.message.chat_id,
                message_id=update.callback_query.message.message_id,
                reply_markup=markup
            )
        except Exception as e:
            db.rollback()
            bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=generic_error_msg
            )
            error(str(e))


def activate_list(bot, update):
    # get data attached to callback and extract list id and user id
    cb_data = update.callback_query.data
    list_id = cb_data.split()[1]
    user_id = update.callback_query.from_user.id

    try:
        # de-activate old activated list
        (List
            .update(active=0)
            .where((List.user_id == user_id) & (List.active == 1))
            .execute())
        # activate new list
        (List
            .update(active=1)
            .where(List.id == list_id)
            .execute())
        # retrieve lists
        lists = (
            List
            .select()
            .where(List.user_id == user_id)
        )

        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            show_alert=True,
            text='✅ OK, activated list {}'.format(
                toUTF8([ls.title for ls in lists if ls.active == 1][0]))
        )
        # update reply_markup
        keyboard_buttons = [
            [InlineKeyboardButton(
                text=ls.title,
                callback_data='{} {}'.format(list_act_ptrn, ls.id)
            )] if ls.active == 0 else [InlineKeyboardButton(
                text='✅  {}'.format(toUTF8(ls.title)),
                callback_data='{} {}'.format(list_act_ptrn, ls.id)
            )] for ls in lists
        ]

        markup = InlineKeyboardMarkup(keyboard_buttons)
        bot.edit_message_reply_markup(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=markup)
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            show_alert=True,
            text=generic_error_msg
        )
        error(str(e))


class WhatItemFilter(BaseFilter):
    def filter(self, message):
        return (message.reply_to_message and
                'What item?' in message.reply_to_message.text and
                message.reply_to_message.from_user.is_bot and
                message.message_id == message.reply_to_message.message_id + 1)


class WhatListFilter(BaseFilter):
    def filter(self, message):
        return (message.reply_to_message and
                'List title?' in message.reply_to_message.text and
                message.reply_to_message.from_user.is_bot and
                message.message_id == message.reply_to_message.message_id + 1)


def toUTF8(input):
    return input.encode('utf-8') if isinstance(input, unicode) else input


def main():
    # db initialization
    dbConfig.init_db()
    # Create the EventHandler and pass it the bot's token.
    updater = Updater('${BOT_TOKEN}')
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("version", version))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("remove", show))
    dp.add_handler(CommandHandler("create_list", create_list))
    dp.add_handler(CommandHandler("show", show))
    dp.add_handler(CommandHandler("delete_list", show_lists))
    dp.add_handler(CommandHandler("show_lists", show_lists))
    dp.add_handler(CommandHandler("activate_list", show_lists))
    # Register handlers for query callbacks from inline keyboard events
    dp.add_handler(CallbackQueryHandler(
        callback=remove, pattern=entry_del_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=view_entry_handler, pattern=view_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=delete_list, pattern=list_del_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=activate_list, pattern=list_act_ptrn))
    # instantiate filters
    filter_what_item = WhatItemFilter()
    filter_list_title = WhatListFilter()
    # create message handlers
    what_item_handler = MessageHandler(filter_what_item, add)
    list_item_handler = MessageHandler(filter_list_title, create_list)
    # Register handlers for reply messages
    dp.add_handler(what_item_handler)
    dp.add_handler(list_item_handler)
    # log all errors
    dp.add_error_handler(error)
    # Start the Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
