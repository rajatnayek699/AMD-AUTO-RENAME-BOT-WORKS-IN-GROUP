#!/usr/bin/env python3
"""
Auto Rename Bot - Queue System Version
Processes files one by one from a queue to reduce server load
"""

import os
import re
import sys
import time
import json
import math
import asyncio
import logging
import datetime
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Deque
from collections import deque
from dotenv import load_dotenv
from PIL import Image
import motor.motor_asyncio
from pyrogram import Client, filters, __version__, idle
from pyrogram.types import (
    Message, InlineKeyboardButton, InlineKeyboardMarkup, 
    CallbackQuery
)

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================
class Config:
    API_ID = int(os.getenv("API_ID", "25775944"))
    API_HASH = os.getenv("API_HASH", "217e861ebca9da0dd4c17b1abf92636c")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7750507797:AAFT5QgxqdKnqDBu_2ZkjFxo9u5fBNOF5qY")
    ADMIN = [int(admin) for admin in os.getenv("ADMIN", "1869817167,1833881094").split(",")]
    DB_URL = os.getenv("DB_URL", "mongodb+srv://Filex:Guddu8972771037@cluster0.er3kfsr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME = os.getenv("DB_NAME", "Filex")
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1002795055491"))
    START_PIC = os.getenv("START_PIC", "https://graph.org/file/29a3acbbab9de5f45a5fe.jpg")
    WEBHOOK = os.getenv("WEBHOOK", "False").lower() == "true"
    PORT = int(os.getenv("PORT", "8080"))
    BOT_UPTIME = time.time()

class Txt:
    START_TXT = """<b>ʜᴇʏ! {}  

» ɪ ᴀᴍ ᴀᴅᴠᴀɴᴄᴇᴅ ʀᴇɴᴀᴍᴇ ʙᴏᴛ! ᴡʜɪᴄʜ ᴄᴀɴ ᴀᴜᴛᴏʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ғɪʟᴇs ᴡɪᴛʜ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ ᴀɴᴅ ᴛʜᴜᴍʙɴᴀɪʟ ᴀɴᴅ ᴀʟsᴏ sᴇǫᴜᴇɴᴄᴇ ᴛʜᴇᴍ ᴘᴇʀғᴇᴄᴛʟʏ</b>"""
    
    FILE_NAME_TXT = """<b>» <u>sᴇᴛᴜᴘ ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ</u></b>

<b>ᴠᴀʀɪᴀʙʟᴇꜱ :</b>
➲ ᴇᴘɪꜱᴏᴅᴇ - ᴛᴏ ʀᴇᴘʟᴀᴄᴇ ᴇᴘɪꜱᴏᴅᴇ ɴᴜᴍʙᴇʀ  
➲ ꜱᴇᴀꜱᴏɴ - ᴛᴏ ʀᴇᴘʟᴀᴄᴇ ꜱᴇᴀꜱᴏɴ ɴᴜᴍʙᴇʀ  
➲ ǫᴜᴀʟɪᴛʏ - ᴛᴏ ʀᴇᴘʟᴀᴄᴇ ǫᴜᴀʟɪᴛʏ  

<b>‣ ꜰᴏʀ ᴇx:- </b> `/autorename Oᴠᴇʀғʟᴏᴡ [Sseason Eepisode] - [Dual] quality`

<b>‣ /Autorename: ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ꜰɪʟᴇꜱ ʙʏ ɪɴᴄʟᴜᴅɪɴɢ 'ᴇᴘɪꜱᴏᴅᴇ' ᴀɴᴅ 'ǫᴜᴀʟɪᴛʏ' ᴠᴀʀɪᴀʙʟᴇꜱ ɪɴ ʏᴏᴜʀ ᴛᴇxᴛ, ᴛᴏ ᴇxᴛʀᴀᴄᴛ ᴇᴘɪꜱᴏᴅᴇ ᴀɴᴅ ǫᴜᴀʟɪᴛʏ ᴘʀᴇꜱᴇɴᴛ ɪɴ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ꜰɪʟᴇɴᴀᴍᴇ.</b>"""

# ==================== QUEUE SYSTEM ====================
class ProcessingQueue:
    def __init__(self):
        self.queue = deque()
        self.current_task = None
        self.is_processing = False
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.lock = asyncio.Lock()
    
    def add_to_queue(self, message: Message, user_id: int):
        """Add a file to the processing queue"""
        queue_item = {
            'message_id': message.id,
            'chat_id': message.chat.id,
            'user_id': user_id,
            'file_name': '',
            'file_size': 0,
            'media_type': '',
            'added_time': time.time(),
            'status': 'waiting'
        }
        
        # Get file info
        if message.document:
            queue_item['file_name'] = message.document.file_name or "file"
            queue_item['file_size'] = message.document.file_size
            queue_item['media_type'] = 'document'
        elif message.video:
            queue_item['file_name'] = message.video.file_name or "video.mp4"
            queue_item['file_size'] = message.video.file_size
            queue_item['media_type'] = 'video'
        elif message.audio:
            queue_item['file_name'] = message.audio.file_name or "audio.mp3"
            queue_item['file_size'] = message.audio.file_size
            queue_item['media_type'] = 'audio'
        
        self.queue.append(queue_item)
        return len(self.queue)
    
    def get_next_task(self):
        """Get the next task from queue"""
        if self.queue:
            return self.queue[0]
        return None
    
    def remove_current_task(self):
        """Remove the current task after processing"""
        if self.queue:
            self.queue.popleft()
    
    def get_queue_length(self):
        """Get current queue length"""
        return len(self.queue)
    
    def clear_queue(self):
        """Clear the entire queue"""
        self.queue.clear()
    
    def get_queue_info(self):
        """Get detailed queue information"""
        info = {
            'total': len(self.queue),
            'current': self.current_task,
            'is_processing': self.is_processing,
            'completed': self.completed_tasks,
            'failed': self.failed_tasks,
            'waiting_list': []
        }
        
        for i, item in enumerate(self.queue):
            info['waiting_list'].append({
                'position': i + 1,
                'file_name': item['file_name'][:50] if item['file_name'] else 'Unknown',
                'user_id': item['user_id'],
                'waiting_time': time.time() - item['added_time']
            })
        
        return info

# Global queue instance
processing_queue = ProcessingQueue()

# ==================== DATABASE ====================
class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URL)
        self.db = self.client[Config.DB_NAME]
        self.col = self.db.users
    
    def new_user(self, user_id):
        return {
            "_id": int(user_id),
            "join_date": datetime.now().isoformat(),
            "file_id": None,
            "caption": None,
            "metadata": True,
            "title": "Encoded by @Codeflix_Bots",
            "author": "@Codeflix_Bots",
            "artist": "@Codeflix_Bots",
            "audio": "By @Codeflix_Bots",
            "subtitle": "By @Codeflix_Bots",
            "video": "Encoded By @Codeflix_Bots",
            "format_template": None,
            "media_type": "document",
            "ban_status": {
                "is_banned": False,
                "ban_duration": 0,
                "banned_on": datetime.max.isoformat(),
                "ban_reason": ''
            }
        }
    
    async def add_user(self, user_id):
        if not await self.is_user_exist(user_id):
            user = self.new_user(user_id)
            await self.col.insert_one(user)
    
    async def is_user_exist(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return bool(user)
    
    async def total_users_count(self):
        return await self.col.count_documents({})
    
    async def get_all_users(self):
        return self.col.find({})
    
    async def delete_user(self, user_id):
        await self.col.delete_many({"_id": int(user_id)})
    
    async def set_thumbnail(self, user_id, file_id):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"file_id": file_id}})
    
    async def get_thumbnail(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("file_id", None) if user else None
    
    async def set_caption(self, user_id, caption):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"caption": caption}})
    
    async def get_caption(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("caption", None) if user else None
    
    async def set_format_template(self, user_id, format_template):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"format_template": format_template}})
    
    async def get_format_template(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("format_template", None) if user else None
    
    async def set_media_preference(self, user_id, media_type):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"media_type": media_type}})
    
    async def get_media_preference(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("media_type", "document") if user else "document"
    
    async def get_metadata(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("metadata", True) if user else True
    
    async def set_metadata(self, user_id, metadata):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"metadata": metadata}})
    
    async def get_title(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("title", "Encoded by @Codeflix_Bots") if user else "Encoded by @Codeflix_Bots"
    
    async def set_title(self, user_id, title):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"title": title}})
    
    async def get_author(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("author", "@Codeflix_Bots") if user else "@Codeflix_Bots"
    
    async def set_author(self, user_id, author):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"author": author}})
    
    async def get_artist(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("artist", "@Codeflix_Bots") if user else "@Codeflix_Bots"
    
    async def set_artist(self, user_id, artist):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"artist": artist}})
    
    async def get_audio(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("audio", "By @Codeflix_Bots") if user else "By @Codeflix_Bots"
    
    async def set_audio(self, user_id, audio):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"audio": audio}})
    
    async def get_subtitle(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("subtitle", "By @Codeflix_Bots") if user else "By @Codeflix_Bots"
    
    async def set_subtitle(self, user_id, subtitle):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"subtitle": subtitle}})
    
    async def get_video(self, user_id):
        user = await self.col.find_one({"_id": int(user_id)})
        return user.get("video", "Encoded By @Codeflix_Bots") if user else "Encoded By @Codeflix_Bots"
    
    async def set_video(self, user_id, video):
        await self.col.update_one({"_id": int(user_id)}, {"$set": {"video": video}})

