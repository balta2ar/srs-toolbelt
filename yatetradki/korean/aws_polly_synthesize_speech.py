# coding=utf-8
import boto3


def norwegian_synthesize(word, filename):
    # Synthesize the sample text, saving it in an MP3 audio file
    polly_client = boto3.client('polly')
    response = polly_client.synthesize_speech(VoiceId='Liv',
                                              OutputFormat='mp3',
                                              LanguageCode='nb-NO',
                                              Text=word)
    with open(filename, 'wb') as file:
        file.write(response['AudioStream'].read())
    return response
