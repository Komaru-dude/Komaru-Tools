import asyncio
import os
from pyrogram import Client
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
token = os.getenv("BOT_API_TOKEN")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=token) if not os.path.exists("my_bot.session") else Client("my_bot")

server = FastAPI()

@server.get("/user/{username}")
async def get_user_id(username: str):
    try:
        user = await app.get_users(username)
        return {"user_id": user.id}
    except Exception as e:
        return {"error": str(e)}

async def start_pyrogram():
    """ Запуск Pyrogram-бота в фоне """
    await app.start()
    print("Pyrogram бот запущен")
    await asyncio.Event().wait()

# Запускаем Pyrogram-бота отдельно
loop = asyncio.get_event_loop()
loop.create_task(start_pyrogram())