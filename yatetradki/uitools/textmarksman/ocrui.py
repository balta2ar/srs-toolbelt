import logging
import sys
from dataclasses import dataclass
from os.path import basename

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL.ImageQt import ImageQt
import pyqtgraph as pg
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from tesserocr import PSM
from tesserocr import PyTessBaseAPI
from tesserocr import RIL
from tesserocr import get_languages

from weight import get_pil_image_weight

FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def by_value(pairs, value):
    for k, v in pairs:
        if v == value:
            return k
    raise ValueError('No key found for value: {}'.format(value))


def by_key(pairs, key):
    for k, v in pairs:
        if k == key:
            return v
    raise ValueError('No value found for key: {}'.format(key))


def pil_image_to_qpixmap(image):
    filename = '/tmp/ocrui-image.png'
    image.save(filename)
    return QPixmap(filename)

@dataclass
class Box:
    x1: int
    y1: int
    x2: int
    y2: int
    weight: float
    text: str


class Menu(QMainWindow):
    COLORS = ['Red', 'Black', 'Blue', 'Green', 'Yellow']
    SIZES = [1, 3, 5, 7, 9, 11]
    default_title = "OCR Tool"
    RIL_MODES = [
        (RIL.BLOCK, 'BLOCK'),
        (RIL.PARA, 'PARA'),
        (RIL.TEXTLINE, 'TEXTLINE'),
        (RIL.WORD, 'WORD'),
        (RIL.SYMBOL, 'SYMBOL'),
    ]
    PSM_MODES = [
        (PSM.AUTO, 'AUTO'),
        (PSM.AUTO_ONLY, 'AUTO_ONLY'),
        (PSM.AUTO_OSD, 'AUTO_OSD'),
        (PSM.CIRCLE_WORD, 'CIRCLE_WORD'),
        (PSM.COUNT, 'COUNT'),
        (PSM.OSD_ONLY, 'OSD_ONLY'),
        (PSM.RAW_LINE, 'RAW_LINE'),
        (PSM.SINGLE_BLOCK, 'SINGLE_BLOCK'),
        (PSM.SINGLE_BLOCK_VERT_TEXT, 'SINGLE_BLOCK_VERT_TEXT'),
        (PSM.SINGLE_CHAR, 'SINGLE_CHAR'),
        (PSM.SINGLE_COLUMN, 'SINGLE_COLUMN'),
        (PSM.SINGLE_LINE, 'SINGLE_LINE'),
        (PSM.SINGLE_WORD, 'SINGLE_WORD'),
        (PSM.SPARSE_TEXT, 'SPARSE_TEXT'),
        (PSM.SPARSE_TEXT_OSD, 'SPARSE_TEXT_OSD'),
    ]

    # numpy_image is the desired image we want to display given as a numpy array.
    def __init__(self, numpy_image=None, snip_number=None, start_position=(100, 100, 1000, 800)):
        super().__init__()

        self.drawing = False
        self.brushSize = 3
        self.brushColor = Qt.red
        self.lastPoint = QPoint()
        self.total_snips = 0
        self.title = Menu.default_title
        self.lang = 'nor'
        self.psm = PSM.AUTO
        self.ril = RIL.WORD
        self.boxes = []

        def set_lang(action):
            logging.info('lang={}'.format(action.text()))
            lang_button.setText('lang={}'.format(action.text()))
            self.lang = action.text()

        def set_psm(action):
            logging.info('PSM={}'.format(action.text()))
            page_segmentation_mode_button.setText('PSM={}'.format(action.text()))
            self.psm = by_value(Menu.PSM_MODES, action.text())

        def set_ril(action):
            logging.info('RIL={}'.format(action.text()))
            page_iteration_level_button.setText('RIL={}'.format(action.text()))
            self.ril = by_value(Menu.RIL_MODES, action.text())

        def threshold_slider_released():
            value = self.threshold_slider.value()
            logging.info('threshold={}'.format(value))
            self.update_layers()
            self.update()

        run_ocr_action = QAction('Run OCR', self)
        run_ocr_action.setStatusTip('Run OCR on the current image')
        run_ocr_action.triggered.connect(self.run_ocr)

        lang_button = QPushButton('lang={}'.format(self.lang))
        lang_menu = QMenu()
        where, langs = get_languages()
        for lang in langs:
            lang_menu.addAction(lang)
        lang_button.setMenu(lang_menu)
        lang_menu.triggered.connect(set_lang)

        page_segmentation_mode_button = QPushButton('PSM={}'.format(by_key(self.PSM_MODES, self.psm)))
        psm_menu = QMenu()
        for (_, mode) in Menu.PSM_MODES:
            psm_menu.addAction(mode)
        page_segmentation_mode_button.setMenu(psm_menu)
        psm_menu.triggered.connect(set_psm)

        page_iteration_level_button = QPushButton('RIL={}'.format(by_key(self.RIL_MODES, self.ril)))
        ril_menu = QMenu()
        for (_, mode) in Menu.RIL_MODES:
            ril_menu.addAction(mode)
        page_iteration_level_button.setMenu(ril_menu)
        ril_menu.triggered.connect(set_ril)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.setValue(90)
        self.threshold_slider.sliderReleased.connect(threshold_slider_released)

        self.histogram_widget = pg.PlotWidget()

        # New snip
        new_snip_action = QAction('New', self)
        new_snip_action.setShortcut('Ctrl+N')
        new_snip_action.setStatusTip('Snip!')
        new_snip_action.triggered.connect(self.new_image_window)

        # Brush color
        brush_color_button = QPushButton("Brush Color")
        colorMenu = QMenu()
        for color in Menu.COLORS:
            colorMenu.addAction(color)
        brush_color_button.setMenu(colorMenu)
        colorMenu.triggered.connect(lambda action: change_brush_color(action.text()))

        # Brush Size
        brush_size_button = QPushButton("Brush Size")
        sizeMenu = QMenu()
        for size in Menu.SIZES:
            sizeMenu.addAction("{0}px".format(str(size)))
        brush_size_button.setMenu(sizeMenu)
        sizeMenu.triggered.connect(lambda action: change_brush_size(action.text()))

        # Save
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save')
        save_action.triggered.connect(self.save_file)

        # Exit
        exit_window = QAction('Exit', self)
        exit_window.setShortcut('Ctrl+Q')
        exit_window.setStatusTip('Exit application')
        exit_window.triggered.connect(self.close)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(run_ocr_action)
        self.toolbar.addWidget(lang_button)
        self.toolbar.addWidget(page_segmentation_mode_button)
        self.toolbar.addWidget(page_iteration_level_button)
        # self.toolbar.addAction(new_snip_action)
        # self.toolbar.addAction(save_action)
        # self.toolbar.addWidget(brush_color_button)
        # self.toolbar.addWidget(brush_size_button)
        self.toolbar.addAction(exit_window)
        # self.toolbar.addWidget(self.threshold_slider)
        two_level_widget = QWidget(self.toolbar)
        two_level_layout = QVBoxLayout()
        two_level_widget.setLayout(two_level_layout)
        two_level_layout.addWidget(self.histogram_widget)
        two_level_layout.addWidget(self.threshold_slider)

        # two_level_widget.setMaximumHeight(100)
        self.toolbar.addWidget(two_level_widget)
        # self.toolbar.setMinimumHeight(100)

        # self.snippingTool = SnippingTool.SnippingWidget()
        self.setGeometry(*start_position)

        # From the second initialization, both arguments will be valid
        if numpy_image is not None and snip_number is not None:
            self.background = self.convert_numpy_img_to_qpixmap(numpy_image)
            self.change_and_set_title("Snip #{0}".format(snip_number))
        else:
            self.background_filename = "page1.jpg"
            self.overlay_filename = "overlay.png"
            self.background = QPixmap(self.background_filename)
            self.change_and_set_title(Menu.default_title)

        # self.resize(self.background.width(), self.background.height() + self.toolbar.height())
        self.show()

        def change_brush_color(new_color):
            self.brushColor = eval("Qt.{0}".format(new_color.lower()))

        def change_brush_size(new_size):
            self.brushSize = int(''.join(filter(lambda x: x.isdigit(), new_size)))

    # def set_background(self, filename):
    #     self.background_filename = filename
    #     self.background = QPixmap(filename)

    def run_ocr(self):
        logging.info('Running OCR: lang={}, psm={}, ril={}'.format(self.lang, self.psm, self.ril))
        with PyTessBaseAPI(lang=self.lang, psm=self.psm) as api:
            # api.SetImage(self.image)
            api.SetImageFile(self.background_filename)
            # mode_dir = ensure_dir('out{}'.format(mode))
            components = api.GetComponentImages(self.ril, True)
            print('components', len(components))
            print('components', components)
            self.boxes = []

            for i, (im, comp, _, _) in enumerate(components):
                # im -- PIL image object
                x, y, w, h = comp['x'], comp['y'], comp['w'], comp['h']
                weight = float(get_pil_image_weight(im))
                logging.info('weight: %s', weight)
                api.SetRectangle(x, y, w, h)
                text = api.GetUTF8Text()
                self.boxes.append(Box(x, y, x + w, y + h, weight, text))

        self.boxes.sort(key=lambda box: box.weight)
        self.update_layers()
        self.update()
        logging.info('OCR finished')

    def update_layers(self):
        boxes = self.boxes
        if len(boxes) == 0: return
        delta = boxes[-1].weight - boxes[0].weight
        threshold = self.threshold_slider.value() / 100.0
        threshold = boxes[0].weight + delta * threshold
        logging.info('min=%s, max=%s, delta=%s, threshold=%s', boxes[0].weight, boxes[-1].weight, delta, threshold)

        weights = []
        with Image.open(self.background_filename) as orig:
            draw = ImageDraw.Draw(orig)
            for box in boxes:
                weights.append(box.weight)
                if box.weight < threshold:
                    continue
                draw.rectangle((box.x1, box.y1, box.x2, box.y2), outline='red')
                # im.save('{}/{:05d}.png'.format(mode_dir, i))
            # orig.save(self.overlay_filename)
            # self.background = QPixmap(self.overlay_filename)
            self.background = pil_image_to_qpixmap(orig)
        y, x = np.histogram(weights, bins=np.linspace(boxes[0].weight, boxes[-1].weight, 50))
        self.histogram_widget.plot(x, y, clear=True, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        self.histogram_widget.plot([threshold, threshold], [0, max(y)], brush=(255, 0, 0, 255))
        # self.histogram_widget.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))

    # snippingTool.start() will open a new window, so if this is the first snip, close the first window.
    def new_image_window(self):
        # if self.snippingTool.background:
        #     self.close()
        self.total_snips += 1
        # self.snippingTool.start()

    def save_file(self):
        file_path, name = QFileDialog.getSaveFileName(self, "Save file", self.title, "PNG Image file (*.png)")
        if file_path:
            self.background.save(file_path)
            self.change_and_set_title(basename(file_path))
            print(self.title, 'Saved')

    def change_and_set_title(self, new_title):
        self.title = new_title
        self.setWindowTitle(self.title)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = QRect(0, self.toolbar.height(), self.background.width(), self.background.height())
        painter.drawPixmap(rect, self.background)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastPoint = event.pos() - QPoint(0, self.toolbar.height())

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing:
            painter = QPainter(self.background)
            painter.setPen(QPen(self.brushColor, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.lastPoint, event.pos() - QPoint(0, self.toolbar.height()))
            self.lastPoint = event.pos() - QPoint(0, self.toolbar.height())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False

    # TODO exit application when we exit all windows
    def closeEvent(self, event):
        event.accept()

    @staticmethod
    def convert_numpy_img_to_qpixmap(np_img):
        height, width, channel = np_img.shape
        bytesPerLine = 3 * width
        return QPixmap(QImage(np_img.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainMenu = Menu()
    sys.exit(app.exec_())
