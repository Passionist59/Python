import sys

sys.path.append("/usr/src/app/api")
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, \
    Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


class DataToPdf():
    """
    Export a list of dictionaries to a table in a PDF file.
    """

    def __init__(self, fields, data, table_col_widths, first_title='Global Summary', second_title = 'Individual Response summary', lang = 'en'):
        self.fields = fields
        self.data = data
        self.size = len(fields)
        self.table_col_widths = table_col_widths
        self.first_title = first_title
        self.second_title = second_title
        self.lang = lang

    def export(self, filename, data_align='LEFT', table_halign='LEFT'):

        def _footer(canvas, doc):
            canvas.saveState()
            width, height = 8 * inch, 1 * inch
            footer = Image(f'/usr/src/app/api/footer_{self.lang}.png', hAlign='CENTER', width=width, height=height)
            footer.drawOn(canvas, 2, 2)
            canvas.restoreState()

        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        styleH = styles['Heading1']
        story = []
        story.append(Paragraph(self.first_title, styleH))
        story.append(Spacer(1, 0.25 * inch))
        converted_data = self.__convert_data()
        i = 0
        for data in converted_data:
            table = Table(data, hAlign=table_halign, colWidths=self.table_col_widths[i])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), data_align),
                ('INNERGRID', (0, 0), (-1, -1), 0.50, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ])
            )
            if i == len(self.table_col_widths) - 1:
                story.append(Spacer(1, 0.25 * inch))
                story.append(Paragraph(self.second_title, styleH))
                story.append(Spacer(1, 0.25 * inch))
            story.append(table)
            i += 1

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    def __convert_data(self):
        result = []
        for i in list(range(self.size)):
            keys, names = zip(*[[k, n] for k, n in self.fields[i]])
            new_data = [names]
            for d in self.data[i]:
                new_data.append([d[k] for k in keys])
            result.append(new_data)
        return result