# Initialize database
db = Database()

# ==================== UTILITY FUNCTIONS ====================
def humanbytes(size):
    """Convert bytes to human readable format"""
    if not size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "ᴅ, ") if days else "") + \
          ((str(hours) + "ʜ, ") if hours else "") + \
          ((str(minutes) + "ᴍ, ") if minutes else "") + \
          ((str(seconds) + "ꜱ, ") if seconds else "")
    return tmp[:-2] or "0 s"

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["█" for _ in range(math.floor(percentage / 5))]),
            ''.join(["░" for _ in range(20 - math.floor(percentage / 5))])
        )
        
        tmp = f"""\n
<b>» Size</b> : {humanbytes(current)} | {humanbytes(total)}
<b>» Done</b> : {round(percentage, 2)}%
<b>» Speed</b> : {humanbytes(speed)}/s
<b>» ETA</b> : {estimated_total_time if estimated_total_time else "0 s"} """
        
        try:
            await message.edit(
                text=f"{ud_type}\n\n{progress}{tmp}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("• ᴄᴀɴᴄᴇʟ •", callback_data="close")]
                ])
            )
        except:
            pass

# ==================== FILE PROCESSING FUNCTIONS ====================
def extract_season_episode(filename):
    """Extract season and episode numbers from filename"""
    patterns = [
        (r'S(\d+)(?:E|EP)(\d+)', ('season', 'episode')),
        (r'S(\d+)[\s-]*(?:E|EP)(\d+)', ('season', 'episode')),
        (r'Season\s*(\d+)\s*Episode\s*(\d+)', ('season', 'episode')),
        (r'\[S(\d+)\]\[E(\d+)\]', ('season', 'episode')),
        (r'S(\d+)[^\d]*(\d+)', ('season', 'episode')),
        (r'(?:E|EP|Episode)\s*(\d+)', (None, 'episode')),
        (r'\b(\d+)\b', (None, 'episode'))
    ]
    
    for pattern, (season_group, episode_group) in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            season = match.group(1) if season_group else None
            episode = match.group(2) if episode_group else match.group(1)
            return season, episode
    return None, None

