from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,ReplyKeyboardMarkup
import sqlite3
import shutil
import os
import time
import threading

# اطلاعات ربات
API_ID = 20010905  
API_HASH = "a53fd7db62068c80e134a756f2a9ecb8"
BOT_TOKEN = "7078603276:AAHbAXTHnmRJFLxi7DIyowNmGq-y1Et7spA"

import sqlite3

# اتصال به دیتابیس (اگر فایل وجود نداشته باشد، ساخته می‌شود)
conn = sqlite3.connect("music.db", check_same_thread=False)
cursor = conn.cursor()

# 🔹 ایجاد جدول `music` برای ذخیره موزیک‌ها
cursor.execute("""
CREATE TABLE IF NOT EXISTS music (
    id TEXT PRIMARY KEY,
    file_id TEXT,
    title TEXT,
    description TEXT,
    views INTEGER DEFAULT 0
)
""")
conn.commit()

# 🔹 ایجاد جدول `music_views` برای ذخیره بازدیدهای کاربران
cursor.execute("""
CREATE TABLE IF NOT EXISTS music_views (
    user_id INTEGER,
    music_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, music_id)
)
""")
conn.commit()

# 🔹 ایجاد جدول `users` برای ذخیره کاربران
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    join_date DATE DEFAULT CURRENT_DATE
)
""")
conn.commit()

# 🔹 ایجاد جدول `videos` برای ذخیره ویدیوها
cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    file_id TEXT,
    caption TEXT,
    music_file_id TEXT
)
""")
conn.commit()

print("✅ دیتابیس `music.db` با موفقیت ساخته شد!")





# مقداردهی اولیه بات
bot = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# لیست ادمین‌ها
ADMIN_IDS = [6840093855]  # آیدی عددی خودت رو اینجا بذار 
CHANNEL_ID = "@alispytest"  # آیدی کانال




# ⬇️ **مدیریت /start برای ادمین و کاربران**
@bot.on_message(filters.command("start") & filters.private)
def start(client, message):
    user_id = message.from_user.id

    # ✅ ثبت کاربر در دیتابیس (اگه قبلاً ثبت نشده باشه)
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    # 🎵 اگه استارت همراه با لینک موزیک بود (مثل start=get_music_123)
    if len(message.command) > 1 and message.command[1].startswith("get_music_"):
        video_code = message.command[1].replace("get_music_", "")
        print(f"🟢 [DEBUG] درخواست دریافت موزیک برای ویدیو: {video_code}")

        # 🔍 دریافت اطلاعات موزیک مرتبط
        cursor.execute("SELECT music_file_id FROM videos WHERE id=?", (video_code,))
        music = cursor.fetchone()

        if not music or not music[0]:
            print(f"❌ [DEBUG] موزیک برای ویدیو {video_code} پیدا نشد!")
            return message.reply_text("🚫 **موزیک مرتبط با این ویدیو یافت نشد!**")

        music_file_id = music[0]
        print(f"🎵 [DEBUG] مقدار music_file_id برای ویدیو {video_code}: {music_file_id}")

        # ✅ چک کردن و ثبت بازدید موزیک
        cursor.execute("SELECT views FROM music WHERE id=?", (video_code,))
        music_data = cursor.fetchone()

        if not music_data:
            print(f"🟡 [DEBUG] موزیک {video_code} در دیتابیس نبود، اضافه شد!")
            cursor.execute("INSERT INTO music (id, file_id, views) VALUES (?, ?, 0)", (video_code, music_file_id))
            conn.commit()
            views = 0
        else:
            views = music_data[0]  # مقدار قبلی بازدید

        # ✅ بررسی اینکه این کاربر قبلاً این موزیک رو دیده یا نه
        cursor.execute("SELECT 1 FROM music_views WHERE user_id=? AND music_id=?", (user_id, video_code))
        view_exists = cursor.fetchone()

        if not view_exists:
            # ✅ اگه اولین باره که این کاربر این موزیک رو می‌بینه، بازدید زیاد بشه
            views += 1
            cursor.execute("UPDATE music SET views = ? WHERE id=?", (views, video_code))
            cursor.execute("INSERT INTO music_views (user_id, music_id) VALUES (?, ?)", (user_id, video_code))
            conn.commit()
            print(f"🟢 [DEBUG] بازدید موزیک {video_code} افزایش یافت: {views}")
        else:
            print(f"🟡 [DEBUG] کاربر {user_id} قبلاً این موزیک را دیده، بازدید اضافه نشد!")

        print(f"✅ [DEBUG] موزیک {video_code} ارسال شد! بازدید جدید: {views}")

        # 📤 ارسال موزیک به کاربر
        client.send_audio(
            user_id, music_file_id,
            caption=f"🎶 #{video_code}\n👁‍🗨 **بازدید:** {views} 👤\n📡 🔗 @{CHANNEL_ID.replace('@', '')}"
        )
        return

    # 🔥 **اگه کاربر ادمین باشه، پیام مخصوص براش بفرست**
    if user_id in ADMIN_IDS:
        keyboard = ReplyKeyboardMarkup([["/panel"]], resize_keyboard=True)
        message.reply_text(
            "🔥 **سلام سلطان! خوش اومدی به ربات خودت** 😎\n\n"
            "⚙️ برای ورود به **پنل مدیریت** روی **/panel** بزن! 🚀",
            reply_markup=keyboard
        )
        return

    # 🎵 پیام خوش‌آمدگویی برای کاربران عادی
    message.reply_text(
        "🎶 **به ربات دانلود موزیک و ویدیو خوش اومدی!** 🎧\n\n"
        "📌 **اینجا می‌تونی موزیک‌های مرتبط با ویدیوهای داخل کانال رو دانلود کنی!**\n"
        f"📡 **کانال ما:** @{CHANNEL_ID.replace('@', '')}"
    )








