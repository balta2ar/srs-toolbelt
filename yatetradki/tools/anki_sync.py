"""
This is a small script that runs Anki, waits for it to sync the db,
and closes. No error checking. This is used to sync db from cron.

Run as follows:

    PYTHONPATH=/usr/share/anki xvfb-run python2 anki_sync.py

"""
import sys
sys.path.insert(0, '/usr/share/anki')

from anki.lang import _
from aqt.qt import *
from aqt import AnkiApp, setupLang


def main(delay):
    app = AnkiApp(sys.argv)
    QCoreApplication.setApplicationName("Anki")

    if app.secondInstance():
        print('Anki is already running')
        return

    from aqt.profiles import ProfileManager
    pm = ProfileManager('', '')
    setupLang(pm, app)
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
            set_timer()
            return
        else:
            mw.onClose()
            mw.close()
            app.closeAllWindows()
            app.quit()

    def set_timer():
        timer = QTimer(mw)
        timer.setSingleShot(True)
        timer.connect(timer, SIGNAL('timeout()'), handler)
        timer.start(delay)

    set_timer()

    app.exec_()


if __name__ == '__main__':
    delay = 60000
    if len(sys.argv) > 1:
        delay = int(sys.argv[1])
    main(delay)
