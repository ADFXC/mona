import logging
import sqlite3
import time
import asyncio
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==============================================================================
# إعدادات البوت والمفاتيح (املأ هذه البيانات)
# ==============================================================================
TELEGRAM_TOKEN = "8336470928:AAEDLSOnHEZ0qG90yl3Y9wQmgsCYPd8xV_s"  # توكن بوت التليجرام من BotFather
AI_API_KEY = "AIzaSyCrnK79sJGS6VK1hEd8e59sbz8QIKEuUQo"              # مفتاح Gemini أو DeepSeek

# اسم البوت عشان التريجر (Trigger)
BOT_NAME_AR = "منى"

# إعدادات اللوج (عشان تشوف الأخطاء لو حصلت)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. قاعدة البيانات (SQLite) - لحفظ الإعدادات والمجموعات
# ==============================================================================
class DatabaseManager:
    def __init__(self, db_name="mona_bot.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # جدول المجموعات: يحفظ الآيدي، كود التفعيل، حالة التفعيل، والمود الحالي
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                activation_code TEXT,
                is_active INTEGER DEFAULT 0,
                admin_id INTEGER,
                current_mood TEXT DEFAULT 'طبيعية',
                last_activity TIMESTAMP
            )
        """)
        # جدول الذاكرة (Context): يحفظ آخر رسائل للمحادثة
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP
            )
        """)
        self.conn.commit()

    def register_group(self, chat_id, code):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO groups (chat_id, activation_code, last_activity) VALUES (?, ?, ?)",
                (chat_id, code, datetime.now())
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error registering group: {e}")

    def activate_group(self, code, admin_id):
        # تفعيل الجروب عن طريق الكود
        self.cursor.execute("SELECT chat_id FROM groups WHERE activation_code = ?", (code,))
        result = self.cursor.fetchone()
        if result:
            chat_id = result[0]
            self.cursor.execute(
                "UPDATE groups SET is_active = 1, admin_id = ? WHERE chat_id = ?",
                (admin_id, chat_id)
            )
            self.conn.commit()
            return chat_id
        return None

    def get_group_info(self, chat_id):
        self.cursor.execute("SELECT is_active, current_mood, last_activity FROM groups WHERE chat_id = ?", (chat_id,))
        return self.cursor.fetchone()

    def update_mood(self, chat_id, mood):
        self.cursor.execute("UPDATE groups SET current_mood = ? WHERE chat_id = ?", (mood, chat_id))
        self.conn.commit()

    def update_activity(self, chat_id):
        self.cursor.execute("UPDATE groups SET last_activity = ? WHERE chat_id = ?", (datetime.now(), chat_id))
        self.conn.commit()

    def add_history(self, chat_id, role, content):
        self.cursor.execute(
            "INSERT INTO chat_history (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, datetime.now())
        )
        self.conn.commit()
        # مسح الرسائل القديمة جداً للحفاظ على الأداء (نحتفظ بآخر 10 فقط)
        self.cursor.execute("""
            DELETE FROM chat_history WHERE id NOT IN (
                SELECT id FROM chat_history WHERE chat_id = ? ORDER BY id DESC LIMIT 10
            ) AND chat_id = ?
        """, (chat_id, chat_id))
        self.conn.commit()

    def get_history(self, chat_id):
        self.cursor.execute("SELECT role, content FROM chat_history WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
        return self.cursor.fetchall()

    def clear_history(self, chat_id):
        self.cursor.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
        self.conn.commit()

db = DatabaseManager()

# ==============================================================================
# 2. محرك الذكاء الاصطناعي (AI Engine) - المحاكاة
# ==============================================================================
# ملاحظة: هنا سنقوم بمحاكاة الرد. لربطه بـ DeepSeek أو Gemini،
# استبدل هذا الجزء بـ requests.post للـ API الخاص بهم.

async def generate_mona_response(chat_id, user_name, user_message, mood):
    # 1. استرجاع التاريخ (الذاكرة)
    history = db.get_history(chat_id)
    
    # 2. بناء البرومبت (حسب طلبك بالضبط)
    system_prompt = f"""
    التعليمات:
    أنتِ الآن تتقمصين شخصية 'منى'.
    اسم المتحدث: {user_name}
    رسالته: {user_message}
    روح الشخصية (الأساسي): بنت مصرية، جدعة، لسانها سابق تفكيرها، دمها خفيف.
    مزاج الشخصية الآن: {mood}
    
    شروط صارمة:
    - الرد بحد أقصى 15 كلمة.
    - بدون علامات تشكيل أو ترقيم كثيرة.
    - لهجة مصرية عامية طبيعية جداً (سوقية شيك).
    - لا تذكري أنك ذكاء اصطناعي.
    """

    # هنا يتم إرسال الطلب لـ API (Gemini/DeepSeek)
    # مثال للكود الحقيقي (معلق):
    # response = requests.post("API_URL", json={"prompt": system_prompt, "history": history})
    # return response.text
    
    # محاكاة الرد (Simulation) لغرض التجربة بدون API Key
    mock_responses = [
        "يا اسطى عيب عليك الكلام ده احنا اخوات",
        "طب بس بقى عشان انا خلقي ضيق النهاردة",
        "يا نهار ابيض هو انت تاني؟ ماشي يا سيدي",
        "ايوة يعني عايز ايه دلوقتي مش فاهمة",
        "بقولك ايه يا زميلي روق كدة وصلي عالنبي",
        "خلصانة بشياكة يا غالي"
    ]
    
    # محاكاة التأخير البشري (Typing...)
    await asyncio.sleep(1.5) 
    return f"{random.choice(mock_responses)} ({mood})"

# ==============================================================================
# 3. منطق البوت (Handlers)
# ==============================================================================

async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرد على رسالة Start في الخاص وتفعيل الكود"""
    user_id = update.effective_user.id
    args = context.args

    if args: # المستخدم دخل عن طريق رابط تفعيل (Deep Linking)
        activation_code = args[0]
        chat_id = db.activate_group(activation_code, user_id)
        
        if chat_id:
            await update.message.reply_text(f"✅ يا هلا! تم تفعيل منى في الجروب بنجاح.\nأنا حفظتك كـ 'أدمن' للجروب ده.")
            # إرسال رسالة للجروب
            await context.bot.send_message(chat_id, "✅ تم التفعيل! منى جاهزة للردح... قصدي للرد 💅")
        else:
            await update.message.reply_text("❌ الكود ده مش شغال أو تم استخدامه قبل كده.")
    else:
        await update.message.reply_text("أهلاً بيك! عشان تشغلني، ضيفني في جروب وخد الكود اللي هبعتهولك.")

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند إضافة البوت لمجموعة جديدة"""
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat_id = update.message.chat_id
            # توليد كود DX عشوائي
            code_suffix = ''.join(random.choices(string.digits, k=10))
            activation_code = f"DX{code_suffix}"
            
            db.register_group(chat_id, activation_code)
            
            bot_username = context.bot.username
            msg = (
                f"👋 **أنا جيت يا بشر!**\n\n"
                f"عشان اشتغل، لازم الأدمن ياخد الكود ده ويفعله عندي في الخاص:\n"
                f"`{activation_code}`\n\n"
                f"أو اضغط هنا للتفعيل السريع 👇"
            )
            
            keyboard = [
                [InlineKeyboardButton("تفعيل منى 🔐", url=f"https://t.me/{bot_username}?start={activation_code}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def mona_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل الرئيسي - مخ منى"""
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat_id
    text = update.message.text
    user_name = update.effective_user.first_name
    
    # 1. التحقق من التفعيل
    group_info = db.get_group_info(chat_id)
    if not group_info:
        return # البوت مش مسجل أصلاً
        
    is_active, current_mood, last_activity_str = group_info
    
    if not is_active:
        if BOT_NAME_AR in text:
            await update.message.reply_text("⚠️ البوت مش متفعل! حد من الأدمن يفعله بالكود.")
        return

    # 2. التحقق من التايم أوت (الذاكرة)
    # تحويل النص لتاريخ
    if last_activity_str:
        try:
            last_activity = datetime.strptime(last_activity_str, "%Y-%m-%d %H:%M:%S.%f")
        except:
            last_activity = datetime.now() # Fallback
            
        time_diff = datetime.now() - last_activity
        if time_diff > timedelta(minutes=10):
            db.clear_history(chat_id)
            # ممكن تخليها تبعت رسالة لو حابب: "معلش كنت بشتري طلبات، كنت بتقولوا ايه؟"
            
    # 3. هل الرد مطلوب؟ (نطق الاسم أو رد على البوت)
    is_reply_to_bot = False
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        is_reply_to_bot = True
        
    if BOT_NAME_AR in text or is_reply_to_bot:
        # إظهار "Jary el ketaba..."
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # تحديث وقت النشاط
        db.update_activity(chat_id)
        
        # حفظ رسالة المستخدم
        db.add_history(chat_id, "user", text)
        
        # توليد الرد من الذكاء
        response_text = await generate_mona_response(chat_id, user_name, text, current_mood)
        
        # حفظ رد البوت
        db.add_history(chat_id, "assistant", response_text)
        
        # الرد على المستخدم
        # إضافة زرار الإعدادات مع الرد (السحابة)
        keyboard = [[InlineKeyboardButton("☁️ تحكم منى", callback_data="open_settings")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response_text, reply_to_message_id=update.message.id, reply_markup=reply_markup)

# ==============================================================================
# 4. لوحة التحكم (Buttons & Callbacks)
# ==============================================================================

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع ضغطات الأزرار"""
    query = update.callback_query
    await query.answer() # لإزالة علامة التحميل
    
    chat_id = query.message.chat_id
    data = query.data
    
    # التحقق من صلاحية الأدمن (اختياري، هنا مفتوح للتجربة)
    # if query.from_user.id != admin_id: return
    
    if data == "open_settings":
        keyboard = [
            [
                InlineKeyboardButton("😊 كيوت", callback_data="mood_cute"),
                InlineKeyboardButton("😡 شرشوبة", callback_data="mood_angry")
            ],
            [
                InlineKeyboardButton("😎 سرسجية", callback_data="mood_street"),
                InlineKeyboardButton("😔 مكتئبة", callback_data="mood_sad")
            ],
            [
                InlineKeyboardButton("🗑️ مسح الذاكرة", callback_data="clear_memory"),
                InlineKeyboardButton("❌ إغلاق", callback_data="close_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        
    elif data.startswith("mood_"):
        new_mood = ""
        if data == "mood_cute": new_mood = "كيوت وطيبة"
        elif data == "mood_angry": new_mood = "عصبية وشرشوبة ولسانها طويل"
        elif data == "mood_street": new_mood = "سرسجية وبنت بلد"
        elif data == "mood_sad": new_mood = "مكتئبة وحزينة"
        
        db.update_mood(chat_id, new_mood)
        await query.edit_message_text(f"تمام يا ريس، قلبت المود لـ: {new_mood} 😉")
        # مسح الذاكرة عند تغيير المود عشان ما تتلخبطش
        db.clear_history(chat_id)
        
    elif data == "clear_memory":
        db.clear_history(chat_id)
        await query.edit_message_text("🗑️ غسلت مخي.. احنا كنا بنقول ايه؟")
        
    elif data == "close_menu":
        await query.edit_message_reply_markup(reply_markup=None)

# ==============================================================================
# 5. التشغيل الرئيسي
# ==============================================================================

def main():
    print("Bot is starting...")
    # بناء التطبيق
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # إضافة الهاندلرز (المعالجات)
    application.add_handler(CommandHandler("start", start_private))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
    
    # معالج الرسائل النصية (يستثني الأوامر)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mona_reply_handler))
    
    # معالج الأزرار
    application.add_handler(CallbackQueryHandler(settings_callback))

    # تشغيل البوت
    print("Mona is ready to fight! 💅")
    application.run_polling()

if __name__ == "__main__":
    main()
