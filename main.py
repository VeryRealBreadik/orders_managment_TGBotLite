import os
import asyncio

from dotenv import load_dotenv
from modules import load_gsheet, start_bot

from modules.bot.bot import Bot


load_dotenv("essentials/.env")
scopes = [os.getenv("SCOPES")]
credentials = os.getenv("CREDENTIALS_FILE")
sheet_id = os.getenv("SHEET_ID")
load_gsheet(scopes=scopes, credentials=credentials, sheet_id=sheet_id)


async def main():
    await start_bot(os.getenv("BOT_TOKEN"))

    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
