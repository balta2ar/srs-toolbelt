# vim: set fileencoding=utf8 :

import re
from os.path import isfile
from os.path import dirname
from os import makedirs
from os import remove
import json
import glob
import logging
import datetime

import requests

_logger = logging.getLogger('handler')

# Sample URLs
#    GET https://apis.naver.com/audioclip/audioclip/channels/57?msgpad=1499603266060&md=C9Z86rOcx0eikSqQ36LNdpq3uxk%3D HTTP/2.0
#        ← 200 application/json 875b 498ms
#    GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes?sortKey=approvalYmdt&limit=50&offset=0&sortType=DESC&msgpad=1499603266690&md=AxBrYN2MGbJLv3KXEx%2FkxVIyWKs%3D HTTP/2.0
#        ← 200 application/json 10.88k 629ms
# >> GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121/audio?msgpad=1499603801930&md=UzBVDx9jBIgdzL1eOwen0ZhyFNw%3D HTTP/2.0
#        ← 200 application/json 3.51k 603ms
#    GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121?msgpad=1499603802241&md=Jdz1GStNcAT4sSAGyInZ9BW%2FCMI%3D HTTP/2.0
#        ← 200 application/json 17.28k 520ms

RX_CHANNELS = re.compile(r'audioclip/channels/(\d+)\?')
RX_CHANNELS_EPISODES = re.compile(r'audioclip/channels/(\d+)/episodes\?')
RX_CHANNELS_EPISODES_AUDIO = re.compile(r'audioclip/channels/(\d+)/episodes/(\d+)/audio\?')
RX_CHANNELS_EPISODES_DESCRIPTION = re.compile(r'audioclip/channels/(\d+)/episodes/(\d+)\?')
RX_CHANNELS_EPISODES_DESCRIPTION_FILENAME = re.compile(r'channels-(\d+)-episodes-(\d+)')
DOWNLOAD_COMMAND = "aria2c -o '%s' '%s'"


def mkpath(filename):
    makedirs(dirname(filename), exist_ok=True)


def remove_file(filename):
    try:
        remove(filename)
    except Exception:
        pass


def spit_json(filename, json_data):
    # if not isfile(filename):
    mkpath(filename)
    with open(filename, 'w', encoding='utf8') as file_:
        data = json.dumps(json_data, indent=4, ensure_ascii=False)
        file_.write(data)


def slurp_json(filename):
    with open(filename) as file_:
        return json.load(file_)


def replay_flow(flow, filename):
    """
    Inspired by: http://docs.mitmproxy.org/en/latest/scripting/overview.html
    See: mitmproxy/mitmproxy/addons/export.py
    Or: /usr/lib/python3.6/site-packages/mitmproxy/export.py
    """
    _logger.info('replaying flow %s to filename %s', flow, filename)
    url_without_query = flow.request.url.split("?", 1)[0]
    params = list(flow.request.query.fields)
    headers = flow.request.headers.copy()
    for x in (":authority", "host", "content-length"):
        headers.pop(x, None)

    response = requests.get(
        url_without_query,
        params=params,
        headers=headers
    )
    _logger.info('response: %s', response)
    _logger.info('response text: %s', response.text)
    result = response.json()
    spit_json(filename, result)
    return result

    # # requests adds those by default.
    # for x in (":authority", "host", "content-length"):
    #     headers.pop(x, None)
    # writearg("headers", dict(headers))
    # try:
    #     if "json" not in flow.request.headers.get("content-type", ""):
    #         raise ValueError()
    #     writearg("json", json.loads(flow.request.text))
    # except ValueError:
    #     writearg("data", flow.request.content)

    # code.seek(code.tell() - 2)  # remove last comma
    # code.write(")")
    # code.write("")
    # code.write("print(response.text)")


