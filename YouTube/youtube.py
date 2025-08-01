# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL | LISA-KOREA/YouTube-Video-Download-Bot

# [⚠️ Do not change this repo link ⚠️] :- https://github.com/LISA-KOREA/YouTube-Video-Download-Bot

import os
import logging
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Youtube.config import Config
from Youtube.forcesub import handle_force_subscribe

youtube_dl_username = None  
youtube_dl_password = None 

@Client.on_message(filters.regex(r'^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+'))
async def process_youtube_link(client, message):
    if Config.CHANNEL:
        fsub = await handle_force_subscribe(client, message)
        if fsub == 400:
            return
    youtube_link = message.text
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Best Quality", callback_data=f"download|best|{youtube_link}")],
        [InlineKeyboardButton("1080p", callback_data=f"download|1080p|{youtube_link}")],
        [InlineKeyboardButton("2K", callback_data=f"download|2k|{youtube_link}")],
        [InlineKeyboardButton("4K", callback_data=f"download|4k|{youtube_link}")],
        [InlineKeyboardButton("Medium Quality", callback_data=f"download|medium|{youtube_link}")],
        [InlineKeyboardButton("Low Quality", callback_data=f"download|low|{youtube_link}")]
    ])
    
    await message.reply_text("**Getting Available Formats**", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^download\|'))
async def handle_download_button(client, callback_query):
    quality, youtube_link = callback_query.data.split('|')[1:]

    quality_format = {
        'best': 'best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '2k': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
        '4k': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        'medium': 'best[height<=480]',
        'low': 'best[height<=360]'
    }.get(quality, 'best')

    try:
        await callback_query.message.edit_text("**Downloading video...**")

        ydl_opts = {
            'format': quality_format,
            'outtmpl': 'downloaded_video_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'progress_hooks': [lambda d: print(f"[yt_dlp] {d.get('status')}")],
            'cookiefile': 'cookies.txt'
        }

        if Config.HTTP_PROXY:
            ydl_opts['proxy'] = Config.HTTP_PROXY
        if youtube_dl_username:
            ydl_opts['username'] = youtube_dl_username
        if youtube_dl_password:
            ydl_opts['password'] = youtube_dl_password

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_link, download=False)
            video_id = info_dict.get('id')
            title = info_dict.get('title')
            duration = info.get("duration", 0)

            if title and video_id:
                ydl.download([youtube_link])
                await callback_query.message.edit_text("**Uploading video...**")

                video_filename = f"downloaded_video_{video_id}.mp4"
                if os.path.exists(video_filename):
                    await client.send_video(
                        callback_query.message.chat.id,
                        video=open(video_filename, 'rb'),
                        caption=title,
                        duration=duration
                    )
                    os.remove(video_filename)

                await callback_query.message.edit_text("✅ **Successfully Uploaded!**")
            else:
                logging.error("No video streams found.")
                await callback_query.message.edit_text("❌ Error: No downloadable video found.")

    except yt_dlp.utils.DownloadError as e:
        logging.exception("Error downloading YouTube video: %s", e)
        await callback_query.message.edit_text("❌ Error: The video is unavailable. It may have been removed or is restricted.")
    except Exception as e:
        logging.exception("Error processing YouTube link: %s", e)
        await callback_query.message.edit_text("❌ Error: Failed to process the YouTube link. Please try again later.")
