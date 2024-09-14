import gspread
from google.oauth2.service_account import Credentials


class GSheet:
    def __init__(self, scopes, credentials, sheet_id):
        self.credentials = Credentials.from_service_account_file(credentials, scopes=scopes)
        self.client = gspread.authorize(self.credentials)
        self.sheet = self.client.open_by_key(sheet_id).sheet1
        self.row_template = {"lastname":1, "name":2, "middlename":3, "company":4, "pallets":5, "boxes":6, "sum":7}
        self.sheet_template = ["Фамилия", "Имя", "Отчество", "Компания", "Количество паллетов", "Количество коробок", "Сумма заказа"]
        self.load_sheet_template()

    def load_sheet_template(self):
        if not self.sheet.row_values(1):
            for i in range(len(self.sheet_template)):
                self.sheet.update_cell(1, i + 1, self.sheet_template[i])

    def get_last_row(self):
        row = 1
        while self.sheet.row_values(row):
            row += 1
        return row

    def add_row(self, data):
        row = self.get_last_row()
        self.sheet.append_row(list(data.values()))

    def delete_last_row(self):
        self.sheet.delete_rows(self.get_last_row() - 1)
