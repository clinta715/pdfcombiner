# Create permissions dialog
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox

class PermissionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set PDF Permissions")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # Add permission checkboxes
        self.print_check = QCheckBox("Allow Printing")
        self.print_check.setChecked(True)
        layout.addWidget(self.print_check)

        self.modify_check = QCheckBox("Allow Modifications")
        layout.addWidget(self.modify_check)

        self.copy_check = QCheckBox("Allow Copying Text")
        self.copy_check.setChecked(True)
        layout.addWidget(self.copy_check)

        self.annot_check = QCheckBox("Allow Annotations and Forms")
        self.annot_check.setChecked(True)
        layout.addWidget(self.annot_check)

        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_permissions(self):
        """Get selected permissions"""
        return {
            'printing': self.print_check.isChecked(),
            'modify': self.modify_check.isChecked(),
            'copy': self.copy_check.isChecked(),
            'annot-forms': self.annot_check.isChecked()
        }
