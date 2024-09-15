from .bot.bot import Bot
from .gsheets.gsheets import GSheet
import sys


def load_gsheet(scopes, credentials, sheet_id, table_range):
    global sheet

    sheet = GSheet(scopes=scopes, credentials=credentials, sheet_id=sheet_id, table_range=table_range)

    if not sheet:
        print("Error: Failed to load Google Sheet.")
        sys.exit()


async def start_bot(bot_token):
    global sheet

    bot = Bot(bot_token=bot_token, sheet=sheet)
    await bot.start()