@bot.on_message(filters.command("panel") & filters.private)
def open_admin_panel(client, message):
    if message.from_user.id not in ADMIN_IDS:
        return message.reply_text("🚫 شما اجازه دسترسی به این بخش را ندارید!")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 افزودن ویدیو", callback_data="add_video")],
        [InlineKeyboardButton("📹 ارسال ویدیو به کانال", callback_data="send_video")],
        [InlineKeyboardButton("🗑 حذف ویدیو", callback_data="list_videos_for_delete")],
        [InlineKeyboardButton("📊 مشاهده آمار", callback_data="bot_stats")],
        [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="send_ad")],
        [InlineKeyboardButton("📦 بکاپ از دیتابیس", callback_data="backup_db")]
    ])

    message.reply_text(
        "🛠 **پنل مدیریت**\n\n"
        "🎬 **مدیریت ویدیوها و موزیک‌های ربات**\n\n"
        "⚡ **از دکمه‌های زیر استفاده کنید:**",
        reply_markup=keyboard
    )






temp_videos = {}

@bot.on_callback_query(filters.regex("^add_video$"))
def request_video(client, query: CallbackQuery):
    admin_id = query.from_user.id
    temp_videos[admin_id] = {"step": "waiting_for_video"}
    query.message.reply_text("📥 لطفاً ویدیوی موردنظر را ارسال کنید.")

@bot.on_message(filters.private & filters.user(ADMIN_IDS) & filters.video)
def receive_video(client, message):
    admin_id = message.from_user.id
    file_id = message.video.file_id

    if admin_id not in temp_videos or temp_videos[admin_id]["step"] != "waiting_for_video":
        return

    temp_videos[admin_id]["file_id"] = file_id
    temp_videos[admin_id]["step"] = "waiting_for_code"

    message.reply_text("🔢 **لطفاً یک کد برای این ویدیو ارسال کنید!**")

