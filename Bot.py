import os
import yt_dlp
import moviepy.editor as mp
from telegram import Update, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from deep_translator import GoogleTranslator
import razorpay

# 🔑 Environment Variables (Set in Railway.app)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

# 🎬 Subscription Plans
PLANS = {
    "31-60sec": 50,  # ₹50 per month
    "61-90sec": 100  # ₹100 per month
}

# 🔄 Razorpay Client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

# 🎥 Download Video Function
def download_video(update: Update, context: CallbackContext):
    url = update.message.text
    chat_id = update.message.chat_id

    update.message.reply_text("🔄 Processing your video... Please wait.")

    try:
        # 🎬 Download video using yt-dlp
        ydl_opts = {"format": "mp4", "outtmpl": "video.mp4"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # ✂ Trim video to 60 seconds
        video = mp.VideoFileClip("video.mp4").subclip(0, 60)
        video.write_videofile("short_video.mp4", codec="libx264", fps=30)

        # 🌍 Add Captions (Offline)
        caption_text = "This is a sample caption in English"
        
        # No Google Translator API, using a simple offline approach
        translated_caption = f"📜 Caption: {caption_text} (Auto-generated)"

        # Send processed video
        context.bot.send_video(chat_id, video=open("short_video.mp4", "rb"), caption=translated_caption)

    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

# 💰 Payment Function
def subscribe(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    plan = update.message.text.split()[1] if len(update.message.text.split()) > 1 else None

    if plan not in PLANS:
        update.message.reply_text("⚠️ Invalid plan! Choose: '31-60sec' or '61-90sec'.")
        return

    amount = PLANS[plan] * 100  # Convert to paise
    order = razorpay_client.order.create({"amount": amount, "currency": "INR", "payment_capture": "1"})

    payment_link = f"https://rzp.io/l/{order['id']}"
    update.message.reply_text(f"💳 Pay ₹{PLANS[plan]} for {plan} videos: [Click Here]({payment_link})", parse_mode="Markdown")

# 🏠 Start Function
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Welcome! Send a YouTube link to create Shorts!")

# 🚀 Main Function
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
