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
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, ParseMode
from peewee import IntegrityError, DoesNotExist
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, BaseFilter
from models import resource, user, theList, resourceList, group, groupUser, db, db_config
from datetime import datetime
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
VERSION = '0.1.5'

# models assignments
db = db.DB
handle_db_connection = db_config.handle_db_connection
User = user.User
Group = group.Group
List = theList.List
Resource = resource.Resource
ResourceList = resourceList.ResourceList
GroupUser = groupUser.GroupUser

# inline keyboard patterns
entry_del_ptrn = 'e_del'
entry_view = 'e_view'
list_del = 'l_del'
list_view = 'l_view'
# errors
generic_error_msg = '❌ Oh no, an error occured, hang in there tight'


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
@handle_db_connection
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


@handle_db_connection
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
            update.message.reply_text('✅ OK, *added* {} in _{}_'.format(item, toUTF8(active_list.title)),
                                      parse_mode=ParseMode.MARKDOWN)
        except DoesNotExist:
            db.rollback()
            update.message.reply_text('❗ No active or available list, '
                                      'create or sctivate one')
        except Exception as e:
            db.rollback()
            update.message.reply_text(generic_error_msg)
            error(str(e))


def version(bot, update):
    update.message.reply_text('🐚 Current bot version {}'.format(VERSION))


@handle_db_connection
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

        # de-activate old activated list if exists
        (List
            .update(active=0)
            .where((List.user_id == user_id) & (List.active == 1))
            .execute())
        # create new list and activate it
        List.create(title=listTitle, user_id=user_id, active=1)

        update.message.reply_text('✅ OK, created and activated list _{}_'.format(listTitle),
                                  parse_mode=ParseMode.MARKDOWN)
    except IntegrityError:
        update.message.reply_text(
            '❗ Be careful now, list _{}_ already exists'.format(listTitle),
            parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


def is_valid_input(input):
    # list must have at least two items and the second must not be empty string
    return (len(input) >= 2 and input[1].strip())


@handle_db_connection
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
                reply_msg = '🗃 Your items in _{}_'.format(
                    toUTF8(active_list.title))
                prefix = entry_view
            else:
                prefix = entry_del_ptrn
                reply_msg = '🗑 Time for some maintenance in _{}_'.format(
                    toUTF8(active_list.title))

            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=rs.rs_content if prefix == entry_view else '❌ {}'.format(
                        toUTF8(rs.rs_content)),
                    url=rs.rs_content if isUrl(
                        rs.rs_content) and prefix == entry_view else '',
                    callback_data='{} {}'.format(prefix, rs.id)
                )] for rs in resources
            ]
            markup = InlineKeyboardMarkup(keyboard_buttons)
            update.message.reply_text(
                reply_msg, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text(
                '😢 This is a sad reality, your list is empty')
    except DoesNotExist:
        update.message.reply_text('❗ No active list, just set one as active')
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


@handle_db_connection
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
                    text='❌ {}'.format(toUTF8(rs.rs_content)),
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


@handle_db_connection
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
                reply_msg = '📚 Check out all your lists (active ticked)'
                prefix = list_view
            elif update.message.text.startswith("/delete_list"):
                reply_msg = '🗑 Throw away lists of the past'
                prefix = list_del

            keyboard_buttons = [
                [InlineKeyboardButton(
                    text='✅ {}'.format(toUTF8(ls.title)) if (prefix == list_view and ls.active == 1) else '❌ {}'.format(
                        toUTF8(ls.title)) if prefix == list_del else ls.title,
                    callback_data='{} {}'.format(
                        list_view if prefix == list_view else list_del, ls.id)
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


@handle_db_connection
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
                    text='❌ {}'.format(toUTF8(ls.title)),
                    callback_data='{} {}'.format(list_del, ls.id)
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


@handle_db_connection
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
                callback_data='{} {}'.format(list_view, ls.id)
            )] if ls.active == 0 else [InlineKeyboardButton(
                text='✅  {}'.format(toUTF8(ls.title)),
                callback_data='{} {}'.format(list_view, ls.id)
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


def isUrl(input):
    return (input.lower().startswith('http://') or
            input.lower().startswith('https://') or
            input.lower().startswith('www'))


def main():
    # db initialization
    db_config.init_db()
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
    # Register handlers for query callbacks from inline keyboard events
    dp.add_handler(CallbackQueryHandler(
        callback=remove, pattern=entry_del_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=view_entry_handler, pattern=entry_view))
    dp.add_handler(CallbackQueryHandler(
        callback=delete_list, pattern=list_del))
    dp.add_handler(CallbackQueryHandler(
        callback=activate_list, pattern=list_view))
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
