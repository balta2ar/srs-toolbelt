from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, Qt

# Step 1: Create a custom QLabel that emits a signal when clicked
class ClickableLabel(QLabel):
    clicked = Signal()  # Custom signal to emit on mouse click

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("font-size: 16px; padding: 10px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # Emit the signal when clicked

# Step 2: Create a main widget that contains the layout and labels
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.sentences = [
            "Sentence 1: Hello world!",
            "Sentence 2: This is another sentence.",
            "Sentence 3: PySide6 is awesome!",
            "Sentence 4: Click any sentence to highlight it."
        ]

        # Step 3: Add clickable labels to the layout
        self.labels = []
        for sentence in self.sentences:
            label = ClickableLabel(sentence)
            label.clicked.connect(self.on_label_clicked)
            self.labels.append(label)
            self.layout.addWidget(label)

        self.active_label = None

    # Step 4: Define the behavior when a label is clicked
    def on_label_clicked(self):
        # Reset all labels' style
        for label in self.labels:
            label.setStyleSheet("font-size: 16px; padding: 10px;")

        # Set the style of the clicked label to highlight it
        clicked_label = self.sender()
        clicked_label.setStyleSheet("font-size: 16px; padding: 10px; background-color: yellow;")

        # Keep track of the active label
        self.active_label = clicked_label

# Step 5: Run the application
if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.setWindowTitle("Clickable Sentences")
    window.show()

    app.exec()