def extract_quality(filename):
    """Extract quality information from filename"""
    quality_patterns = [
        (r'\b(\d{3,4}[pi])\b', lambda m: m.group(1)),  # 1080p, 720p
        (r'\b(4k|2160p)\b', lambda m: "4K"),
        (r'\b(2k|1440p)\b', lambda m: "2K"),
        (r'\b(HDRip|HDTV|WEB-DL|WEBRip|BluRay)\b', lambda m: m.group(1)),
        (r'\[(\d{3,4}[pi])\]', lambda m: m.group(1))
    ]
    
    for pattern, extractor in quality_patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return extractor(match)
    return "Unknown"

async def cleanup_files(*paths):
    """Safely remove files if they exist"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
        except Exception as e:
            print(f"Error removing {path}: {e}")

async def process_thumbnail(thumb_path):
    """Process and resize thumbnail image"""
    if not thumb_path or not os.path.exists(thumb_path):
        return None
    
    try:
        with Image.open(thumb_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((320, 320))
            img.save(thumb_path, "JPEG", quality=85)
        return thumb_path
    except Exception as e:
        print(f"Thumbnail processing error: {e}")
        await cleanup_files(thumb_path)
        return None

async def add_metadata_correct(input_path, output_path, user_id):
    """Add metadata to media file - CORRECT VERSION that preserves all tracks"""
    # Find ffmpeg path
    ffmpeg_path = None
    for path in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/bin/ffmpeg']:
        if shutil.which(path):
            ffmpeg_path = path
            break
    
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg not found. Please install ffmpeg: sudo apt-get install ffmpeg")
    
    # Get metadata from database
    title = await db.get_title(user_id)
    artist = await db.get_artist(user_id)
    author = await db.get_author(user_id)
    video_title = await db.get_video(user_id)
    audio_title = await db.get_audio(user_id)
    subtitle_title = await db.get_subtitle(user_id)
    
    # Escape quotes in metadata
    def escape_metadata(text):
        return text.replace('"', '\\"').replace("'", "\\'")
    
    # Build CORRECT ffmpeg command that preserves all tracks
    cmd = [
        ffmpeg_path,
        '-i', input_path,
        '-map', '0',  # Map all streams from input
        '-c:v', 'copy',  # Copy video codec
        '-c:a', 'copy',  # Copy audio codec
        '-c:s', 'copy',  # Copy subtitle codec
        '-metadata', f'title={escape_metadata(title)}',
        '-metadata', f'artist={escape_metadata(artist)}',
        '-metadata', f'author={escape_metadata(author)}',
        '-metadata:s:v', f'title={escape_metadata(video_title)}',
        '-metadata:s:a', f'title={escape_metadata(audio_title)}',
        '-metadata:s:s', f'title={escape_metadata(subtitle_title)}',
        '-y',
        output_path
    ]
    
    print(f"FFmpeg command: {' '.join(cmd)}")
    
    # Execute ffmpeg
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown error"
        print(f"FFmpeg error: {error_msg}")
        
        # Try alternative simpler command
        alt_cmd = [
            ffmpeg_path, '-i', input_path,
            '-map', '0',
            '-c', 'copy',
            '-metadata', f'title={escape_metadata(title)}',
            '-metadata', f'artist={escape_metadata(artist)}',
            '-metadata', f'author={escape_metadata(author)}',
            '-y', output_path
        ]
        
        process2 = await asyncio.create_subprocess_exec(
            *alt_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout2, stderr2 = await process2.communicate()
        
        if process2.returncode != 0:
            error_msg2 = stderr2.decode() if stderr2 else "Unknown error"
            raise RuntimeError(f"FFmpeg error (alternative): {error_msg2}")
    
    # Verify output file exists
    if not os.path.exists(output_path):
        raise RuntimeError("Output file was not created")
    
    # Verify file has content
    if os.path.getsize(output_path) == 0:
        raise RuntimeError("Output file is empty")
    
    return output_path

# ==================== QUEUE WORKER ====================
async def queue_worker():
    """Worker that processes files from the queue one by one"""
    while True:
        try:
            # Wait if queue is empty
            if processing_queue.get_queue_length() == 0:
                await asyncio.sleep(2)
                continue
            
            # Check if already processing
            if processing_queue.is_processing:
                await asyncio.sleep(2)
                continue
            
            # Start processing next task
            async with processing_queue.lock:
                processing_queue.is_processing = True
                task = processing_queue.get_next_task()
                
                if not task:
                    processing_queue.is_processing = False
                    await asyncio.sleep(2)
                    continue
                
                # Update task status
                processing_queue.current_task = task
                task['status'] = 'processing'
                task['start_time'] = time.time()
                
                print(f"Processing task: {task}")
                
                # Try to get the message from Telegram
                try:
                    message = await app.get_messages(
                        chat_id=task['chat_id'],
                        message_ids=task['message_id']
                    )
                    
                    if not message:
                        print(f"Message not found: {task['message_id']}")
                        processing_queue.completed_tasks += 1
                        processing_queue.failed_tasks += 1
                        processing_queue.remove_current_task()
                        processing_queue.is_processing = False
                        processing_queue.current_task = None
                        continue
                    
                    # Process the file
                    await process_queue_file(message, task['user_id'])
                    
                    # Mark task as completed
                    processing_queue.completed_tasks += 1
                    
                except Exception as e:
                    print(f"Error processing task {task['message_id']}: {e}")
                    processing_queue.failed_tasks += 1
                
                finally:
                    # Remove task from queue
                    processing_queue.remove_current_task()
                    processing_queue.is_processing = False
                    processing_queue.current_task = None
                    await asyncio.sleep(1)  # Small delay before next task
        
        except Exception as e:
            print(f"Queue worker error: {e}")
            await asyncio.sleep(5)

async def process_queue_file(message, user_id):
    """Process a single file from the queue"""
    # Check if user has set rename format
    format_template = await db.get_format_template(user_id)
    if not format_template:
        try:
            await app.send_message(
                chat_id=message.chat.id,
                text="❌ Please set a rename format first in private chat!\n"
                     "Use: `/autorename Your Format Here`\n\n"
                     "**Example:** `/autorename {filename} [S{season}E{episode}]`",
                reply_to_message_id=message.id
            )
        except:
            pass
        return
    
    # Get file info
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "file"
        file_size = message.document.file_size
        media_type = "document"
        duration = 0
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video.mp4"
        file_size = message.video.file_size
        media_type = "video"
        duration = message.video.duration
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio.mp3"
        file_size = message.audio.file_size
        media_type = "audio"
        duration = message.audio.duration
    else:
        return
    
    # Extract filename components
    base_name = os.path.splitext(file_name)[0]
    ext = os.path.splitext(file_name)[1] or ('.mp4' if media_type == 'video' else '.mp3')
    
    season, episode = extract_season_episode(base_name)
    quality = extract_quality(base_name)
    
    # Replace variables in template
    new_filename = format_template
    replacements = {
        '{filename}': base_name,
        '{season}': season or '01',
        '{episode}': episode or '01',
        '{quality}': quality,
        '{filesize}': humanbytes(file_size),
        '{duration}': str(timedelta(seconds=duration)) if duration else '00:00:00',
        'Season': season or '01',
        'Episode': episode or '01',
        'QUALITY': quality.upper() if quality != "Unknown" else "HD"
    }
    
    for key, value in replacements.items():
        new_filename = new_filename.replace(key, value)
    
    # Clean filename
    new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename)
    new_filename = new_filename.strip() + ext
    
    # Send processing started message
    status_msg = await app.send_message(
        chat_id=message.chat.id,
        text=f"🔄 **Processing Started**\n"
             f"**File:** `{file_name}`\n"
             f"**Queue Position:** Now Processing\n"
             f"**New Name:** `{new_filename[:50]}`",
        reply_to_message_id=message.id
    )
    
    download_path = f"downloads/{user_id}_{int(time.time())}{ext}"
    
    try:
        # Download with progress
        start_time = time.time()
        await status_msg.edit_text(f"📥 **Downloading...**\n`{file_name}`")
        
        file_path = await message.download(
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading...", status_msg, start_time)
        )
        
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text("❌ Download failed!")
            return
        
        file_size = os.path.getsize(file_path)
        await status_msg.edit_text(f"✅ **Downloaded!**\n\n**File:** `{file_name}`\n**Size:** {humanbytes(file_size)}\n\n⚙️ **Processing file...**")
        
        # Process metadata if enabled
        output_path = file_path
        metadata_enabled = await db.get_metadata(user_id)
        
        if metadata_enabled:
            try:
                metadata_path = f"temp/{user_id}_metadata{ext}"
                await status_msg.edit_text("🔧 **Adding metadata...**")
                output_path = await add_metadata_correct(file_path, metadata_path, user_id)
                await cleanup_files(file_path)  # Remove original
                await status_msg.edit_text(f"✅ **Metadata added successfully!**")
            except Exception as e:
                print(f"Metadata error: {e}")
                await status_msg.edit_text(f"⚠️ Metadata skipped: {str(e)[:100]}")
                output_path = file_path
        else:
            await status_msg.edit_text("ℹ️ **Metadata disabled, skipping...**")
        
        # Get thumbnail
        thumb_path = None
        user_thumb = await db.get_thumbnail(user_id)
        
        if user_thumb:
            try:
                thumb_path = f"temp/{user_id}_thumb.jpg"
                await app.download_media(user_thumb, file_name=thumb_path)
                thumb_path = await process_thumbnail(thumb_path)
            except Exception as e:
                print(f"Thumbnail error: {e}")
        elif media_type == "video" and message.video.thumbs:
            try:
                thumb = message.video.thumbs[0]
                thumb_path = f"temp/{user_id}_video_thumb.jpg"
                await app.download_media(thumb.file_id, file_name=thumb_path)
                thumb_path = await process_thumbnail(thumb_path)
            except Exception as e:
                print(f"Video thumbnail error: {e}")
        
        # Get caption
        caption_template = await db.get_caption(user_id) or "{filename}"
        caption = caption_template.replace("{filename}", os.path.splitext(new_filename)[0])\
                                 .replace("{filesize}", humanbytes(file_size))\
                                 .replace("{duration}", str(timedelta(seconds=duration)) if duration else '00:00:00')
        
        # Get media type preference
        media_pref = await db.get_media_preference(user_id)
        
        await status_msg.edit_text("📤 **Uploading renamed file...**")
        
        # Upload file based on media preference
        upload_start = time.time()
        
        try:
            if media_pref == "document" or media_type == "document":
                await app.send_document(
                    chat_id=message.chat.id,
                    document=output_path,
                    caption=caption[:1024] if caption else None,
                    thumb=thumb_path,
                    file_name=new_filename,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading...", status_msg, upload_start)
                )
            elif media_pref == "video" and media_type == "video":
                await app.send_video(
                    chat_id=message.chat.id,
                    video=output_path,
                    caption=caption[:1024] if caption else None,
                    thumb=thumb_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading...", status_msg, upload_start)
                )
            elif media_pref == "audio" and media_type == "audio":
                await app.send_audio(
                    chat_id=message.chat.id,
                    audio=output_path,
                    caption=caption[:1024] if caption else None,
                    thumb=thumb_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading...", status_msg, upload_start)
                )
            else:
                # Fallback to document
                await app.send_document(
                    chat_id=message.chat.id,
                    document=output_path,
                    caption=caption[:1024] if caption else None,
                    thumb=thumb_path,
                    file_name=new_filename,
                    progress=progress_for_pyrogram,
                    progress_args=("📤 Uploading...", status_msg, upload_start)
                )
            
            await status_msg.delete()
            await app.send_message(
                chat_id=message.chat.id,
                text=f"✅ **File renamed successfully!**\n**New name:** `{new_filename[:50]}`",
                reply_to_message_id=message.id
            )
            
        except Exception as upload_error:
            await status_msg.edit_text(f"❌ **Upload Error:** {str(upload_error)[:200]}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)[:200]}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            await cleanup_files(
                download_path if 'download_path' in locals() else None,
                output_path if 'output_path' in locals() and output_path != download_path else None,
                thumb_path if 'thumb_path' in locals() else None
            )
        except:
            pass

# ==================== BOT CLIENT ====================
# Create necessary directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Initialize bot
app = Client(
    "auto_rename_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=100,
    sleep_threshold=10,
)

# ==================== HANDLERS ====================
# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user = message.from_user
    await db.add_user(user.id)
    
    # Check if photo is sent with /start
    if message.reply_to_message and message.reply_to_message.photo:
        await db.set_thumbnail(user.id, message.reply_to_message.photo.file_id)
        await message.reply_text("✅ Thumbnail saved successfully!")
        return
    
    # Send welcome message
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
        [
            InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Codeflix_Bots'),
            InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')
        ],
        [
            InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')
        ]
    ])
    
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            Txt.START_TXT.format(user.mention),
            reply_markup=buttons
        )

# Autorename command
@app.on_message(filters.command("autorename") & filters.private)
async def autorename_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "**Please provide a rename format!**\n\n"
            "**Example:** `/autorename {filename} [S{season}E{episode}] - {quality}`\n\n"
            "**Available variables:**\n"
            "- `{filename}`: Original filename\n"
            "- `{season}`: Season number\n"
            "- `{episode}`: Episode number\n"
            "- `{quality}`: Video quality\n"
            "- `{filesize}`: File size\n"
            "- `{duration}`: Duration (for videos)"
        )
        return
    
    format_template = message.text.split(" ", 1)[1]
    await db.set_format_template(message.from_user.id, format_template)
    
    await message.reply_text(
        f"**✅ Rename format set successfully!**\n\n"
        f"**Your format:** `{format_template}`\n\n"
        "Now send me any file to rename it automatically."
    )

# Set caption command
@app.on_message(filters.command("set_caption") & filters.private)
async def set_caption_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "**Please provide a caption!**\n\n"
            "**Example:** `/set_caption File: {filename}\nSize: {filesize}\nDuration: {duration}`\n\n"
            "**Available variables:**\n"
            "- `{filename}`: File name\n"
            "- `{filesize}`: File size\n"
            "- `{duration}`: Duration"
        )
        return
    
    caption = message.text.split(" ", 1)[1]
    await db.set_caption(message.from_user.id, caption)
    await message.reply_text("✅ Caption set successfully!")

# View caption command
@app.on_message(filters.command(["see_caption", "view_caption"]) & filters.private)
async def see_caption_handler(client, message):
    caption = await db.get_caption(message.from_user.id)
    if caption:
        await message.reply_text(f"**Your caption:**\n\n`{caption}`")
    else:
        await message.reply_text("❌ No caption set. Use /set_caption to set one.")

# Delete caption command
@app.on_message(filters.command("del_caption") & filters.private)
async def del_caption_handler(client, message):
    await db.set_caption(message.from_user.id, None)
    await message.reply_text("✅ Caption deleted successfully!")

# View thumbnail command
@app.on_message(filters.command(["view_thumb", "viewthumb"]) & filters.private)
async def view_thumb_handler(client, message):
    thumb = await db.get_thumbnail(message.from_user.id)
    if thumb:
        await client.send_photo(message.chat.id, thumb)
    else:
        await message.reply_text("❌ No thumbnail set. Send a photo to set as thumbnail.")

# Delete thumbnail command
@app.on_message(filters.command(["del_thumb", "delthumb"]) & filters.private)
async def del_thumb_handler(client, message):
    await db.set_thumbnail(message.from_user.id, None)
    await message.reply_text("✅ Thumbnail deleted successfully!")

# Set thumbnail from photo
@app.on_message(filters.private & filters.photo)
async def set_thumb_handler(client, message):
    await db.set_thumbnail(message.from_user.id, message.photo.file_id)
    await message.reply_text("✅ Thumbnail saved successfully!")

# Metadata command
@app.on_message(filters.command("metadata") & filters.private)
async def metadata_handler(client, message):
    metadata_status = await db.get_metadata(message.from_user.id)
    status_text = "ON ✅" if metadata_status else "OFF ❌"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Turn ON", callback_data="metadata_on"),
            InlineKeyboardButton("Turn OFF", callback_data="metadata_off")
        ]
    ])
    
    await message.reply_text(
        f"**Metadata Status:** {status_text}\n\n"
        "Use buttons below to toggle metadata.",
        reply_markup=buttons
    )

# Set metadata fields commands
@app.on_message(filters.command("settitle") & filters.private)
async def settitle_handler(client, message):
    if len(message.command) > 1:
        title = message.text.split(" ", 1)[1]
        await db.set_title(message.from_user.id, title)
        await message.reply_text(f"✅ Title set to: `{title}`")
    else:
        await message.reply_text("**Usage:** `/settitle Your Title Here`")

@app.on_message(filters.command("setauthor") & filters.private)
async def setauthor_handler(client, message):
    if len(message.command) > 1:
        author = message.text.split(" ", 1)[1]
        await db.set_author(message.from_user.id, author)
        await message.reply_text(f"✅ Author set to: `{author}`")
    else:
        await message.reply_text("**Usage:** `/setauthor Author Name`")

@app.on_message(filters.command("setartist") & filters.private)
async def setartist_handler(client, message):
    if len(message.command) > 1:
        artist = message.text.split(" ", 1)[1]
        await db.set_artist(message.from_user.id, artist)
        await message.reply_text(f"✅ Artist set to: `{artist}`")
    else:
        await message.reply_text("**Usage:** `/setartist Artist Name`")

@app.on_message(filters.command("setaudio") & filters.private)
async def setaudio_handler(client, message):
    if len(message.command) > 1:
        audio = message.text.split(" ", 1)[1]
        await db.set_audio(message.from_user.id, audio)
        await message.reply_text(f"✅ Audio title set to: `{audio}`")
    else:
        await message.reply_text("**Usage:** `/setaudio Audio Title`")

@app.on_message(filters.command("setsubtitle") & filters.private)
async def setsubtitle_handler(client, message):
    if len(message.command) > 1:
        subtitle = message.text.split(" ", 1)[1]
        await db.set_subtitle(message.from_user.id, subtitle)
        await message.reply_text(f"✅ Subtitle title set to: `{subtitle}`")
    else:
        await message.reply_text("**Usage:** `/setsubtitle Subtitle Title`")

@app.on_message(filters.command("setvideo") & filters.private)
async def setvideo_handler(client, message):
    if len(message.command) > 1:
        video = message.text.split(" ", 1)[1]
        await db.set_video(message.from_user.id, video)
        await message.reply_text(f"✅ Video title set to: `{video}`")
    else:
        await message.reply_text("**Usage:** `/setvideo Video Title`")

# Show metadata settings
@app.on_message(filters.command("showmetadata") & filters.private)
async def showmetadata_handler(client, message):
    user_id = message.from_user.id
    metadata = {
        "Title": await db.get_title(user_id),
        "Author": await db.get_author(user_id),
        "Artist": await db.get_artist(user_id),
        "Audio": await db.get_audio(user_id),
        "Subtitle": await db.get_subtitle(user_id),
        "Video": await db.get_video(user_id),
        "Status": "ON ✅" if await db.get_metadata(user_id) else "OFF ❌"
    }
    
    text = "**📝 Current Metadata Settings:**\n\n"
    for key, value in metadata.items():
        text += f"**{key}:** `{value}`\n"
    
    await message.reply_text(text)

# Reset metadata to defaults
@app.on_message(filters.command("resetmetadata") & filters.private)
async def resetmetadata_handler(client, message):
    user_id = message.from_user.id
    await db.set_title(user_id, "Encoded by @Codeflix_Bots")
    await db.set_author(user_id, "@Codeflix_Bots")
    await db.set_artist(user_id, "@Codeflix_Bots")
    await db.set_audio(user_id, "By @Codeflix_Bots")
    await db.set_subtitle(user_id, "By @Codeflix_Bots")
    await db.set_video(user_id, "Encoded By @Codeflix_Bots")
    
    await message.reply_text("✅ Metadata reset to default values!")

# ==================== GROUP HANDLERS ====================
# Group file handler - add to queue (WORKS FOR ALL USERS IN ALL GROUPS)
@app.on_message(filters.group & (filters.document | filters.video | filters.audio))
async def group_file_handler(client, message):
    try:
        print(f"Received file in group {message.chat.id}: {message.document.file_name if message.document else message.video.file_name if message.video else message.audio.file_name}")
        
        # Add file to queue
        queue_position = processing_queue.add_to_queue(message, message.from_user.id)
        
        # Send queue confirmation
        queue_info = processing_queue.get_queue_info()
        current_task = queue_info['current_task']
        is_processing = queue_info['is_processing']
        
        # Get file name
        if message.document:
            file_name = message.document.file_name or "file"
        elif message.video:
            file_name = message.video.file_name or "video.mp4"
        elif message.audio:
            file_name = message.audio.file_name or "audio.mp3"
        else:
            file_name = "Unknown"
        
        if is_processing and current_task:
            status_text = f"✅ **File added to queue!**\n\n"
            status_text += f"**File:** `{file_name[:50]}`\n"
            status_text += f"**Queue Position:** `{queue_position}`\n"
            status_text += f"**Currently Processing:** `{current_task.get('file_name', 'Unknown')[:30]}`\n"
            status_text += f"**Queue Size:** `{processing_queue.get_queue_length()}`\n\n"
            status_text += "⏳ **Please wait, files are processed one by one...**"
        else:
            status_text = f"✅ **File added to queue!**\n\n"
            status_text += f"**File:** `{file_name[:50]}`\n"
            status_text += f"**Queue Position:** `{queue_position}`\n"
            status_text += f"**Queue Size:** `{processing_queue.get_queue_length()}`\n\n"
            status_text += "🚀 **Starting processing now...**"
        
        await client.send_message(
            chat_id=message.chat.id,
            text=status_text,
            reply_to_message_id=message.id
        )
        print(f"Added file to queue. Position: {queue_position}")
        
    except Exception as e:
        print(f"Error in group file handler: {e}")
        import traceback
        traceback.print_exc()

# Queue status command (works in groups)
@app.on_message(filters.command("queue") & filters.group)
async def queue_status_handler(client, message):
    queue_info = processing_queue.get_queue_info()
    
    if queue_info['total'] == 0 and not queue_info['is_processing']:
        await message.reply_text("📭 **Queue is empty!**\nNo files in processing queue.")
        return
    
    status_text = "📊 **Queue Status**\n\n"
    
    if queue_info['is_processing'] and queue_info['current_task']:
        status_text += f"🔄 **Currently Processing:**\n"
        status_text += f"   • `{queue_info['current_task'].get('file_name', 'Unknown')[:30]}`\n"
        status_text += f"   • User ID: `{queue_info['current_task'].get('user_id', 'Unknown')}`\n\n"
    
    status_text += f"📋 **Waiting in Queue:** `{queue_info['total']}` files\n"
    
    if queue_info['waiting_list']:
        status_text += "\n**Next 5 in Queue:**\n"
        for i, item in enumerate(queue_info['waiting_list'][:5]):  # Show first 5
            status_text += f"`{item['position']}.` `{item['file_name'][:30]}...` (User: `{item['user_id']}`)\n"
        
        if len(queue_info['waiting_list']) > 5:
            status_text += f"\n... and {len(queue_info['waiting_list']) - 5} more files\n"
    
    status_text += f"\n**Statistics:**\n"
    status_text += f"• ✅ Completed: `{queue_info['completed']}`\n"
    status_text += f"• ❌ Failed: `{queue_info['failed']}`\n"
    status_text += f"• ⏳ Total in System: `{queue_info['total'] + (1 if queue_info['is_processing'] else 0)}`"
    
    await message.reply_text(status_text)

# Clear queue command (admin only - works everywhere)
@app.on_message(filters.command("clearqueue") & filters.user(Config.ADMIN))
async def clear_queue_handler(client, message):
    processing_queue.clear_queue()
    processing_queue.completed_tasks = 0
    processing_queue.failed_tasks = 0
    await message.reply_text("✅ **Queue cleared successfully!**")

# ==================== CALLBACK QUERY HANDLER ====================
@app.on_callback_query()
async def callback_handler(client, query):
    data = query.data
    user_id = query.from_user.id
    
    if data == "home":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("• ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs •", callback_data='help')],
            [
                InlineKeyboardButton('• ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Codeflix_Bots'),
                InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ •', url='https://t.me/CodeflixSupport')
            ],
            [
                InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about'),
                InlineKeyboardButton('sᴏᴜʀᴄᴇ •', callback_data='source')
            ]
        ])
        
        await query.message.edit_text(
            Txt.START_TXT.format(query.from_user.mention),
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    
    elif data == "help":
        await query.message.edit_text(
            Txt.FILE_NAME_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="home")]
            ]),
            disable_web_page_preview=True
        )
    
    elif data == "metadata_on":
        await db.set_metadata(user_id, True)
        await query.answer("Metadata turned ON ✅")
        await query.message.edit_text(
            "✅ **Metadata turned ON!**\n\nNow your files will have metadata added while preserving all audio and subtitle tracks.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="home")]
            ])
        )
    
    elif data == "metadata_off":
        await db.set_metadata(user_id, False)
        await query.answer("Metadata turned OFF ❌")
        await query.message.edit_text(
            "❌ **Metadata turned OFF!**\n\nYour files will not have metadata added.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="home")]
            ])
        )
    
    elif data == "close":
        await query.message.delete()
    
    elif data in ["about", "source", "donate"]:
        await query.answer("This feature will be added soon!", show_alert=True)
    
    else:
        await query.answer("Feature not implemented yet!", show_alert=True)

# ==================== ADMIN COMMANDS ====================
@app.on_message(filters.command("stats") & filters.user(Config.ADMIN))
async def stats_handler(client, message):
    total_users = await db.total_users_count()
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - Config.BOT_UPTIME))
    queue_info = processing_queue.get_queue_info()
    
    stats_text = f"**📊 Bot Statistics**\n\n"
    stats_text += f"**• Total Users:** `{total_users}`\n"
    stats_text += f"**• Uptime:** `{uptime}`\n"
    stats_text += f"**• Queue Status:** `{queue_info['total']} waiting, {queue_info['completed']} completed`\n"
    stats_text += f"**• Processing:** `{'Yes' if queue_info['is_processing'] else 'No'}`\n"
    stats_text += f"**• Admin IDs:** `{', '.join(map(str, Config.ADMIN))}`"
    
    await message.reply_text(stats_text)

# Restart command (admin only)
@app.on_message(filters.command("restart") & filters.user(Config.ADMIN))
async def restart_handler(client, message):
    await message.reply_text("**🔄 Restarting bot...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ==================== MAIN ====================
async def main():
    """Main function to start the bot"""
    # Start the bot
    await app.start()
    
    # Start queue worker as background task
    asyncio.create_task(queue_worker())
    print("👷 Queue Worker: Started")
    
    # Get bot info
    me = await app.get_me()
    print(f"✅ Bot started as @{me.username}")
    print(f"✅ Bot ID: {me.id}")
    print("✅ Bot is ready to receive files in groups!")
    
    # Keep the bot running
    await idle()
    
    # Stop the bot
    await app.stop()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check for ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        print("✅ FFmpeg is installed and working")
        print(f"FFmpeg version: {result.stdout.split('version')[1].split(' ')[1] if 'version' in result.stdout else 'N/A'}")
    except:
        print("⚠️ WARNING: FFmpeg not found! Metadata features will not work.")
        print("Install ffmpeg:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
    
    print("🚀 Starting Auto Rename Bot with Queue System...")
    print(f"🤖 Bot Name: {Config.BOT_TOKEN.split(':')[0]}")
    print(f"👑 Admins: {Config.ADMIN}")
    print("📋 Queue System: ACTIVE (Files processed one by one)")
    print("📢 IMPORTANT: Add bot to your group and give it admin rights!")
    print("💡 Users must set /autorename format in private chat first")
    print("🤖 Bot is running. Press Ctrl+C to stop.")
    
    try:
        # Run the bot
        app.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
