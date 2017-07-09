"""
This script is a filter for mitmproxy that allows to grab contents of
http://audioclip.naver.com/channels/57 and save it into files. Specifically,
audios (mp4) and scripts (text in Korean) are saved for later studying.

This was made possible by surfing the contents of the channel from the phone,
while redirecting the traffer though a PC and bookmarking visited URLs.

To get this running, do:

0. Install audioclip app on the phone (Android):
    https://play.google.com/store/apps/details?id=com.naver.naveraudio

1. Install mitmproxy certificate on the phone:
    a) Run mitmproxy on PC: $ sudo mitmproxy --host
    b) On the phone settings go to WiFi settings, add manual proxy: 192.168.1.2:8080
    c) On the phone browser go to "mitm.it" to install fake certificate on the phone

2. Run the filtering script on the PC:

    $ sudo mitmdump --hist -s audioclip.py

3. Start surfing the channel, start playing audio episodes. As soon as the
   script sees you visiting known URLs, it will redownload them and save them
   into files. JSON responses and scripts in HTML format will be saved
   into "audioclip-naver-ripped" directory. File "download.sh" will be updated
   in current directory. Run it with "bash download.sh" to download audios using
   aria2c downloader. If you visited the same episode on the phone twice,
   the file will contain duplicates, but don't worry, either "sort -u" it,
   or aria2c will not download the same file twice anyway.
"""
from mitmproxy import flowfilter
from mitmproxy import ctx, http

import logging
logging.basicConfig(filename='naver-audioclip.log',
                    format='%(asctime)s %(levelname)s: (%(name)s) %(message)s',
                    level=logging.INFO)
_logger = logging.getLogger('audioclip')

# Sample URLs
#    GET https://apis.naver.com/audioclip/audioclip/channels/57?msgpad=1499603266060&md=C9Z86rOcx0eikSqQ36LNdpq3uxk%3D HTTP/2.0
#        ← 200 application/json 875b 498ms
#    GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes?sortKey=approvalYmdt&limit=50&offset=0&sortType=DESC&msgpad=1499603266690&md=AxBrYN2MGbJLv3KXEx%2FkxVIyWKs%3D HTTP/2.0
#        ← 200 application/json 10.88k 629ms
# >> GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121/audio?msgpad=1499603801930&md=UzBVDx9jBIgdzL1eOwen0ZhyFNw%3D HTTP/2.0
#        ← 200 application/json 3.51k 603ms
#    GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121?msgpad=1499603802241&md=Jdz1GStNcAT4sSAGyInZ9BW%2FCMI%3D HTTP/2.0
#        ← 200 application/json 17.28k 520ms


# /usr/lib/python3.6/site-packages/mitmproxy/export.py
def curl_command(flow: http.HTTPFlow) -> str:
    data = "curl "

    request = flow.request.copy()
    request.decode(strict=False)

    for k, v in request.headers.items(multi=True):
        data += "-H '%s:%s' " % (k, v)

    if request.method != "GET":
        data += "-X %s " % request.method

    data += "'%s'" % request.url

    if request.content:
        data += " --data-binary '%s'" % _native(request.content)

    return data


FLOW_FILTER = '~u channels/57'
from handler import RequestHandler

#addons = [Filter()]
def request(flow) -> None:
    filter_ = flowfilter.parse(FLOW_FILTER)
    if flowfilter.match(filter_, flow):
        _logger.info("handle request: %s%s", flow.request.host, flow.request.path)
        request_handler = RequestHandler()
        request_handler(flow.request.path, flow)

_logger.info('audioclip module has been imported')
