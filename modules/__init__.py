from .bot.bot import Bot
from .gsheets.gsheets import GSheet
import sys


def load_gsheet(scopes, credentials, sheet_id):
    global gsheet

    gsheet = GSheet(scopes, credentials, sheet_id)

    if not gsheet:
        print("Error: Failed to load Google Sheet.")
        sys.exit()


async def start_bot(bot_token, authorized_user):
    global gsheet

    bot = Bot(bot_token, gsheet, authorized_user)
    await bot.start()
