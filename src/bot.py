#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot for to-do lists
# Under GPLv3.0
"""
To do list Bot.

Usage:
The user can create and manage her to-do lists.
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from peewee import IntegrityError, DoesNotExist, OperationalError
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, BaseFilter
from models import resource, user, theList, resourceList, group, groupUser, db
from datetime import datetime
import logging
import validators
import time

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
VERSION = '0.1.1'

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
generic_error_msg = 'An error occured while processing the request'


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Welcome to your personal to do list handler.')
    user_id = update.message.from_user.id
    User.get_or_create(id=user_id)


def help(bot, update):
    update.message.reply_text('All stuff is pretty straightforward!')


def echo(bot, update):
    update.message.reply_text(update.message.text)


def error(error):
    logger.error(error)


def add_to_list(bot, update):
    items = update.message.text.split("/add_to_list ")
    user_id = update.message.from_user.id

    if (is_valid_input(items)):
        item = ' '.join(items[1:])
    elif update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
        item = update.message.text
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
            resource = Resource.create(
                rs_content=item, rs_date=datetime.utcnow())
            ResourceList.create(resource_id=resource.id,
                                list_id=active_list.id)

            update.message.reply_text('OK, added {}'.format(item))
        except DoesNotExist:
            db.rollback()
            update.message.reply_text('No active or available list. '
                'Create a list or set one as active.')
        except Exception as e:
            db.rollback()
            update.message.reply_text(generic_error_msg)
            error(str(e))


def version(bot, update):
    update.message.reply_text('Current bot version ' + VERSION)


def create_list(bot, update):
    items = update.message.text.split("/create_list ")
    user_id = update.message.from_user.id

    if (is_valid_input(items)):
        listTitle = items[1].strip()
    elif update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
        listTitle = update.message.text
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

        update.message.reply_text('Created list ' + listTitle)
    except IntegrityError:
        update.message.reply_text('List ' + listTitle + ' already exists')
    except Exception as e:
        update.message.reply_text('An error occured ')
        error(str(e))


def is_valid_input(input):
    # list must have at least two items and the second must not be empty string
    return (len(input) >= 2 and input[1].strip())


def show_list(bot, update):
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
            if update.message.text.startswith("/show_list"):
                reply_msg = 'Displaying items from list: ' + active_list.title
                cb_dt_pfx = view_ptrn
            else:
                cb_dt_pfx = entry_del_ptrn
                reply_msg = 'Delete items from list: ' + active_list.title

            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=rs.rs_content,
                    url=rs.rs_content if validators.url(rs.rs_content) else '',
                    callback_data='{} {}'.format(cb_dt_pfx, rs.id)
                )] for rs in resources
            ]
            markup = InlineKeyboardMarkup(keyboard_buttons)
            update.message.reply_text(reply_msg, reply_markup=markup)
        else:
            update.message.reply_text('List is empty.')
    except DoesNotExist:
        update.message.reply_text('No active list to display. Set an active list')
    except Exception as e:
        update.message.reply_text('An error occured ')
        error(str(e))


def remove_from_list(bot, update):
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


def show_all_lists(bot, update):
    user_id = update.message.from_user.id

    try:
        lists = (
            List
            .select()
            .where(List.user_id == user_id)
        )

        if len(list(lists)):
            if update.message.text.startswith("/show_all_lists"):
                reply_msg = 'Showing all user lists.'
                cb_dt_pfx = view_ptrn
            elif update.message.text.startswith("/delete_list"):
                reply_msg = 'Delete any of the following lists:'
                cb_dt_pfx = list_del_ptrn
            elif update.message.text.startswith("/set_active_list"):
                reply_msg = 'Choose list to set as active to perform operations:'
                cb_dt_pfx = list_act_ptrn

            keyboard_buttons = [
                [InlineKeyboardButton(
                    text=ls.title,
                    callback_data='{} {}'.format(cb_dt_pfx, ls.id)
                )] for ls in lists
            ]

            markup = InlineKeyboardMarkup(keyboard_buttons)
            update.message.reply_text(reply_msg, reply_markup=markup)
        else:
            update.message.reply_text('No list available.')
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
                text='An error occured while processing the request.'
            )
            error(str(e))


def set_active_list(bot, update):
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

        # retrieve list
        active_list = (
            List
            .select()
            .where((List.user_id == user_id) & (List.active == 1))
            .get()
        )
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            show_alert=True,
            text='Changed currently active list to: {}'.format(active_list.title)
        )
    except Exception as e:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            show_alert=True,
            text=generic_error_msg
        )
        error(str(e))

def view_active_list(bot, update):
    user_id = update.message.from_user.id
    try:
        active_list = (
            List
            .select()
            .where((List.user_id == user_id) & (List.active == 1))
            .get()
        )

        update.message.reply_text('{} list is currently active.'.format(active_list.title))
    except DoesNotExist:
        update.message.reply_text('No list available. Add a new list and try again.')
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


def init_db():
    num_of_retries = 30
    time_interval__in_secs = 1
    # connect to db explicitely, will reveal errors
    for _ in range(num_of_retries):
        try:
            db.connect()
            # create db tables if they do not exist
            db.create_tables([User, List, ResourceList, Resource], safe=True)
            break
        except OperationalError:
            time.sleep(time_interval__in_secs)
        except Exception as e:
            error(str(e))
            raise
    else:
        raise


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


def main():
    # db initialization
    init_db()
    # Create the EventHandler and pass it the bot's token.
    updater = Updater('${BOT_TOKEN}')
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("version", version))
    dp.add_handler(CommandHandler("add_to_list", add_to_list))
    dp.add_handler(CommandHandler("remove_from_list", show_list))
    dp.add_handler(CommandHandler("create_list", create_list))
    dp.add_handler(CommandHandler("show_list", show_list))
    dp.add_handler(CommandHandler("delete_list", show_all_lists))
    dp.add_handler(CommandHandler("show_all_lists", show_all_lists))
    dp.add_handler(CommandHandler("set_active_list", show_all_lists))
    dp.add_handler(CommandHandler("view_active_list", view_active_list))
    # Register handlers for query callbacks from inline keyboard events
    dp.add_handler(CallbackQueryHandler(
        callback=remove_from_list, pattern=entry_del_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=view_entry_handler, pattern=view_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=delete_list, pattern=list_del_ptrn))
    dp.add_handler(CallbackQueryHandler(
        callback=set_active_list, pattern=list_act_ptrn))
    # instantiate filters
    filter_what_item = WhatItemFilter()
    filter_list_title = WhatListFilter()
    # create message handlers
    what_item_handler = MessageHandler(filter_what_item, add_to_list)
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