@bot.on_message(filters.private & filters.user(ADMIN_IDS) & filters.text)
def receive_video_info(client, message):
    admin_id = message.from_user.id

    # 📌 مرحله دریافت کد ویدیو
    if admin_id in temp_videos and temp_videos[admin_id]["step"] == "waiting_for_code":
        video_code = message.text.strip().replace("#", "")

        # 🔍 چک کنیم که کد تکراری نباشه
        cursor.execute("SELECT id FROM videos WHERE id=?", (video_code,))
        existing_code = cursor.fetchone()

        if existing_code:
            message.reply_text("🚫 **این کد قبلاً استفاده شده است! لطفاً کد دیگری وارد کنید.**")
            return  # ❌ از تابع خارج شو

        temp_videos[admin_id]["video_code"] = video_code
        temp_videos[admin_id]["step"] = "waiting_for_caption"
        message.reply_text("📝 **حالا کپشن ویدیو را ارسال کنید.**")
        return

    # 📌 مرحله دریافت کپشن ویدیو
    if admin_id in temp_videos and temp_videos[admin_id]["step"] == "waiting_for_caption":
        temp_videos[admin_id]["caption"] = message.text.strip()
        temp_videos[admin_id]["step"] = "waiting_for_music"
        message.reply_text("🎵 **حالا موزیک مرتبط با ویدیو را ارسال کنید.**")
        return

    # 📌 مرحله دریافت موزیک مرتبط با ویدیو
    if admin_id in temp_videos and temp_videos[admin_id]["step"] == "waiting_for_music":
        if not message.audio:
            message.reply_text("🚫 **لطفاً فایل صوتی موزیک را ارسال کنید!**")
            return

        file_id = message.audio.file_id
        temp_videos[admin_id]["music_file_id"] = file_id
        temp_videos[admin_id]["step"] = "completed"

        # 📌 ذخیره در دیتابیس
        video_code = temp_videos[admin_id]["video_code"]
        caption = temp_videos[admin_id]["caption"]

        cursor.execute(
            "INSERT INTO videos (id, file_id, caption, music_file_id) VALUES (?, ?, ?, ?)",
            (video_code, temp_videos[admin_id]["file_id"], caption, file_id)
        )
        conn.commit()

        message.reply_text(f"✅ **ویدیو با کد {video_code} ذخیره شد!**\n\n"
                           "📤 حالا می‌تونی این ویدیو رو به کانال ارسال کنی.")

        # حذف اطلاعات موقتی
        del temp_videos[admin_id]

@bot.on_message(filters.private & filters.user(ADMIN_IDS) & filters.audio)
def receive_video_music(client, message):
    admin_id = message.from_user.id

    if admin_id in temp_videos and temp_videos[admin_id]["step"] == "waiting_for_music":
        if not message.audio:
            message.reply_text("🚫 **لطفاً فایل صوتی موزیک را ارسال کنید!**")
            return

        file_id = message.audio.file_id
        temp_videos[admin_id]["music_file_id"] = file_id
        temp_videos[admin_id]["step"] = "completed"

        video_code = temp_videos[admin_id]["video_code"]
        caption = temp_videos[admin_id]["caption"]

        print(f"🎵 [DEBUG] دریافت موزیک برای ویدیو {video_code}: {file_id}")  # ✅ لاگ برای بررسی مقدار موزیک دریافت‌شده

        # ذخیره اطلاعات ویدیو و موزیک در دیتابیس
        cursor.execute(
            "INSERT INTO videos (id, file_id, caption, music_file_id) VALUES (?, ?, ?, ?)",
            (video_code, temp_videos[admin_id]["file_id"], caption, file_id)
        )
        conn.commit()

        message.reply_text(
            f"✅ **ویدیو با کد {video_code} ذخیره شد!** 🎬\n\n"
            "📤 **می‌خوای ویدیو رو به کانال بفرستی؟**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 ارسال ویدیو به کانال", callback_data=f"send_video_{video_code}")],
                [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")]
            ])
        )

        del temp_videos[admin_id]









