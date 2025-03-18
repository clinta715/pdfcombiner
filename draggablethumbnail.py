from PyQt6.QtWidgets import QWidget  # Base widget class
from PyQt6.QtCore import QPoint, Qt  # QPoint for position, Qt for enums
from PyQt6.QtGui import QMouseEvent  # Mouse event handling

class DraggableThumbnail(QWidget):
    """Custom widget for draggable thumbnails"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.drag_start_position = QPoint()
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QWidget:hover {
                border: 1px solid #888;
                background-color: #f0f0f0;
            }
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10:
            return

        # Get the current position in the grid
        layout = self.parent.thumbnail_layout
        index = layout.indexOf(self)

        # Calculate new position based on mouse
        pos = self.mapToParent(event.position().toPoint())

        # Find the widget under the mouse position
        target_index = -1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.geometry().contains(pos):
                target_index = i
                break

        # If we found a target position and it's different from current
        if target_index != -1 and target_index != index:
            # Remove all widgets from layout
            widgets = []
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    widgets.append(item.widget())

            # Reorder widgets
            widgets.insert(target_index, widgets.pop(index))

            # Add widgets back in new order
            for i, widget in enumerate(widgets):
                row = i // 3
                col = i % 3
                layout.addWidget(widget, row, col)

            # Update the order of PDF paths
            self.parent.update_pdf_order()
