import os
import asyncio

from dotenv import load_dotenv
from modules import load_gsheet, start_bot

from modules.bot.bot import Bot


load_dotenv("essentials/.env")
scopes = [os.getenv("SCOPES")]
credentials = os.getenv("CREDENTIALS_FILE")
sheet_id = os.getenv("SHEET_ID")
table_range = os.getenv("TABLE_RANGE")
load_gsheet(scopes=scopes, credentials=credentials, sheet_id=sheet_id, table_range=table_range)


async def main():
    await start_bot(bot_token=os.getenv("BOT_TOKEN"))

    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
