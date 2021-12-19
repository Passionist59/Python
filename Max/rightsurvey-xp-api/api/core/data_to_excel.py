import sys

sys.path.append("/usr/src/app/api")
import xlsxwriter


class DataToExcel():

    def __init__(self, filename, headers, data, detail_header, detail_data):
        self.filename = filename
        self.headers = headers
        self.data = data
        self.detail_header = detail_header
        self.detail_data = detail_data
        self.workbook = xlsxwriter.Workbook(self.filename)

    def export(self, stats_sheetname=None, detail_sheetname=None):
        worksheet_stats = self.workbook.add_worksheet(stats_sheetname)
        if detail_sheetname:
            worksheet_detail = self.workbook.add_worksheet(detail_sheetname)
        row_count = 1
        column_count = 1
        total = len(self.headers)
        for i in list(range(total)):
            worksheet_stats.add_table(row_count, column_count,
                                      row_count + len(self.data[i]) if row_count > 1 else len(self.data[i]) + 1,
                                      len(self.headers[i]),
                                      {'autofilter': False, 'data': self.data[i],
                                       'columns': self.headers[i]})
            row_count += (len(self.data[i]) + 2)

        table_row_count = len(self.detail_data) + 1
        table_column_count = len(self.detail_header)
        if detail_sheetname:
            worksheet_detail.add_table(1, 1, table_row_count, table_column_count,
                                       {'autofilter': False, 'data': self.detail_data, 'columns': self.detail_header})
        self.workbook.close()
