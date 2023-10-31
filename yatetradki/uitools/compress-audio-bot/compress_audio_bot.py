#!/usr/bin/env python

#
# Use this simple bot to normalize & compress audio messages sent to the audio cards channel.
#
import logging
import subprocess
from os import environ
from tempfile import TemporaryDirectory

from telegram import Bot, Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, Updater, filters)

TOKEN = environ.get('TELEGRAM_COMPRESS_AUDIO_BOT_TOKEN')

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def audio_handler(update: Update, context):
    with TemporaryDirectory() as tmpdir:
        file = await update.effective_message.voice.get_file()
        download_path = tmpdir + "/" + update.effective_message.voice.file_unique_id
        await file.download_to_drive(download_path)
        compressed_path = download_path + "_compressed.ogg"

        cmd = ["ffmpeg", "-i", download_path,
            "-filter:a", "loudnorm,dynaudnorm,speechnorm,loudnorm",
            "-ac", "1", "-c:a", "libopus", "-b:a", "24k",
            "-vbr", "on", "-ar", "16000", "-compression_level", "10",
            "-f", "ogg",
            compressed_path]
        logger.info('Running command: %s', ' '.join(cmd))
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with open(compressed_path, 'rb') as audio:
            await context.bot.send_voice(chat_id=update.effective_message.chat_id, voice=audio)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, audio_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
