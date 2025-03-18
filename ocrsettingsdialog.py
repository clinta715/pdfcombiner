from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QDialogButtonBox,
)

class OCRSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCR Settings")
        self.setMinimumWidth(400)

        layout = QFormLayout()

        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(["eng", "fra", "spa", "deu", "ita"])
        layout.addRow("Language:", self.language_combo)

        # Quality level
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Fast", "Balanced", "Best"])
        self.quality_combo.setCurrentIndex(1)
        layout.addRow("Quality:", self.quality_combo)

        # Page segmentation mode
        self.psm_combo = QComboBox()
        self.psm_combo.addItems([
            "0 = Orientation and script detection (OSD) only",
            "1 = Automatic page segmentation with OSD",
            "2 = Automatic page segmentation, but no OSD, or OCR",
            "3 = Fully automatic page segmentation, but no OSD (Default)",
            "4 = Assume a single column of text of variable sizes",
            "5 = Assume a single uniform block of vertically aligned text",
            "6 = Assume a single uniform block of text",
            "7 = Treat the image as a single text line",
            "8 = Treat the image as a single word",
            "9 = Treat the image as a single word in a circle",
            "10 = Treat the image as a single character"
        ])
        self.psm_combo.setCurrentIndex(3)
        layout.addRow("Page Segmentation:", self.psm_combo)

        # Image processing options
        self.deskew_check = QCheckBox("Auto deskew")
        self.deskew_check.setChecked(True)
        layout.addRow(self.deskew_check)

        self.clean_check = QCheckBox("Clean images")
        self.clean_check.setChecked(True)
        layout.addRow(self.clean_check)

        # Contrast adjustment
        self.contrast_spin = QDoubleSpinBox()
        self.contrast_spin.setRange(0.5, 2.0)
        self.contrast_spin.setValue(1.0)
        self.contrast_spin.setSingleStep(0.1)
        layout.addRow("Contrast:", self.contrast_spin)

        # Brightness adjustment
        self.brightness_spin = QDoubleSpinBox()
        self.brightness_spin.setRange(0.5, 2.0)
        self.brightness_spin.setValue(1.0)
        self.brightness_spin.setSingleStep(0.1)
        layout.addRow("Brightness:", self.brightness_spin)

        # Threshold
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 255)
        self.threshold_spin.setValue(0)
        self.threshold_spin.setSpecialValueText("Auto")
        layout.addRow("Threshold:", self.threshold_spin)

        # Output destination
        self.output_combo = QComboBox()
        self.output_combo.addItems([
            "Text file (auto-named)",
            "Clipboard",
            "Text window",
            "New PDF file"
        ])
        layout.addRow("Output Destination:", self.output_combo)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.setLayout(layout)
