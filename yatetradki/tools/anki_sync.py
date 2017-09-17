"""
This is a small script that runs Anki, waits for it to sync the db,
and closes. No error checking. This is used to sync db from cron.

Run as follows:

    PYTHONPATH=/usr/share/anki xvfb-run python2 anki_sync.py

"""
import time
import sys
sys.path.insert(0, '/usr/share/anki')

from anki.lang import _
from aqt.qt import *
from aqt import AnkiApp, setupLang


def main(delay):
    from PyQt4.QtCore import QTimer
    app = AnkiApp(sys.argv)
    QCoreApplication.setApplicationName("Anki")

    if app.secondInstance():
        print('Anki is already running')
        return

    from aqt.profiles import ProfileManager
    pm = ProfileManager('', '')
    setupLang(pm, app)
    pm.load('bz')
    pm.profile['autoSync'] = True
    pm.ensureProfile()

    def dummy(*args, **kwargs):
        pass

    # load the main window
    import aqt.main
    mw = aqt.main.AnkiQt(app, pm, [])

    # prevent Anki from showing main window
    mw.show = dummy
    mw.activateWindow = dummy
    mw.raise_ = dummy

    def handler():
        if mw.state == 'sync':
            # print('state sync')
            set_timer()
            return
        else:
            # print('state NOT sync')
            mw.onClose()
            mw.close()
            app.closeAllWindows()
            app.quit()

    def set_timer():
        timer = QTimer(mw)
        timer.setSingleShot(True)
        timer.connect(timer, SIGNAL('timeout()'), handler)
        timer.start(delay)

    def start_sync():
        # print('timer start_sync')
        mw.onSync(auto=True)

    set_timer()
    QTimer.singleShot(5000, start_sync)

    # print(dir(mw))
    #print('executing app')
    #mw.setupProgress()
    #mw.progress.start(immediate=True)
    #mw.progress._lastUpdate = time.time()
    #mw.onSync()
    app.exec_()


if __name__ == '__main__':
    delay = 60000
    if len(sys.argv) > 1:
        delay = int(sys.argv[1])
    main(delay)
