from config import *
from telethon import TelegramClient


bot = TelegramClient(bot_name, api_id, api_hash).start(bot_token=bot_token)
