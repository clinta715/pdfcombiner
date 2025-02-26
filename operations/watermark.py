import os
from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtGui import QColor

class Watermark:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
    def add_text_watermark(self, pdf_path, text, font_size, opacity, rotation, color, position):
        try:
            if not os.path.exists(pdf_path):
                raise ValueError("PDF file does not exist")
                
            if not pdf_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")
                
            if not text:
                raise ValueError("Watermark text cannot be empty")
                
            if self.parent_window:
                self.parent_window.show_status_message("Adding watermark...")
                self.parent_window.update_status_label("Processing watermark")
                self.parent_window.show_progress(0, 100)

            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from io import BytesIO

            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            can.setFont("Helvetica", font_size)
            can.setFillColorRGB(color.redF(), color.greenF(), color.blueF(), opacity)

            width, height = A4
            text_width = can.stringWidth(text, "Helvetica", font_size)

            if position == "Center":
                x = (width - text_width) / 2
                y = height / 2
            elif position == "Top Left":
                x = 50
                y = height - 50
            elif position == "Top Right":
                x = width - text_width - 50
                y = height - 50
            elif position == "Bottom Left":
                x = 50
                y = 50
            elif position == "Bottom Right":
                x = width - text_width - 50
                y = 50

            can.saveState()
            can.translate(x, y)
            can.rotate(rotation)
            can.drawString(0, 0, text)
            can.restoreState()
            can.save()

            watermark_pdf = PdfReader(packet)
            original_pdf = PdfReader(pdf_path)
            output_pdf = PdfWriter()

            total_pages = len(original_pdf.pages)
            for i in range(total_pages):
                if self.parent_window:
                    progress = int((i + 1) / total_pages * 100)
                    self.parent_window.show_progress(progress)
                    self.parent_window.update_status_label(f"Processing page {i+1}/{total_pages}")
                    QApplication.processEvents()

                page = original_pdf.pages[i]
                page.merge_page(watermark_pdf.pages[0])
                output_pdf.add_page(page)

            temp_file = pdf_path + '.tmp'
            with open(temp_file, 'wb') as f:
                output_pdf.write(f)

            os.replace(temp_file, pdf_path)

            if self.parent_window:
                self.parent_window.show_status_message("Watermark added successfully", 3000)
                self.parent_window.hide_progress()

        except Exception as e:
            if self.parent_window:
                self.parent_window.show_status_message(f"Watermark error: {str(e)}", 5000)
                self.parent_window.hide_progress()
            raise
