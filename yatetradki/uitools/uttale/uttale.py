import sys
import subprocess
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QProcess
import webvtt

class SubtitleSearchApp(QMainWindow):
    def __init__(self, folder):
        super().__init__()
        self.folder = os.path.abspath(folder)
        self.init_ui()
        self.current_process = None

    def init_ui(self):
        self.setWindowTitle('Subtitle Search App')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.perform_search)  # Add Enter key functionality
        search_button = QPushButton('Search')
        search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)

        layout.addLayout(search_layout)

        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.results_list)

        central_widget.setLayout(layout)

    def perform_search(self):
        query = self.search_input.text()
        if not query:
            return

        command = ['rg', '-n', '--no-heading', '-g', '*.vtt', query, self.folder]
        result = subprocess.run(command, capture_output=True, text=True)

        self.results_list.clear()
        for line in result.stdout.splitlines():
            file_path, line_number, content = line.split(':', 2)
            relative_path = os.path.relpath(file_path, self.folder)  # Get relative path
            item = QListWidgetItem(f"{relative_path}:{line_number} - {content}")
            item.setData(Qt.ItemDataRole.UserRole, (file_path, int(line_number)))
            self.results_list.addItem(item)

    def on_item_clicked(self, item):
        file_path, raw_line_number = item.data(Qt.ItemDataRole.UserRole)
        self.play_audio(file_path, raw_line_number)

    def play_audio(self, vtt_file, raw_line_number):
        media_file = os.path.splitext(vtt_file)[0] + '.ogg'
        
        if not os.path.exists(media_file):
            QMessageBox.warning(self, "Error", f"Media file not found: {media_file}")
            return

        try:
            with open(vtt_file, 'r') as f:
                vtt_content = f.readlines()

            subtitle_index = self.get_subtitle_index(vtt_content, raw_line_number)
            if subtitle_index is None:
                raise ValueError(f"No subtitle found for line number: {raw_line_number}")

            vtt = webvtt.read(vtt_file)
            caption = vtt[subtitle_index]
            start_time = self.time_to_seconds(caption.start)
            end_time = self.time_to_seconds(caption.end)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error processing VTT file: {str(e)}")
            return

        self.play_audio_segment(media_file, start_time, end_time)

    def get_subtitle_index(self, vtt_content, raw_line_number):
        subtitle_count = -1
        for i, line in enumerate(vtt_content):
            if i + 1 >= raw_line_number:
                return max(0, subtitle_count)
            if line.strip() and not line.strip().isdigit() and ' --> ' not in line:
                subtitle_count += 1
        return None

    def time_to_seconds(self, time_str):
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)

    def play_audio_segment(self, media_file, start_time, end_time):
        if self.current_process and self.current_process.state() == QProcess.ProcessState.Running:
            self.current_process.kill()

        duration = end_time - start_time
        command = [
            'mplayer',
            '-ss', str(start_time),
            '-endpos', str(duration),
            '-really-quiet',
            media_file
        ]

        self.current_process = QProcess(self)
        self.current_process.start('mplayer', command[1:])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv) < 2:
        print("Usage: python script.py /path/to/folder")
        sys.exit(1)
    folder = sys.argv[1]
    window = SubtitleSearchApp(folder)
    window.show()
    sys.exit(app.exec())