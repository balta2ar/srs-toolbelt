from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal, Qt

# Step 1: Create a custom QLabel that emits a signal when clicked
class ClickableLabel(QLabel):
    clicked = Signal()  # Custom signal to emit on mouse click

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("font-size: 16px; padding: 10px;")  # Initial styling

    # Overriding the mousePressEvent to emit a signal when clicked
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # Emit the custom signal when clicked


# Step 2: Main window to manage the layout and labels
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # List of sentences to display
        self.sentences = [
            "Sentence 1: Hello world!",
            "Sentence 2: This is another sentence.",
            "Sentence 3: PySide6 is awesome!",
            "Sentence 4: Click any sentence to highlight it."
        ]

        # Store labels for easy access
        self.labels = []

        # Set up each sentence as a clickable label
        for sentence in self.sentences:
            label = ClickableLabel(sentence)
            label.clicked.connect(self.on_label_clicked)  # Connect the clicked signal to a handler
            self.labels.append(label)
            self.layout.addWidget(label)

        # Keep track of the currently highlighted label
        self.active_label = None

        self.setLayout(self.layout)

    # Step 3: Handle label click
    def on_label_clicked(self):
        # Reset the previous label's style if any
        if self.active_label:
            self.active_label.setStyleSheet("font-size: 16px; padding: 10px;")

        # Highlight the clicked label
        clicked_label = self.sender()  # The sender is the clicked label
        clicked_label.setStyleSheet("font-size: 16px; padding: 10px; background-color: yellow;")
        self.active_label = clicked_label

    # Step 4: Exit the application when Escape is pressed
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


# Step 5: Run the application
if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.setWindowTitle("Clickable Labels with Highlight")
    window.show()

    app.exec()
