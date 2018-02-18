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
import os.path
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from peewee import IntegrityError, DoesNotExist
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, BaseFilter
from models import resource, user, theList, resourceList, group, groupUser, db, db_config
from datetime import datetime
from functools import wraps
import logging
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
cur_dir = os.path.abspath(os.path.dirname(__file__))
conf_path = os.path.join(cur_dir, './conf.ini')
parser.read(conf_path)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
VERSION = '0.2.6'

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


def handle_group_call(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        if update.message.chat.type == 'group':
            update.message.reply_text('❗ Not available in groups!')
        elif update.message.chat.type == 'private':
            func(bot, update, *args, **kwargs)
    return wrapper


def handle_user_membership(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        user_id = update.message.from_user.id

        if update.message.chat.type == 'group':
            try:
                (GroupUser
                    .select()
                    .where(GroupUser.user_id == user_id)
                    .get())

                func(bot, update, *args, **kwargs)
            except DoesNotExist:
                update.message.reply_text(
                    '❗ Not member of the group list. Please join')
            except Exception as e:
                update.message.reply_text(generic_error_msg)
                error(str(e))
        elif update.message.chat.type == 'private':
            func(bot, update, *args, **kwargs)
    return wrapper


def handle_user_call(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        if update.message.chat.type == 'private':
            update.message.reply_text('❗ Only available in groups!')
        elif update.message.chat.type == 'group':
            func(bot, update, *args, **kwargs)
    return wrapper


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
@handle_group_call
@handle_db_connection
def start(bot, update):
    update.message.reply_text(
        '👶🏼 Hello there, I am going to help you manage your to-do lists')
    user_id = update.message.from_user.id
    f_name = update.message.from_user.first_name
    l_name = update.message.from_user.last_name
    try:
        User.get_or_create(
            id=user_id, f_name=f_name if not None else '', l_name=l_name if not None else '')
    except Exception as e:
        bot.send_message(
            chat_id=user_id,
            text=generic_error_msg
        )
        error(str(e))


def help(bot, update):
    update.message.reply_text('👶🏼 All stuff is pretty straightforward!')


def error(error):
    logger.error(error)


@handle_db_connection
@handle_user_membership
def add(bot, update):
    items = update.message.text.split("/add ")
    user_id = update.message.from_user.id
    chat_type = update.message.chat.type
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
            if chat_type == 'private':
                active_list = (
                    List
                    .select()
                    .where((List.user_id == user_id) & (List.active == 1))
                    .get()
                )
                # from private chat a user can only add to her lists
                if active_list.group == 1:
                    update.message.reply_text('❗ Cannot add to the group list {} from a private chat'.format(
                        toUTF8(active_list.title)))
                else:
                    resource = Resource.create(
                        rs_content=item, rs_date=datetime.utcnow())
                    ResourceList.create(resource_id=resource.id,
                                        list_id=active_list.id)
                    update.message.reply_text('✅ OK, added  {}  in  {}'.format(
                        item, toUTF8(active_list.title)))
            elif chat_type == 'group':
                group_name = update.message.chat.title
                group_id = update.message.chat.id
                user_id = update.message.from_user.id
                user_f_name = update.message.from_user.first_name
                # get the lists of all users in group
                lists = (
                    List
                    .select()
                    .join(User, on=User.id == List.user_id)
                    .where((List.group == 1) & (List.title == group_name))
                )
                # create resource
                resource = Resource.create(
                    rs_content=item, rs_date=datetime.utcnow())
                # add to every user's list
                if len(list(lists)) != 0:
                    for ls in lists:
                        if ls.user_id.id != user_id:
                            ResourceList.create(resource_id=resource.id,
                                                list_id=ls.id)

                    bot.send_message(
                        chat_id=group_id,
                        text='✅ OK, {} added  {}  in  {}  list'.format(
                            toUTF8(user_f_name), item, toUTF8(group_name))
                    )
                else:
                    bot.send_message(
                        chat_id=group_id,
                        text='❗ At least two members of the group must join the list in order to add items.'
                    )
        except DoesNotExist:
            db.rollback()
            update.message.reply_text('❗ No active or available list, '
                                      'create or activate one')
        except Exception as e:
            db.rollback()
            update.message.reply_text(generic_error_msg)
            error(str(e))


def version(bot, update):
    update.message.reply_text('🐚 Current bot version {}'.format(VERSION))


@handle_group_call
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

        update.message.reply_text(
            '✅ OK, created and activated list  {}'.format(listTitle))
    except IntegrityError:
        update.message.reply_text(
            '❗ Be careful now, list  {}  already exists'.format(listTitle))
    except Exception as e:
        update.message.reply_text(generic_error_msg)
        error(str(e))


def is_valid_input(input):
    # list must have at least two items and the second must not be empty string
    return (len(input) >= 2 and input[1].strip())


@handle_group_call
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
                reply_msg = '🗃 Your items in  {}'.format(
                    toUTF8(active_list.title))
                prefix = entry_view
            else:
                prefix = entry_del_ptrn
                reply_msg = '🗑 Time for some maintenance in  {}'.format(
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
                reply_msg, reply_markup=markup)
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


@handle_group_call
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

            def generate_keyboard_button(list, prefix):
                group_icon = '👫' if list.group == 1 else ''
                tick_icon = '✅' if (
                    prefix == list_view and list.active == 1) else ''
                del_icon = '❌'
                item_icon = del_icon if prefix == list_del else tick_icon

                callback_data = '{} {} {}'.format(
                    list_view if prefix == list_view else list_del, list.id, list.group)

                return [InlineKeyboardButton(text='{} {} {}'.format(item_icon, toUTF8(list.title), group_icon),
                                             callback_data=callback_data)]

            keyboard_buttons = [generate_keyboard_button(
                ls, prefix) for ls in lists]

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
    list_group = cb_data.split()[2]
    user_id = update.callback_query.from_user.id

    # start db transaction
    with db.atomic() as trx:
        try:
            if list_group == 'True':
                # if you delete a group list remove user from group
                (GroupUser
                    .delete()
                    .where(GroupUser.user_id == user_id)
                    .execute())
                # if no user from the group holds this resource get it to delete it
                raw_query = 'SELECT resource_list.resource_id FROM resource_list WHERE resource_list.list_id = {0} AND resource_list.resource_id  NOT IN (SELECT resource_list.resource_id FROM resource_list WHERE resource_list.list_id != {0})'.format(
                    list_id)

                resources_in_list = ResourceList.raw(raw_query)
            else:
                # get all resources associated with list to delete
                resources_in_list = (
                    ResourceList
                    .select()
                    .where(ResourceList.list_id == list_id)
                )

            rs_list_ids = []
            for rs_list in resources_in_list:
                rs_list_ids.append(rs_list.resource_id.id)

            # delete entries from associative table
            (ResourceList
                .delete()
                .where(ResourceList.list_id == list_id)
                .execute())
            # # delete resources
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
                    text='❌ {} {}'.format(
                        toUTF8(ls.title), '👫' if ls.group == 1 else ''),
                    callback_data='{} {} {}'.format(list_del, ls.id, ls.group)
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
        def generate_keyboard_button(list):
            group_icon = '👫' if list.group == 1 else ''
            tick_icon = '✅' if list.active == 1 else ''
            callback_data = '{} {} {}'.format(list_view, list.id, list.group)

            return [InlineKeyboardButton(text='{} {} {}'.format(tick_icon, toUTF8(list.title), group_icon),
                                         callback_data=callback_data)]

        keyboard_buttons = [generate_keyboard_button(ls) for ls in lists]

        markup = InlineKeyboardMarkup(keyboard_buttons)
        bot.edit_message_reply_markup(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=markup)
    except Exception as e:
        if e.message != 'Message is not modified':
            bot.send_message_reply_markup(
                chat_id=update.callback_query.message.chat_id,
                text=generic_error_msg)
            error(str(e))


@handle_db_connection
def create_group(bot, update):
    group_id = update.message.chat.id
    group_name = update.message.chat.title
    try:
        Group.get_or_create(id=group_id, g_name=group_name)
    except Exception as e:
        bot.send_message(
            chat_id=update.message.chat.id,
            text='❌ Bot initialization for group failed. Remove and add again',
            reply_to_message_id=update.message.message_id)
        error(str(e))


@handle_user_call
@handle_db_connection
def join_group_list(bot, update):
    user_id = update.message.from_user.id
    group_id = update.message.chat.id
    f_name = update.message.from_user.first_name
    l_name = update.message.from_user.last_name
    group_name = update.message.chat.title

    # start db transaction
    with db.atomic() as trx:
        try:
            # register user if necessary
            User.get_or_create(id=user_id, f_name=f_name, l_name=l_name)
            #  FOR TEST Only
            # Group.get_or_create(id=group_id, g_name=group_name)
            # create group-user record
            GroupUser.get_or_create(user_id=user_id,
                                    group_id=group_id)
            # create group list for user
            List.get_or_create(
                title=group_name, user_id=user_id, active=0, group=1)

            bot.send_message(
                chat_id=group_id,
                text='✅ OK, {} you joined the shared list of  {}  group'.format(
                    toUTF8(f_name), toUTF8(group_name))
            )
        except Exception as e:
            db.rollback()
            bot.send_message(
                chat_id=group_id,
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


class AddedToGroupFilter(BaseFilter):
    def filter(self, message):
        return message.new_chat_members and any(user.is_bot and user.username == conf.get('bot', 'BOT_NAME') for user in message.new_chat_members)


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
    updater = Updater(parser.get('bot', 'BOT_TOKEN'))
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
    dp.add_handler(CommandHandler("join_group_list", join_group_list))
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
    filter_add_to_group = AddedToGroupFilter()
    # create message handlers
    what_item_handler = MessageHandler(filter_what_item, add)
    list_item_handler = MessageHandler(filter_list_title, create_list)
    add_to_group_handler = MessageHandler(filter_add_to_group, create_group)
    # Register handlers for reply messages
    dp.add_handler(what_item_handler)
    dp.add_handler(list_item_handler)
    dp.add_handler(add_to_group_handler)
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
