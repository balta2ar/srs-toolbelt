import os
import sys
import fileinput
from subprocess import Popen, PIPE, STDOUT #, TimeoutExpired
from os.path import join, expanduser, expandvars, basename
import logging

sys.path.insert(0, '/usr/share/anki')

_logger = logging.getLogger('audio')


def get_pronunciation(text):
    """
    A set of hacks that are pulled togeher to run awesometts and produce
    pronunciation for a word.
    """

    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    sip.setapi('QUrl', 2)

    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QTimer
    sound_path = [None]
    app = QApplication([])

    def fake_awesometts():
        class FakeAddons(object):
            def GetAddons(self):
                return []
            GetAddons.__bases__ = [object]

        import aqt
        aqt.addons = FakeAddons()

        sys.path.insert(0, expanduser('~/Documents/Anki/addons'))
        import awesometts

        #text = 'furfurfur'
        # text = 'smear'
        group = {u'presets': [u'Howjsay (en)', u'Oxford Dictionary (en-US)', u'Collins (en)', u'Google Translate (en-US)', u'Baidu Translate (en)', u'ImTranslator (VW Paul)'], u'mode': u'ordered'}
        presets = {u'ImTranslator (VW Paul)': {u'voice': u'VW Paul', u'speed': 0, u'service': u'imtranslator'}, u'Linguatec (ko, Sora)': {u'voice': u'Sora', u'service': u'linguatec'}, u'Collins (en)': {u'voice': u'en', u'service': u'collins'}, u'NeoSpeech (ko, Jihun)': {u'voice': u'Jihun', u'service': u'neospeech'}, u'Baidu Translate (en)': {u'voice': u'en', u'service': u'baidu'}, u'Google Translate (en-US)': {u'voice': u'en-US', u'service': u'google'}, u'Acapela Group (ko, Minji)': {u'voice': u'Minji', u'service': u'acapela'}, u'ImTranslator (ko, VW Yumi)': {u'voice': u'VW Yumi', u'speed': 0, u'service': u'imtranslator'}, u'Howjsay (en)': {u'voice': u'en', u'service': u'howjsay'}, u'Oxford Dictionary (en-US)': {u'voice': u'en-US', u'service': u'oxford'}, u'NAVER Translate (ko)': {u'voice': u'ko', u'service': u'naver'}}
        def on_okay(path):
            sound_path[0] = path
            app.quit()
        def on_fail(path):
            app.quit()
        callbacks = {
            'okay': on_okay,
            'fail': on_fail,
        } #{'fail': <function fail at 0x7fe53b8aa668>, 'then': <function <lambda> at 0x7fe53b8aa758>, 'done': <function done at 0x7fe55084fed8>, 'okay': <function okay at 0x7fe550afa758>, 'miss': <function miss at 0x7fe53b8aa6e0>}
        want_human = False
        note = None # <anki.notes.Note object at 0x7fe550871990>

        awesometts.router._logger = _logger
        awesometts.router.group(text, group, presets, callbacks, want_human, note)

    # fake_awesometts()
    QTimer.singleShot(1, fake_awesometts)
    app.exec_()
    return sound_path[0]


def get_pronunciation_call(text):
    """
    Call this module as a process. This way it is more reliable and less
    error-prone as all that Qt machinery is reinitialized each time.
    """
    proc = Popen(['python2', __file__], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    outs, errs = proc.communicate(input='%s\n' % text)
    result = outs.strip().decode('utf8')
    return result if result else None


def main():
    for line in fileinput.input():
        print(get_pronunciation(line))


if __name__ == '__main__':
    main()