@bot.on_callback_query(filters.regex("^send_video$"))
def list_videos_for_send(client, query: CallbackQuery):
    print("📌 [DEBUG] دکمه ارسال ویدیو به کانال کلیک شد!")  # چک کن که این لاگ میاد یا نه
    
    cursor.execute("SELECT id FROM videos")
    videos = cursor.fetchall()

    if not videos:
        return query.message.edit_text("🚫 **هیچ ویدیویی برای ارسال وجود ندارد!**")

    buttons = [[InlineKeyboardButton(f"🎬 ویدیو #{v[0]}", callback_data=f"choose_video_{v[0]}")] for v in videos]
    buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")])

    query.message.edit_text(
        "📜 **لیست ویدیوها برای ارسال:**\n\n"
        "🔹 روی ویدیویی که می‌خوای ارسال کنی کلیک کن:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@bot.on_callback_query(filters.regex("^send_video_"))
def send_video_to_channel_direct(client, query: CallbackQuery):
    video_code = query.data.replace("send_video_", "")  # دریافت کد ویدیو به درستی

    # دریافت اطلاعات ویدیو از دیتابیس
    cursor.execute("SELECT file_id, caption, music_file_id FROM videos WHERE id=?", (video_code,))
    video = cursor.fetchone()

    if not video:
        return query.message.edit_text("🚫 **ویدیوی موردنظر یافت نشد! لطفاً دوباره امتحان کنید.**")

    file_id, caption, music_file_id = video

    # 🔍 بررسی مقدار music_file_id
    if not music_file_id:
        return query.message.edit_text("🚫 **برای این ویدیو هیچ موزیکی ثبت نشده!**")

    # 🔍 بررسی مقدار client.me.username
    bot_username = client.me.username if client.me.username else "your_bot_username"

    # دکمه دریافت موزیک
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 دانلود موزیک 📥", url=f"https://t.me/{bot_username}?start=get_music_{video_code}")]
    ])

    try:
        client.send_video(
            chat_id=CHANNEL_ID,
            video=file_id,
            caption=f"🎬 #{video_code}\n\n{caption}\n📡 @{CHANNEL_ID.replace('@', '')}",
            reply_markup=keyboard
        )

        query.message.edit_text(
            f"✅ **ویدیو {video_code} با موفقیت به کانال ارسال شد!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")]
            ])
        )
        query.answer("✅ ویدیو ارسال شد!", show_alert=False)

    except Exception as e:
        query.message.edit_text(f"❌ **خطا در ارسال ویدیو:** {e}")
        print(f"❌ خطا در ارسال ویدیو: {e}")


@bot.on_callback_query(filters.regex("^choose_video_"))
def send_selected_video(client, query: CallbackQuery):
    video_code = query.data.replace("choose_video_", "")  # دریافت کد ویدیو درست

    # دریافت اطلاعات ویدیو از دیتابیس
    cursor.execute("SELECT file_id, caption, music_file_id FROM videos WHERE id=?", (video_code,))
    video = cursor.fetchone()

    if not video:
        return query.message.edit_text("🚫 **ویدیوی موردنظر یافت نشد! لطفاً دوباره امتحان کنید.**")

    file_id, caption, music_file_id = video

    # 🔍 بررسی مقدار music_file_id
    if not music_file_id:
        return query.message.edit_text("🚫 **برای این ویدیو هیچ موزیکی ثبت نشده!**")

    # 🔍 بررسی مقدار client.me.username
    bot_username = client.me.username if client.me.username else "your_bot_username"

    # دکمه دریافت موزیک
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 دانلود موزیک 📥", url=f"https://t.me/{bot_username}?start=get_music_{video_code}")]
    ])

    try:
        client.send_video(
            chat_id=CHANNEL_ID,
            video=file_id,
            caption=f"🎬 #{video_code}\n\n{caption}\n📡 @{CHANNEL_ID.replace('@', '')}",
            reply_markup=keyboard
        )

        query.message.edit_text(
            f"✅ **ویدیو {video_code} با موفقیت به کانال ارسال شد!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")]
            ])
        )
        query.answer("✅ ویدیو ارسال شد!", show_alert=False)

    except Exception as e:
        query.message.edit_text(f"❌ **خطا در ارسال ویدیو:** {e}")
        print(f"❌ خطا در ارسال ویدیو: {e}")

