import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL

BOT_TOKEN = "8869791073:AAHqtAowVzkbrz5yX3M98_a61kaTXIWRXfY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Улучшенные настройки yt-dlp для стабильного поиска
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'default_search': 'ytsearch',
    'quiet': True,
    'noplaylist': True,
}

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Сәлем акпатшам!\n"
        "маган музиканнын атын жбер,мен саган жберем сол музиканды тындайсын!"
    )

@dp.message(F.text)
async def handle_music_search(message: types.Message):
    query = message.text.strip()

    if query.startswith('/'):
        return

    status_msg = await message.answer(f"🔎 Ищу трек: **{query}**...", parse_mode="Markdown")

    loop = asyncio.get_running_loop()
    try:
        audio_info = await loop.run_in_executor(None, download_track, query)
    except Exception as e:
        logging.error(f"Ошибка поиска: {e}")
        await status_msg.edit_text("❌ блә бупипай чота таппадым,кышкене нактырак жберш атын (например: *Kendrick Lamar - Swimming Pools*).")
        return

    file_path = audio_info['file_path']
    title = audio_info.get('title', 'Аудиозапись')
    performer = audio_info.get('uploader', 'Музыка')
    duration = audio_info.get('duration', 0)

    # Проверка лимита Telegram (50 МБ)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 50 * 1024 * 1024:
        await status_msg.edit_text("⚠️ Файл слишком большой (превышает лимит Telegram в 50 МБ).")
        if os.path.exists(file_path):
            os.remove(file_path)
        return

    await status_msg.edit_text("⬆️ Отправляю трек...")

    try:
        audio_file = FSInputFile(file_path)
        await message.answer_audio(
            audio=audio_file,
            title=title,
            performer=performer,
            duration=int(duration)
        )
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.answer("❌ Произошла ошибка при отправке файла.")
    finally:
        await status_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

def download_track(query: str) -> dict:
    # Ищем первое видео по запросу
    search_target = f"ytsearch1:{query}"
    
    with YoutubeDL(YTDL_OPTIONS) as ydl:
        info = ydl.extract_info(search_target, download=True)
        if 'entries' in info and info['entries']:
            video_data = info['entries'][0]
        else:
            video_data = info

        video_id = video_data['id']
        expected_mp3_path = os.path.join('downloads', f"{video_id}.mp3")

        return {
            'file_path': expected_mp3_path,
            'title': video_data.get('title', 'Без названия'),
            'uploader': video_data.get('uploader', 'Неизвестен'),
            'duration': video_data.get('duration', 0)
        }

async def main():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    print("Бот успешно запущен и ждет сообщения!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())