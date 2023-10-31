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


async def audio_handler(update: Update, context):
    with TemporaryDirectory() as tmpdir:
        file = await update.effective_message.voice.get_file()
        download_path = tmpdir + "/" + update.effective_message.voice.file_unique_id
        await file.download_to_drive(download_path)
        compressed_path = download_path + "_compressed.ogg"

        cmd = ["ffmpeg", "-i", download_path,
            "-filter:a", "loudnorm,dynaudnorm,speechnorm,loudnorm",
            "-ac", "1", "-c:a", "libopus", "-b:a", "32k",
            "-vbr", "on", "-ar", "16000", "-compression_level", "10",
            "-f", "ogg",
            compressed_path]
        logging.info('Running command: %s', ' '.join(cmd))
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with open(compressed_path, 'rb') as audio:
            await context.bot.send_voice(chat_id=update.effective_message.chat_id, voice=audio)

def main():
    load_env('~/.telegram')
    TOKEN = environ.get('TELEGRAM_COMPRESS_AUDIO_BOT_TOKEN')
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, audio_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