def write_standard_html_header(title, writer):
    w = writer
    w('<meta charset="UTF-8">')
    w('<!doctype html>')
    w('<html>')

    w('<head>')
    w('  <meta charset="utf-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w('  <title>%s</title>' % title)
    w('  <link rel="stylesheet" href="mini.css">')
    w('</head>')


def write_episode_script(filename, episode_json):
    with open(filename, 'w', encoding='utf8') as file_:
        def w(msg):
            file_.write(msg)
            file_.write('\n')

        title = 'Channel {channelNo} ({channelId}): {channelName} -' \
            ' Episode {episodeNo}: {episodeTitle}'.format_map(episode_json)
        write_standard_html_header(title, w)

        duration = int(episode_json['playTime'] / 60.)
        date = datetime.datetime.utcfromtimestamp(
            int(episode_json['approvalTimestamp'] / 1e3))
        date = date.strftime('%Y-%m-%d %H:%M:%S')
        img_url = 'channels-{channelNo}-episodes-{episodeNo}-image.jpg'.format_map(episode_json)

        w('<body>')
        w('  <h1>Channel {channelNo} ({channelId}): {channelName}</h1>'.format_map(episode_json))
        w('    <img src="%s"/>' % img_url)
        w('    <h2>Episode {episodeNo}: {episodeTitle}</h2>'.format_map(episode_json))
        w('      <p>Episode description: {description}</p>'.format_map(episode_json))
        w('      <p>Episode date: %s</p>' % date)
        w('      <p>Episode duration: %s minutes</p>' % duration)

        for chapter in episode_json['chapters']:
            w('        <h3>Chapter {chapterNo}: {chapterTitle}</h3>'.format_map(chapter))
            for section in chapter['sections']:
                for line in section['description'].splitlines():
                    line = line.strip()
                    if line:
                        w('          <p>%s</p>' % line)
        w('</body></html>')


def get_bitrate(encodingOptionId):
    return int(re.sub(r'\D', '', encodingOptionId))


def get_url_of_type(type_, urls):
    for url_dict in urls:
        if type_ == url_dict['type']:
            return url_dict['url']
    return None


def append_to_file(filename, line):
    with open(filename, 'a') as file_:
        file_.write(line)
        file_.write('\n')


# def download_file(filename, url):
#     response = requests.get(url)
#     with open(filename, 'w') as file_:
#         file_.write(response.text)


def download_episode_image(image_filename, episode_json):
    line = DOWNLOAD_COMMAND % (image_filename, episode_json['imageUrl'])
    append_to_file('download_images.sh', line)


def download_episode_audio(filename, episode_json, downloader):
    url = None
    bitrate = None
    for info in episode_json['audioPlayUrlInfos']:
        current_bitrate = get_bitrate(info['encodingOptionId'])
        if bitrate is None or current_bitrate > bitrate:
            url = get_url_of_type('download', info['urls'])
            bitrate = current_bitrate
    downloader(filename, url)


class RequestHandler:
    _DOWNLOAD_COMMANDS_FILENAME = 'download.sh'

    def _match(self, request_path, flow, rx, handler):
        match = rx.search(request_path)
        if match is not None:
            handler(match, flow)
            return True
        return False

    def _download(self, filename, url):
        _logger.info('Downloading episode audio %s to filename %s', url, filename)
        line = DOWNLOAD_COMMAND % (filename, url)
        append_to_file(RequestHandler._DOWNLOAD_COMMANDS_FILENAME, line)

    def __call__(self, request_path, flow):
        self._match(request_path, flow, RX_CHANNELS, self.handle_channels)
        self._match(request_path, flow, RX_CHANNELS_EPISODES, self.handle_channels_episodes)
        self._match(request_path, flow, RX_CHANNELS_EPISODES_AUDIO, self.handle_channels_episodes_audio)
        self._match(request_path, flow, RX_CHANNELS_EPISODES_DESCRIPTION, self.handle_channels_episodes_description)

    def handle_channels(self, match, flow):
        _logger.info('handle_channel_description %s', match)
        filename = './audioclip-naver-ripped/channels-%s-response.json' % (match.group(1),)
        replay_flow(flow, filename)

    def handle_channels_episodes(self, match, flow):
        _logger.info('handle_channels_episodes %s', match)
        filename = './audioclip-naver-ripped/channels-%s-episodes-response.json' % (match.group(1),)
        replay_flow(flow, filename)

    def handle_channels_episodes_audio(self, match, flow):
        _logger.info('handle_channels_episodes_audio %s', match)
        filename = './audioclip-naver-ripped/channels-%s-episodes-%s-audio-response.json' % (
            match.group(1), match.group(2))
        episode_json = replay_flow(flow, filename)

        audio_filename = './audioclip-naver-ripped/channels-%s-episodes-%s-audio.mp4' % (
            match.group(1), match.group(2))
        download_episode_audio(audio_filename, episode_json, self._download)

    def handle_channels_episodes_description(self, match, flow):
        _logger.info('handle_channels_episodes_description %s', match)
        filename = './audioclip-naver-ripped/channels-%s-episodes-%s-description-response.json' % (
            match.group(1), match.group(2))
        episode_json = replay_flow(flow, filename)

        script_filename = './audioclip-naver-ripped/channels-%s-episodes-%s-script.html' % (
            match.group(1), match.group(2))
        write_episode_script(script_filename, episode_json)

        image_filename = './audioclip-naver-ripped/channels-%s-episodes-%s-image.jpg' % (
            match.group(1), match.group(2))
        download_episode_image(image_filename, episode_json)


def init_logging(filename):
    logging.basicConfig(
        filename=filename,
        format='%(asctime)s %(levelname)s: (%(name)s) %(message)s',
        level=logging.INFO)


def download_images(json_wildcard):
    init_logging(None)
    for filename in glob.glob(json_wildcard):
        _logger.info('Extracting image from %s', filename)
        episode_json = slurp_json(filename)
        match = RX_CHANNELS_EPISODES_DESCRIPTION_FILENAME.search(filename)
        image_filename = './audioclip-naver-ripped/channels-%s-episodes-%s-image.jpg' % (
            match.group(1), match.group(2))
        download_episode_image(image_filename, episode_json)


def generate_html(json_wildcard):
    init_logging(None)
    for filename in glob.glob(json_wildcard):
        _logger.info('Generating HTML %s', filename)
        episode_json = slurp_json(filename)
        match = RX_CHANNELS_EPISODES_DESCRIPTION_FILENAME.search(filename)
        script_filename = './audioclip-naver-ripped/channels-%s-episodes-%s-script.html' % (
            match.group(1), match.group(2))
        write_episode_script(script_filename, episode_json)


def generate_index(json_wildcard):
    init_logging(None)
    index_filename = './audioclip-naver-ripped/index.html'

    def w(line):
        append_to_file(index_filename, line)

    remove_file(index_filename)
    write_standard_html_header('Index', w)
    w('<body>')
    filenames = sorted(glob.glob(json_wildcard),
                       key=lambda x: int(re.sub(r'\D', '', x)))
    for filename in filenames:
        _logger.info('Adding to index %s', filename)
        episode_json = slurp_json(filename)
        match = RX_CHANNELS_EPISODES_DESCRIPTION_FILENAME.search(filename)

        script_filename = 'channels-%s-episodes-%s-script.html' % (
            match.group(1), match.group(2))

        duration = int(episode_json['playTime'] / 60.)
        date = datetime.datetime.utcfromtimestamp(
            int(episode_json['approvalTimestamp'] / 1e3))
        date = date.strftime('%Y-%m-%d %H:%M:%S')
        img_url = 'channels-{channelNo}-episodes-{episodeNo}-image.jpg'.format_map(episode_json)

        # w('  <h1>Channel {channelNo} ({channelId}): {channelName}</h1>'.format_map(episode_json))
        w('<div class="index_entry">')
        w('  <a href="%s"><img class="index_img" src="%s"/></a>' % (script_filename, img_url))
        w('  <p class="index_p">Episode {episodeNo}: {episodeTitle}'.format_map(episode_json))
        # w('      <p>Description: {description}</p>'.format_map(episode_json))
        w('  <br><span>Date: %s</span>' % date)
        w('  <br><span>Duration: %s minutes</span></p>' % duration)
        w('</div>')
        w('<hr>')
        w('')

        # write_episode_script(script_filename, episode_json)
        # break
    w('</body></html>')
