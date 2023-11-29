#!/usr/bin/env python3
import asyncio
import logging
import math
import os

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from metaapi_cloud_sdk import MetaApi
from prettytable import PrettyTable
from telegram import ParseMode, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, ConversationHandler, CallbackContext

# ... (rest of the imports and setup)

# New state for conversation handler
RECEIVE_MESSAGES = range(4)

# ... (rest of the code)

def handle_forwarded_messages(update: Update, context: CallbackContext) -> None:
    """Handles forwarded messages to start receiving all messages from a chat."""
    if not update.effective_message.chat.username == TELEGRAM_USER:
        update.effective_message.reply_text("You are not authorized to use this bot! 🙅🏽‍♂️")
        return

    # Extract the chat ID from the forwarded message
    chat_id = update.message.forward_from_chat.id

    # Start receiving all messages from the chat
    context.bot.send_message(chat_id, "Starting to receive all messages from this chat. Type /stop to stop.")
    context.user_data['chat_to_receive'] = chat_id

    return

def stop_receiving_messages(update: Update, context: CallbackContext) -> None:
    """Stops receiving messages from the chat."""
    if 'chat_to_receive' in context.user_data:
        del context.user_data['chat_to_receive']
        update.effective_message.reply_text("Stopped receiving messages from the chat.")
    else:
        update.effective_message.reply_text("Not currently receiving messages from any chat.")

    return

def Trade_Command(update: Update, context: CallbackContext) -> int:
    """Asks user to enter the trade they would like to place.

    Arguments:
        update: update from Telegram
        context: CallbackContext object that stores commonly used objects in handler callbacks
    """
    if not update.effective_message.chat.username == TELEGRAM_USER:
        update.effective_message.reply_text("You are not authorized to use this bot! 🙅🏽‍♂️")
        return ConversationHandler.END

    # initializes the user's trade as empty prior to input and parsing
    context.user_data['trade'] = None

    # check if the message is a command or a regular text message
    if update.message.text.startswith('/'):
        # Handle as a command
        update.effective_message.reply_text("Please use the /trade command to enter a trade.")
        return ConversationHandler.END
    else:
        # Handle as a trade input
        try:
            # parses signal from Telegram message
            trade = ParseSignal(update.effective_message.text)

            # checks if there was an issue with parsing the trade
            if not trade:
                raise Exception('Invalid Trade')

            # sets the user context trade equal to the parsed trade
            context.user_data['trade'] = trade
            update.effective_message.reply_text(
                "Trade Successfully Parsed! 🥳\nConnecting to MetaTrader ... \n(May take a while) ⏰")

        except Exception as error:
            logger.error(f'Error: {error}')
            errorMessage = f"There was an error parsing this trade 😕\n\nError: {error}\n\nPlease re-enter trade with this format:\n\nBUY/SELL SYMBOL\nEntry \nSL \nTP \n\nOr use the /cancel command to cancel this action."
            update.effective_message.reply_text(errorMessage)

            # returns to TRADE state to reattempt trade parsing
            return TRADE

        # attempts connection to MetaTrader and places trade
        asyncio.run(ConnectMetaTrader(update, context.user_data['trade'], True))

        # removes trade from user context data
        context.user_data['trade'] = None

        return ConversationHandler.END

def main() -> None:
    """Runs the Telegram bot."""

    updater = Updater(TOKEN, use_context=True)

    # get the dispatcher to register handlers
    dp = updater.dispatcher

    # ... (existing code)

    dp.add_handler(MessageHandler(Filters.forwarded, handle_forwarded_messages))
    dp.add_handler(CommandHandler("stop", stop_receiving_messages))

    # ... (existing code)

    # conversation handler for entering trade or calculating trade information
    dp.add_handler(conv_handler)

    # message handler for all messages that are not included in conversation handler
    dp.add_handler(MessageHandler(Filters.text, unknown_command))

    # log all errors
    dp.add_error_handler(error)

    # listens for incoming updates from Telegram
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=APP_URL + TOKEN)
    updater.idle()

    return

if __name__ == '__main__':
    main()
