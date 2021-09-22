"""
See examples here:
https://github.com/Azure-Samples/cognitive-services-speech-sdk/blob/master/samples/python/console/speech_synthesis_sample.py

You may need to set this in ArchLinux:

    SSL_CERT_DIR=/etc/ssl/certs AZURE_KEY=<key> AZURE_REGION=eastus python3 ./azure_cognitive_speech.py
"""

import sys
from os import remove
from time import sleep
from random import choice

from azure.cognitiveservices.speech import (
    AudioDataStream,
    CancellationReason,
    ResultReason,
    SpeechConfig,
    SpeechSynthesizer,
)
from yatetradki.tools.log import get_logger
from yatetradki.utils import convert_wav_to_mp3, must_env

_logger = get_logger('azure_cognitive_speech')

norsk = "Forrige uke var det høstferie i Trondheim, og studentene på norskkurset hadde fri"
engelsk = "A simple test to write to a file."

# cheerful, chat, customerservice
# <mstts:express-as style="cheerful">
#   This is awesome!
# </mstts:express-as>

THROTTLE_DELAY = 3.0
SSML_TEMPLATE = '''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
  <voice name="{0}">
      {1}
  </voice>
</speak>
'''


def format_template(voice, text):
    data = SSML_TEMPLATE.format(voice, text)
    with open('/tmp/azure.xml', 'w') as f:
        f.write(data)
    return data


def norwegian_synthesize(text, mp3):
    voices = ['nb-NO-PernilleNeural', 'nb-NO-FinnNeural', 'nb-NO-IselinNeural']
    voice = choice(voices)
    return synthesize(voice, text, mp3)


def english_synthesize(text, mp3):
    voices = ['en-US-ChristopherNeural', 'en-US-GuyNeural']
    voice = choice(voices)
    return synthesize(voice, text, mp3)


def synthesize_file(filename, mp3):
    voice = 'nb-NO-FinnNeural'
    text = open(filename).read().strip()
    synthesize(voice, text, mp3)


def synthesize(voice, text, mp3):
    sleep(THROTTLE_DELAY)
    speech_key = must_env('AZURE_KEY')
    service_region = must_env('AZURE_REGION')

    speech_config = SpeechConfig(subscription=speech_key, region=service_region)
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    ssml = format_template(voice, text)
    result = synthesizer.speak_ssml_async(ssml).get()
    _logger.debug('speak_ssml_async result: %s', result)

    if result.reason == ResultReason.SynthesizingAudioCompleted:
        stream = AudioDataStream(result)
        wav = mp3 + '.wav'
        stream.save_to_wav_file(wav)
        convert_wav_to_mp3(wav, mp3)
        remove(wav)
        _logger.info("Azure: Speech synthesized for text [%s], and the audio was saved to [%s]", text, mp3)
        return True

    if result.reason == ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        _logger.error("Speech synthesis canceled: %s", cancellation_details.reason)
        if cancellation_details.reason == CancellationReason.Error:
            _logger.error("Error details: %s", cancellation_details.error_details)

    else:
        _logger.error('Unknown error: %s', result.cancellation_details)

    return False


#norwegian_synthesize(norsk, '/tmp/azure.mp3')

if __name__ == '__main__':
    text, mp3 = sys.argv[1:3]
    synthesize_file(text, mp3)
