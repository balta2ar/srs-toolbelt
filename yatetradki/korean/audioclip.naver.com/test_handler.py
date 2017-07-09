from unittest import TestCase
from mock import MagicMock, Mock

from handler import RequestHandler

# Sample URLs
#    GET https://apis.naver.com/audioclip/audioclip/channels/57?msgpad=1499603266060&md=C9Z86rOcx0eikSqQ36LNdpq3uxk%3D HTTP/2.0
#        ← 200 application/json 875b 498ms
#    GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes?sortKey=approvalYmdt&limit=50&offset=0&sortType=DESC&msgpad=1499603266690&md=AxBrYN2MGbJLv3KXEx%2FkxVIyWKs%3D HTTP/2.0
#        ← 200 application/json 10.88k 629ms
# >> GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121/audio?msgpad=1499603801930&md=UzBVDx9jBIgdzL1eOwen0ZhyFNw%3D HTTP/2.0
#        ← 200 application/json 3.51k 603ms
#    GET https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121?msgpad=1499603802241&md=Jdz1GStNcAT4sSAGyInZ9BW%2FCMI%3D HTTP/2.0
#        ← 200 application/json 17.28k 520ms

class TestHandler(TestCase):
    def setUp(self):
        self._handler = RequestHandler()

    def test_handle_channel(self):
        url = 'https://apis.naver.com/audioclip/audioclip/channels/57msgpad=1499603266060&md=C9Z86rOcx0eikSqQ36LNdpq3uxk%3D'
        self._handler.handle_channels = Mock()
        self._handler(url, None)
        self.assertEqual(0, len(self._handler.handle_channels.call_args_list))

        url = 'https://apis.naver.com/audioclip/audioclip/channels/57?msgpad=1499603266060&md=C9Z86rOcx0eikSqQ36LNdpq3uxk%3D'
        self._handler.handle_channels = Mock()
        self._handler(url, None)
        self.assertEqual(1, len(self._handler.handle_channels.call_args_list))

    def test_handle_channels_episodes(self):
        url = 'https://apis.naver.com/audioclip/audioclip/channels/57/episodes?sortKey=approvalYmdt&limit=50&offset=0&sortType=DESC&msgpad=1499603266690&md=AxBrYN2MGbJLv3KXEx%2FkxVIyWKs%3D'
        self._handler.handle_channels_episodes = Mock()
        self._handler(url, None)
        self.assertEqual(1, len(self._handler.handle_channels_episodes.call_args_list))

    def test_handle_channels_episodes_audio(self):
        url = 'https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121/audio?msgpad=1499603801930&md=UzBVDx9jBIgdzL1eOwen0ZhyFNw%3D'
        self._handler.handle_channels_episodes_audio = Mock()
        self._handler(url, None)
        self.assertEqual(1, len(self._handler.handle_channels_episodes_audio.call_args_list))

    def test_handle_channels_episodes_description(self):
        url = 'https://apis.naver.com/audioclip/audioclip/channels/57/episodes/121?msgpad=1499603802241&md=Jdz1GStNcAT4sSAGyInZ9BW%2FCMI%3D'
        self._handler.handle_channels_episodes_description = Mock()
        self._handler(url, None)
        self.assertEqual(1, len(self._handler.handle_channels_episodes_description.call_args_list))
