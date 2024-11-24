from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import yt_dlp
import os
import logging
import time



# Load environment variables from the .env file
load_dotenv()

# Path for storing downloaded files
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to handle the /start command
async def start(update: Update, context):
    await update.message.reply_text("👋 Welcome! Send me a YouTube video link, and I'll download it for you as video or audio. 🎵📹")

# Function to process YouTube links
async def process_link(update: Update, context):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # Store the link in user_data
        context.user_data['pending_url'] = url

        # Create inline buttons for Video and Audio
        keyboard = [
            [InlineKeyboardButton("1️⃣ Download Video 🎥", callback_data="video")],
            [InlineKeyboardButton("2️⃣ Download Audio 🎵", callback_data="audio")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Ask the user to choose between Video or Audio
        await update.message.reply_text(
            "What would you like to download?",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Please send a valid YouTube video link.")

# Callback function for handling button clicks
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()  # Acknowledge the button click
    choice = query.data  # Get the user's choice (video or audio)

    # Retrieve the pending URL from user_data
    url = context.user_data.get('pending_url', None)

    if not url:
        await query.edit_message_text("❌ No YouTube link provided. Please send a valid YouTube link.")
        return

    if choice == "video":
        await query.edit_message_text("📥 Downloading video... Please wait.")
        await download_file(query, url, "video")
    elif choice == "audio":
        await query.edit_message_text("📥 Downloading audio... Please wait.")
        await download_file(query, url, "audio")

# Function to download files (video or audio)
async def download_file(query, url, file_type):
    # Configure options based on file type
    if file_type == "video":
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
            "socket_timeout": 30,
        }
    elif file_type == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "socket_timeout": 30,
        }

    retries = 3  # Number of retries for download
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info)
                if file_type == "audio":
                    file_name = file_name.replace(".webm", ".mp3")  # Ensure correct extension for audio

                # Send the file to the user
                with open(file_name, "rb") as file:
                    if file_type == "video":
                        await query.message.reply_video(video=file, caption="🎥 Here's your video file!")
                    elif file_type == "audio":
                        await query.message.reply_document(document=file, caption="🎵 Here's your audio file!")

                # Delete the file after sending it
                os.remove(file_name)
                return  # Exit after successful download

        except Exception as e:
            logger.error(f"Error downloading {file_type} (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(5)  # Wait before retrying
            else:
                await query.message.reply_text(f"❌ Failed to download {file_type} after multiple attempts: {e}")

# Main function to run the bot
def main():
    # Replace with your bot token
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    # Command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_link))
    application.add_handler(CallbackQueryHandler(button_click))  # Handles button clicks

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
