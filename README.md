# Auto Rename Bot - Queue System

An advanced Telegram bot that automatically renames files with custom formats, thumbnails, captions, and metadata.

## Features
- 📁 File renaming with custom templates
- 🖼️ Custom thumbnail support
- 📝 Custom caption templates
- 🏷️ Metadata editing (title, artist, author, etc.)
- 📊 Queue system for processing files one by one
- 🔄 Supports documents, videos, and audio files
- 📈 Real-time progress tracking

## Deployment on Render

### Method 1: Using Render Dashboard
1. Fork or clone this repository
2. Go to [render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `auto-rename-bot`
   - **Environment**: `Python`
   - **Build Command**: 
     ```
     apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
     ```
   - **Start Command**: `python test3.py`
6. Add environment variables (from `.env` file)
7. Click "Create Web Service"

### Method 2: Using Blueprint (render.yaml)
1. Push all files to GitHub
2. Go to [render.com/blueprints](https://render.com/blueprints)
3. Connect your repository
4. Click "Create New Blueprint"
5. Render will automatically detect `render.yaml` and deploy

### Environment Variables
| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `API_ID` | Yes | `25775944` | Telegram API ID |
| `API_HASH` | Yes | `217e861ebca9...` | Telegram API Hash |
| `BOT_TOKEN` | Yes | `7750507797:AA...` | Bot Token from @BotFather |
| `ADMIN` | Yes | `1869817167,1833881094` | Admin user IDs (comma separated) |
| `DB_URL` | Yes | `mongodb+srv://...` | MongoDB connection string |
| `DB_NAME` | No | `Filex` | MongoDB database name |
| `LOG_CHANNEL` | No | `-1002795055491` | Channel ID for logs |
| `START_PIC` | No | `https://...` | Start message photo URL |
| `WEBHOOK` | No | `False` | Enable webhooks |
| `PORT` | No | `8080` | Port for web server |

## Bot Commands

### User Commands
- `/start` - Start the bot and see welcome message
- `/autorename <format>` - Set rename format template
- `/set_caption <caption>` - Set custom caption
- `/see_caption` - View current caption
- `/del_caption` - Delete caption
- `/view_thumb` - View current thumbnail
- `/del_thumb` - Delete thumbnail
- `/metadata` - Toggle metadata on/off
- `/queue` - Check queue status (in groups)

### Admin Commands
- `/stats` - Bot statistics
- `/clearqueue` - Clear processing queue
- `/restart` - Restart the bot

## Format Variables
Use these variables in your rename format:

- `{filename}` - Original filename
- `{season}` - Season number (extracted from filename)
- `{episode}` - Episode number (extracted from filename)
- `{quality}` - Quality (1080p, 4K, etc.)
- `{filesize}` - File size
- `{duration}` - Duration (for videos/audio)

## Example Format
