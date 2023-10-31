#!/usr/bin/env python

#
# Use this simple bot to normalize & compress audio messages sent to the audio cards channel.
#
import logging
import subprocess
from os import environ
from os.path import expanduser, expandvars, exists
from tempfile import TemporaryDirectory

from telegram import Bot, Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, Updater, filters)

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

def compress(original, result: str):
    # cmd = ["ffmpeg", "-i", original,
    #     "-filter:a", "loudnorm,dynaudnorm,speechnorm,loudnorm",
    #     "-ac", "1", "-c:a", "libopus", "-b:a", "32k",
    #     "-vbr", "on", "-ar", "16000", "-compression_level", "10",
    #     "-f", "ogg",
    #     result]
    cmd = ["ffmpeg", "-i", original,
        "-filter:a", "loudnorm,dynaudnorm,speechnorm,loudnorm",
        "-ac", "1", "-c:a", "libmp3lame",
        result]
    logging.info('Running command: %s', ' '.join(cmd))
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

async def audio_handler(update: Update, context):
    logging.info('Message: %s', update.effective_message)
    ts = update.effective_message.date.strftime('%Y%m%d-%H%M%S')
    yyyymm = update.effective_message.date.strftime('d%Y%m')
    with TemporaryDirectory() as tmpdir:
        file = await update.effective_message.voice.get_file()
        base = tmpdir + "/" + ts #update.effective_message.voice.file_unique_id
        await file.download_to_drive(base)
        compressed = base + ".mp3"
        compress(base, compressed)
        with open(compressed, 'rb') as audio:
            caption = update.effective_message.caption or ''
            caption = f'#compressed #card #{yyyymm}\n{caption}'.strip()
            logging.info('Sending audio: %s', caption)
            await context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=audio,
                                         title=ts, caption=caption)

def main():
    load_env('~/.telegram')
    token = environ.get('TELEGRAM_COMPRESS_AUDIO_BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, audio_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