@bot.on_message(filters.private & filters.user(ADMIN_IDS) & filters.text)
def send_video_to_channel(client, message):
    admin_id = message.from_user.id

    if admin_id in temp_videos and temp_videos[admin_id].get("step") == "waiting_for_send_code":
        video_code = message.text.strip().replace("#", "")

        # دریافت اطلاعات ویدیو از دیتابیس
        cursor.execute("SELECT file_id, caption, music_file_id FROM videos WHERE id=?", (video_code,))
        video = cursor.fetchone()

        if not video:
            return message.reply_text("🚫 **ویدیوی موردنظر یافت نشد! لطفاً کد درست وارد کنید.**")

        file_id, caption, music_file_id = video

        # 🔍 بررسی مقدار music_file_id
        if not music_file_id:
            return message.reply_text("🚫 **برای این ویدیو هیچ موزیکی ثبت نشده!**")

        # 🔍 بررسی مقدار client.me.username
        bot_username = client.me.username if client.me.username else "your_bot_username"

        # دکمه دریافت موزیک
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 دریافت موزیک", url=f"https://t.me/{bot_username}?start=get_music_{music_file_id}")]
        ])

        try:
            client.send_video(
                chat_id=CHANNEL_ID,
                video=file_id,
                caption=f"🎬 **[{video_code}](https://t.me/{bot_username}?start=get_music_{music_file_id})**\n\n"
                        f"{caption}\n📡 [🔗 @{CHANNEL_ID.replace('@', '')}](https://t.me/{CHANNEL_ID.replace('@', '')})",
                reply_markup=keyboard,
                parse_mode="markdown"
            )

            message.reply_text("✅ **ویدیو با موفقیت به کانال ارسال شد!**")

            del temp_videos[admin_id]

        except Exception as e:
            message.reply_text(f"❌ **خطا در ارسال ویدیو:** {e}")
            print(f"❌ خطا در ارسال ویدیو: {e}")






