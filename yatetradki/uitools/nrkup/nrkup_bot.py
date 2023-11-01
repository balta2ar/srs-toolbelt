#!/usr/bin/env python

#
# Use this simple bot to normalize & compress audio messages sent to the audio cards channel.
#
import logging
import subprocess
from os import environ
from os.path import expanduser, expandvars, exists
from tempfile import TemporaryDirectory
import requests

from telegram import Bot, Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, Updater, filters)

from episode import Episode

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

def load_env(filename):
    filename = expanduser(expandvars(filename))
    if not exists(filename):
        logging.warning('Missing env file "%s"', filename)
        return
    with open(filename, 'r') as f:
        for line in [x.strip() for x in f.readlines()]:
            if line.startswith('#'): continue
            key, value = line.strip().split('=', 1)
            environ[key] = value

def resolve(url):
    response = requests.get(url, allow_redirects=False)
    return str(response.headers['Location'])

async def fetch(url):
    if url.startswith('https://tv.nrk.no/se?v='): # resolve, use location
        logging.info('Resolving: %s', url)
        url = resolve(url)
    logging.info('Caption: %s', url)
    episode = await Episode.make(url)
    logging.info('Found episode: %s', episode)
    filename = await episode.mp3()
    logging.info('Downloaded: %s', filename)
    return filename

def test_fetch(url):
    from asyncio import new_event_loop
    loop = new_event_loop()
    filename = loop.run_until_complete(fetch(url))
    print(filename)

async def text_handler(update: Update, context):
    logging.info('Message: %s', update.effective_message)
    url = update.effective_message.text.strip().splitlines()[0].strip()
    filename = await fetch(url)
    with open(filename, 'rb') as audio:
        await context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=audio)
        # await update.effective_message.reply_audio(f)

def main():
    load_env('~/.telegram')
    token = environ.get('TELEGRAM_NRKUP_BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()
    # filter = filters.TEXT & (filters.Entity("url") | filters.Entity("text_link"))
    filter = filters.TEXT & filters.Regex(r'https://tv.nrk.no/.*')
    app.add_handler(MessageHandler(filter, text_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
