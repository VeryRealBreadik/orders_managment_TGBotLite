import gspread
from google.oauth2.service_account import Credentials


class GSheet:
    def __init__(self, scopes, credentials, sheet_id, table_range):
        self.credentials = Credentials.from_service_account_file(credentials, scopes=scopes)
        self.client = gspread.authorize(self.credentials)
        self.sheet = self.client.open_by_key(sheet_id).sheet1
        self.table_range = table_range
        self.row_template = {"company":1, "pallets":2, "boxes":3, "sum":4}
        self.sheet_template = [["Компания/Заказчик", "Количество паллетов", "Количество коробок", "Сумма заказа"]]
        self.load_sheet_template()


    def load_sheet_template(self):
        if not self.sheet.row_values(1):
            self.sheet.append_rows(values=self.sheet_template, table_range=self.table_range)


    def get_last_row_num(self):
        return len(self.sheet.get_all_values()) + 1


    def get_last_row_values(self):
        last_row = self.get_last_row_num()
        if last_row - 1 > 1:
            return self.sheet.row_values(last_row - 1)
        return None


    def add_n_rows(self, data):
        data_to_add = list(map(lambda x: list(x.values()), data))
        self.sheet.append_rows(data_to_add, table_range=self.table_range)


    def delete_last_row(self):
        self.sheet.delete_rows(self.get_last_row_num() - 1)