@bot.on_callback_query(filters.regex("^list_videos_for_delete$"))
def list_videos_for_delete(client, query: CallbackQuery):
    cursor.execute("SELECT id FROM videos")
    videos = cursor.fetchall()

    if not videos:
        return query.message.edit_text(
            "🚫 **هیچ ویدیویی برای حذف وجود ندارد!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")]])
        )

    buttons = [[InlineKeyboardButton(f"🎬 ویدیو #{v[0]}", callback_data=f"delete_video_{v[0]}")] for v in videos]
    buttons.append([InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")])  

    query.message.edit_text(
        "📜 **لیست ویدیوها برای حذف:**\n\n"
        "🔹 روی ویدیویی که می‌خوای حذف کنی کلیک کن:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query(filters.regex("^delete_video_"))
def delete_selected_video(client, query: CallbackQuery):
    video_id = query.data.split("_")[2]

    # بررسی وجود ویدیو
    cursor.execute("SELECT id FROM videos WHERE id=?", (video_id,))
    existing_video = cursor.fetchone()

    if not existing_video:
        return query.answer("🚫 این ویدیو در دیتابیس وجود ندارد!", show_alert=True)

    # حذف ویدیو از دیتابیس
    cursor.execute("DELETE FROM videos WHERE id=?", (video_id,))
    conn.commit()

    # پیام موفقیت
    query.message.edit_text(
        f"✅ **ویدیو {video_id} با موفقیت حذف شد!** 🗑",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به لیست ویدیوها", callback_data="list_videos_for_delete")]
        ])
    )




@bot.on_callback_query(filters.regex("^bot_stats$"))
def panel_bot_stats(client, query: CallbackQuery):
    # ✅ تعداد کل کاربران
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    # ✅ تعداد کاربران جدید امروز
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(join_date) = DATE('now')")
    new_users_today = cursor.fetchone()[0]

    # ✅ تعداد کل ویدیوها
    cursor.execute("SELECT COUNT(*) FROM videos")
    video_count = cursor.fetchone()[0]

    # ✅ تعداد کل بازدیدهای موزیک
    cursor.execute("SELECT SUM(views) FROM music")
    total_music_views = cursor.fetchone()[0] or 0

    # ✅ تعداد بازدیدهای امروز
    cursor.execute("SELECT COUNT(*) FROM music_views WHERE DATE(timestamp) = DATE('now')")
    today_music_views = cursor.fetchone()[0]

    # ✅ تعداد ویدیوهای ارسال‌شده به کانال (اگر نیاز داری)
    cursor.execute("SELECT COUNT(*) FROM videos WHERE file_id IS NOT NULL")
    videos_sent_to_channel = cursor.fetchone()[0]

    # 📊 ارسال پیام آمار
    query.message.edit_text(
        f"📊 **آمار کلی ربات:**\n\n"
        f"👥 **تعداد کل کاربران:** {user_count}\n"
        f"🆕 **کاربران جدید امروز:** {new_users_today}\n"
        f"🎬 **تعداد کل ویدیوها:** {video_count}\n"
        f"🎵 **کل بازدیدهای موزیک:** {total_music_views}\n"
        f"📅 **بازدیدهای امروز:** {today_music_views}\n"
        f"📤 **ویدیوهای ارسال‌شده به کانال:** {videos_sent_to_channel}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="panel")]])
    )



# درخواست متن تبلیغ از ادمین
@bot.on_callback_query(filters.regex("^send_ad$"))
def request_advertisement(client, query: CallbackQuery):
    query.message.reply_text("📢 **متن پیام همگانی را ارسال کنید:**")
    temp_videos[query.from_user.id] = {"step": "waiting_for_ad"}

# ارسال پیام به همه‌ی کاربران
@bot.on_message(filters.private & filters.user(ADMIN_IDS) & filters.text)
def send_advertisement(client, message):
    user_id = message.from_user.id

    if user_id in temp_videos and temp_videos[user_id]["step"] == "waiting_for_ad":
        ad_text = message.text.strip()

        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        sent_count = 0
        for user in users:
            try:
                client.send_message(user[0], ad_text)
                sent_count += 1
                time.sleep(0.5)  # جلوگیری از FloodWait
            except Exception as e:
                print(f"❌ خطا در ارسال پیام به {user[0]}: {e}")

        message.reply_text(f"✅ **پیام همگانی به {sent_count} کاربر ارسال شد!**")
        del temp_videos[user_id]






@bot.on_callback_query(filters.regex("^backup_db$"))
def backup_db(client, query: CallbackQuery):
    backup_file = "backup_music.db"
    shutil.copy("music.db", backup_file)
    
    try:
        client.send_document(query.from_user.id, backup_file, caption="📦 **بکاپ دیتابیس ربات**")
        os.remove(backup_file)
        query.answer("✅ بکاپ ارسال شد!", show_alert=True)
    except Exception as e:
        query.message.edit_text(f"❌ **خطا در ارسال بکاپ:** {e}")
        print(f"❌ خطا در ارسال بکاپ: {e}")











@bot.on_callback_query(filters.regex("^panel$"))
def back_to_panel(client, query: CallbackQuery):
    if query.from_user.id not in ADMIN_IDS:
        return query.answer("🚫 شما اجازه دسترسی به این بخش را ندارید!", show_alert=True)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 افزودن ویدیو", callback_data="add_video")],
        [InlineKeyboardButton("📹 ارسال ویدیو به کانال", callback_data="send_video")],
        [InlineKeyboardButton("🗑 حذف ویدیو", callback_data="list_videos_for_delete")],
        [InlineKeyboardButton("📊 مشاهده آمار", callback_data="bot_stats")],
        [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="send_ad")],
        [InlineKeyboardButton("📦 بکاپ از دیتابیس", callback_data="backup_db")]
    ])

    query.message.edit_text(
        "🛠 **پنل مدیریت**\n\n"
        "🎬 **مدیریت ویدیوها و موزیک‌های ربات**\n\n"
        "⚡ **از دکمه‌های زیر استفاده کنید:**",
        reply_markup=keyboard
    )




def clear_temp_videos():
    while True:
        time.sleep(600)  # هر ۱۰ دقیقه چک کنه
        for admin in list(temp_videos.keys()):
            if temp_videos[admin].get("step") != "completed":
                del temp_videos[admin]
                print(f"🗑 اطلاعات ناتمام ادمین {admin} پاک شد!")

threading.Thread(target=clear_temp_videos, daemon=True).start()


bot.run()