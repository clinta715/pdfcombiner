from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox  # Updated import

class Watermark:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
    def add_text_watermark(self, pdf_path, text, font_size, opacity, rotation, color, position):
        try:
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

            for i in range(len(original_pdf.pages)):
                page = original_pdf.pages[i]
                page.merge_page(watermark_pdf.pages[0])
                output_pdf.add_page(page)

            temp_file = pdf_path + '.tmp'
            with open(temp_file, 'wb') as f:
                output_pdf.write(f)

            import os
            os.replace(temp_file, pdf_path)

            self.parent_window.show_status_message("Text watermark added successfully!", 3000)

        except Exception as e:
            self.parent_window.show_status_message(f"Watermark error: {str(e)}", 5000)
