import io
from datetime import datetime

from django.conf import settings
from django.http import FileResponse
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib import styles, colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate
from reportlab.platypus.paragraph import Paragraph


def get_shopping_cart_pdf():
    styles = getSampleStyleSheet()
    styles['Heading1'].fontName = 'DejaVuSansMono'
    styles['Heading2'].fontName = 'DejaVuSansMono'
    styles['Normal'].fontName = 'DejaVuSansMono'

    registerFont(TTFont(
        'DejaVuSansMono',
        f'{settings.BASE_DIR}{settings.STATIC_URL}/DejaVuSansMono.ttf',
        'UTF-8')
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, rightMargin=10 * mm, leftMargin=10 * mm, topMargin=10 * mm,
        bottomMargin=10 * mm, pagesize=A4,
        title='Список покупок',
        creator="robky")

    story = []

    width, _ = portrait(A4)
    drawing = Drawing(width - 20, 1)
    drawing.add(Line(0, 0, width - 60, 0))
    story.append(drawing)

    story.append(Paragraph('Сформирован: ' + datetime.today().strftime(
        '%d/%m/%Y %H:%M'), styles['Normal']))
    story.append(Paragraph('<br />\nСписок покупок:', styles['Heading1']))

    data = [
        ['Продукт', 'Ед.изм.', 'Кол-во'],
        ['Шпроты', 'банка', '36'],
        ['Огурцы', 'шт', '5346'],
        ['Молоко', 'л', '2']
    ]

    table = Table(data, colWidths=[12 * cm, 3 * cm, 3 * cm])

    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
        ('SIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (1, 0), (1, -1), 'CENTRE'),
        ('ALIGN', (2, 0), (2, -1), 'CENTRE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONT', (0, 0), (-1, -1), 'DejaVuSansMono'),

    ]))
    story.append(table)
    story.append(Paragraph('<br />\n <br />\n'))

    drawing2 = Drawing(width - 20, 1)
    drawing2.add(Line(0, 0, width - 60, 0))
    story.append(drawing2)

    address_name = 'foodgram-project-react'
    address = '<link href="' + 'https://github.com/robky/foodgram-project-react' + '">' + address_name + '</link>'
    story.append(Paragraph(
        '<br />\nДанный файл подготовлен в рамках учебного проекта: ' + address,
        styles['Heading2']))

    doc.build(story)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True,
                        filename='shopping_cart.pdf')
