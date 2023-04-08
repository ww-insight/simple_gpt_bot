#!/usr/bin/env python
"""
Simple Bot to reply to Telegram messages.

Four OpenAI models are available to reply to messages
    1. text-davinci-003 - general usage model for text generation
    2. code-davinci-002 - model trained for code generation
    3. code-cushman-001 - model trained for code generation
    4. image-generator - model for image generation from text prompt, also can alter images


To run this code it is required to set environment variables with your OpenAI and Telegram Bot tokens:
export OPENAI_API_KEY="qqq"
export TELEGRAM_BOT_TOKEN="qqq"

"""

import logging
import os
import io
import openai
from PIL import Image
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Getting your OpenAI and Telegram Bot tokens from env variables
bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
openai.api_key = os.environ["OPENAI_API_KEY"]

# Setting up default model for the bot
open_ai_engine = "text-davinci-003"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start menu for choosing the model to reply to messages
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("code-davinci-002", callback_data="code-davinci-002"),
            InlineKeyboardButton("code-cushman-001", callback_data="code-cushman-001"),
        ],
        [InlineKeyboardButton("text-davinci-003", callback_data="text-davinci-003")],
        [InlineKeyboardButton("image-generator", callback_data="image-generator")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please choose:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    global open_ai_engine
    open_ai_engine = query.data
    logger.info(f"Changing model to {open_ai_engine}")
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")

# TODO: print help messages
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

# Method for replying to user's messages
async def gpt_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text
    message_photo = update.message.photo
    logger.info(f"Running model {open_ai_engine}")
    # if photo attached use image model to create an alternative image
    if message_photo:
        photo_size = message_photo[-1]

        # Download the photo data
        photo_file = await context.bot.get_file(photo_size.file_id)
        jpeg_bytes = await photo_file.download_as_bytearray()
        jpeg_image = Image.open(io.BytesIO(jpeg_bytes))
        png_bytes = io.BytesIO()
        png_image = jpeg_image.convert("RGBA")
        png_image.save(png_bytes, format="PNG")
        img = openai.Image.create_variation(
            image=png_bytes.getvalue(),
            n=1,
            size="1024x1024"
        )
        await update.message.reply_photo(img['data'][0]['url'])
    # if image-generator model chosen - generate image from text prompt
    elif open_ai_engine == 'image-generator':
        img = openai.Image.create(
              prompt=message,
              n=1,
              size="1024x1024"
            )
        await update.message.reply_photo(img['data'][0]['url'])
    # for other choices just reply with chosen model response
    else:
        response = openai.Completion.create(
            engine=open_ai_engine,
            prompt=message,
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.5,
        )
        await update.message.reply_text(response.choices[0].text)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message and photos - replying with currently chosen model
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_reply))
    application.add_handler(MessageHandler(filters.PHOTO, gpt_reply))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()