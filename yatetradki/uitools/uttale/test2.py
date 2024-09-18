from PySide6.QtWidgets import QApplication, QTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

class ClickableTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMouseTracking(True)  # Enable mouse tracking

    # Overriding mousePressEvent to capture clicks inside the QTextEdit
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            # Emit signal or call the parent function to handle the click
            parent = self.parentWidget()
            if parent:
                parent.handle_sentence_click(cursor)
        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # Use the custom ClickableTextEdit
        self.text_edit = ClickableTextEdit(self)

        # Step 1: Add sentences in a flowing paragraph with spans
        self.sentences = [
            "Sentence 1: Hello world! ",
            "Sentence 2: This is another sentence. ",
            "Sentence 3: PySide6 is awesome! ",
            "Sentence 4: Click any sentence to highlight it."
        ]
        self.highlighted_style = "background-color: yellow; font-weight: bold;"
        self.normal_style = ""

        # Create HTML string with spans for each sentence
        self.html_text = ''.join([f'<span id="sentence-{i}" style="{self.normal_style}">{sentence}</span>'
                                  for i, sentence in enumerate(self.sentences)])
        self.text_edit.setHtml(self.html_text)

        # Add the QTextEdit to the layout
        self.layout.addWidget(self.text_edit)

        self.current_sentence_idx = -1

    # Step 2: Handle mouse clicks to highlight a sentence
    def handle_sentence_click(self, cursor):
        sentence_idx = self.get_clicked_sentence_index(cursor)

        if sentence_idx is not None:
            # Reset previous sentence style if any
            if self.current_sentence_idx >= 0:
                self.set_sentence_style(self.current_sentence_idx, self.normal_style)

            # Highlight the clicked sentence
            self.set_sentence_style(sentence_idx, self.highlighted_style)
            self.current_sentence_idx = sentence_idx

    # Step 3: Find which sentence was clicked by comparing cursor position
    def get_clicked_sentence_index(self, cursor):
        cursor.select(QTextCursor.WordUnderCursor)
        clicked_word = cursor.selectedText()

        if clicked_word:
            # Find the sentence that contains the clicked word
            for i, sentence in enumerate(self.sentences):
                if clicked_word in sentence:
                    return i
        return None

    # Step 4: Update the sentence style
    def set_sentence_style(self, index, style):
        sentence_id = f"sentence-{index}"
        self.html_text = self.html_text.replace(f'<span id="{sentence_id}" style="{self.normal_style}">', 
                                                f'<span id="{sentence_id}" style="{style}">')
        self.html_text = self.html_text.replace(f'<span id="{sentence_id}" style="{self.highlighted_style}">', 
                                                f'<span id="{sentence_id}" style="{style}">')
        self.text_edit.setHtml(self.html_text)

    # Step 5: Exit on Escape key
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

# Step 6: Run the application
if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.setWindowTitle("Clickable Flowing Text Sentences")
    window.show()

    app.exec()
