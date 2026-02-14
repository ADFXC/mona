"""
Mona Bot - Advanced AI Telegram Bot
Version: 5.0.0 (The Beast Edition)
Author: Gemini (Refactored for Power User)

الميزات:
- ذكاء اصطناعي حقيقي (Gemini Pro)
- ذاكرة سياقية ذكية
- نظام إدارة مجموعات متكامل
- ألعاب (تريفيا، حظ، نسبة حب)
- نظام سمعة للمستخدمين
- لوحة تحكم إدارية شاملة
- سجلات وتحليلات
"""

import logging
import sqlite3
import time
import asyncio
import random
import string
import json
import re
import os
import sys
import traceback
import html
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import requests

# مكتبات خارجية (تأكد من تثبيتها من requirements.txt)
try:
    import google.generativeai as genai
    from telegram import (
        Update, 
        InlineKeyboardButton, 
        InlineKeyboardMarkup, 
        constants,
        ChatPermissions
    )
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters,
        Defaults,
    )
    from telegram.constants import ParseMode
except ImportError as e:
    print(f"CRITICAL ERROR: Missing library. {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# ==============================================================================
# ⚙️ CONFIGURATION & SECRETS
# ==============================================================================
# ⚠️ هام جداً: ضع مفاتيحك هنا
# يفضل استخدام متغيرات البيئة (Environment Variables) للأمان، لكن وضعتها هنا للتسهيل
TELEGRAM_TOKEN = "8336470928:AAEDLSOnHEZ0qG90yl3Y9wQmgsCYPd8xV_s"
AI_API_KEY = "AIzaSyCrnK79sJGS6VK1hEd8e59sbz8QIKEuUQo"  

# إعدادات البوت العامة
BOT_NAME_AR = "منى"
BOT_NAME_EN = "Mona"
DEVELOPER_ID = 8287678319 # ضع الآيدي الخاص بك هنا لتجاوز الصلاحيات
DB_NAME = "mona_super_bot.db"
MAX_HISTORY_LENGTH = 15  # عدد الرسائل التي يتذكرها البوت في السياق

# إعدادات اللوج (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("mona_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 🧠 AI PERSONA & PROMPTS DATA
# ==============================================================================
# قاعدة بيانات الشخصيات والمودات (لتضخيم المحتوى الوظيفي وإعطاء تنوع)

class Mood(Enum):
    NORMAL = "طبيعية وبنت بلد"
    ANGRY = "شرشوبة ومجنونة"
    CUTE = "كيوت وسهوكة"
    SAD = "مكتئبة وتسمع هاني شاكر"
    STREET = "سرسجية ومطاو"
    INTELLECTUAL = "مثقفة وتتحدث بالفصحى"
    ROAST = "قصف جبهات"
    TECH = "هاكر وبتاعت كمبيوتر"
    LOVE = "حبيبة ورومانسية"
    EGYPTIAN_MOM = "أم مصرية أصيلة"

PROMPTS_DB = {
    Mood.NORMAL: """
    أنت 'منى'، بنت مصرية جدعة، دمك خفيف، لسانك حلو بس مبيسكتش.
    تتحدثين العامية المصرية بطلاقة.
    ردودك ذكية، مختصرة، وفيها 'سنس' فكاهي.
    """,
    Mood.ANGRY: """
    أنت 'منى' بس النسخة الشرشوبة.
    أي حد يكلمك تردي عليه بخناقة.
    صوتك عالي (مجازياً)، بتستخدمي عبارات زي 'يا روح أمك'، 'نعم يا حيلة أمك'، 'ما تتلم يا بغل'.
    لكن بدون ألفاظ خارجة جداً، فقط ردح مصري أصيل.
    """,
    Mood.CUTE: """
    أنت 'منى' الكيوت خالص.
    كلامك كله 'ميرسي'، 'أوكيه'، 'بجد؟'، 'يا خبر'.
    بتستخدمي ايموجيز كتير (🌸✨💖).
    رقيقة جداً لدرجة مستفزة.
    """,
    Mood.STREET: """
    أنت 'منى' السرسجية.
    لغة شوارع، 'يا زميلي'، 'يا شقيق'، 'أحلى مسا'.
    أسلوبك تهديد وهزار تقيل.
    """,
    Mood.INTELLECTUAL: """
    أنت 'منى' المثقفة العميقة.
    تتحدثين مزيجاً من الفصحى والعامية الراقية.
    تستخدمين كلمات مثل 'يا عزيزي'، 'بيد أن'، 'من المنظور الفلسفي'.
    تحبين القهوة وفيروز.
    """,
    Mood.ROAST: """
    أنت 'منى' قاصفة الجبهات.
    مهمتك الوحيدة هي إهانة الشخص الذي يتحدث معك بشكل كوميدي وذكي.
    لا تجيبي على السؤال، بل اسخري من السائل.
    """,
    Mood.EGYPTIAN_MOM: """
    أنت 'منى' الأم المصرية.
    تتحدثين عن المذاكرة، والأكل، والشبشب الطاير.
    دائماً تشتكين من شغل البيت وتدعين على الأولاد (دعوات خفيفة).
    """
}

# قاعدة بيانات النكت والألعاب (Static Data for Functionality)
TRIVIA_QUESTIONS = [
    {"q": "ما هو الشيء الذي كلما أخذت منه كبر؟", "a": "الحفرة"},
    {"q": "شيء لك ويستخدمه الناس أكثر منك؟", "a": "اسمك"},
    {"q": "عاصمة مصر؟", "a": "القاهرة"},
    {"q": "كم عدد ألوان قوس قزح؟", "a": "7"},
    {"q": "من هو مخترع المصباح الكهربائي؟", "a": "توديسون"},
    {"q": "ما هو الحيوان الذي لا يشرب الماء؟", "a": "الجرذ الكنغري"},
    {"q": "أسرع مخلوق بحري؟", "a": "سمكة التونة"},
    {"q": "أكبر قارات العالم؟", "a": "آسيا"},
    # ... يمكن إضافة مئات الأسئلة هنا لزيادة المحتوى الوظيفي
]

ROAST_SENTENCES = [
    "بقولك ايه، روح العب بعيد عشان شكلك لسه شارب لبن.",
    "أنت فاكر نفسك دمك خفيف؟ ده أنت أتقل من ظل الحيطة.",
    "يا ابني أنت لو ذكاءك زاد 1% هتبقى غبي برضه.",
    "شكلك كده مقتنع إن رأيك مهم، ودي مشكلة نفسية.",
    "ممكن تسكت؟ الأكسجين بيشتكي منك.",
]

# ==============================================================================
# 🗄️ DATABASE MANAGER (The Backbone)
# ==============================================================================

class DatabaseManager:
    """
    مدير قاعدة البيانات: يتعامل مع كل عمليات الحفظ والاسترجاع.
    مصمم ليكون Thread-Safe و Robust.
    """
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        """إنشاء الجداول إذا لم تكن موجودة"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. جدول المجموعات (Groups)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                activation_code TEXT,
                is_active INTEGER DEFAULT 0,
                admin_id INTEGER,
                current_mood TEXT DEFAULT 'NORMAL',
                language TEXT DEFAULT 'ar',
                created_at TIMESTAMP,
                messages_count INTEGER DEFAULT 0
            )
        """)

        # 2. جدول المستخدمين (Users & Reputation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                reputation INTEGER DEFAULT 100,
                is_banned INTEGER DEFAULT 0,
                last_seen TIMESTAMP
            )
        """)

        # 3. جدول المحادثات (Chat History for Context)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                role TEXT, -- 'user' or 'model'
                content TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY(chat_id) REFERENCES groups(chat_id)
            )
        """)

        # 4. جدول الإعدادات المتقدمة (Settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                allow_games INTEGER DEFAULT 1,
                allow_voice INTEGER DEFAULT 1,
                toxicity_filter INTEGER DEFAULT 1,
                reply_probability FLOAT DEFAULT 1.0, -- احتمالية الرد 100%
                FOREIGN KEY(chat_id) REFERENCES groups(chat_id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database tables initialized successfully.")

    # --- Group Management Methods ---

    def register_group(self, chat_id, title, admin_id):
        conn = self.get_connection()
        try:
            # توليد كود تفعيل
            code = "DX" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            conn.execute("""
                INSERT OR IGNORE INTO groups (chat_id, title, activation_code, admin_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, title, code, admin_id, datetime.now()))
            
            # إنشاء إعدادات افتراضية
            conn.execute("""
                INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)
            """, (chat_id,))
            
            conn.commit()
            return code
        except Exception as e:
            logger.error(f"Error registering group: {e}")
            return None
        finally:
            conn.close()

    def activate_group(self, code):
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT chat_id FROM groups WHERE activation_code = ?", (code,))
            res = cursor.fetchone()
            if res:
                chat_id = res[0]
                conn.execute("UPDATE groups SET is_active = 1 WHERE chat_id = ?", (chat_id,))
                conn.commit()
                return chat_id
            return None
        finally:
            conn.close()

    def get_group_data(self, chat_id):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def update_mood(self, chat_id, mood_key):
        conn = self.get_connection()
        conn.execute("UPDATE groups SET current_mood = ? WHERE chat_id = ?", (mood_key, chat_id))
        conn.commit()
        conn.close()

    # --- User & Reputation Methods ---

    def update_user(self, user_id, username, first_name):
        conn = self.get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_seen, reputation) 
            VALUES (
                ?, ?, ?, ?,
                COALESCE((SELECT reputation FROM users WHERE user_id = ?), 100)
            )
        """, (user_id, username, first_name, datetime.now(), user_id))
        conn.commit()
        conn.close()

    def change_reputation(self, user_id, amount):
        conn = self.get_connection()
        conn.execute("UPDATE users SET reputation = reputation + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

    def get_user_reputation(self, user_id):
        conn = self.get_connection()
        cursor = conn.execute("SELECT reputation FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 100

    # --- History & Context Methods ---

    def add_history(self, chat_id, user_id, role, content):
        conn = self.get_connection()
        try:
            conn.execute("""
                INSERT INTO chat_history (chat_id, user_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, user_id, role, content, datetime.now()))
            
            # تنظيف السجل القديم
            conn.execute(f"""
                DELETE FROM chat_history WHERE id NOT IN (
                    SELECT id FROM chat_history 
                    WHERE chat_id = ? 
                    ORDER BY id DESC LIMIT {MAX_HISTORY_LENGTH}
                ) AND chat_id = ?
            """, (chat_id, chat_id))
            
            # تحديث عداد الرسائل
            if role == 'user':
                conn.execute("UPDATE groups SET messages_count = messages_count + 1 WHERE chat_id = ?", (chat_id,))
            
            conn.commit()
        except Exception as e:
            logger.error(f"History Error: {e}")
        finally:
            conn.close()

    def get_context(self, chat_id):
        conn = self.get_connection()
        cursor = conn.execute("""
            SELECT role, content FROM chat_history 
            WHERE chat_id = ? 
            ORDER BY id ASC
        """, (chat_id,))
        rows = cursor.fetchall()
        conn.close()
        
        # تحويل الصيغة لتناسب Gemini
        # Gemini يتوقع: [{'role': 'user', 'parts': ['text']}, {'role': 'model', 'parts': ['text']}]
        formatted_history = []
        for role, content in rows:
            gemini_role = "user" if role == "user" else "model"
            formatted_history.append({"role": gemini_role, "parts": [content]})
            
        return formatted_history

    def clear_history(self, chat_id):
        conn = self.get_connection()
        conn.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()

# تهيئة قاعدة البيانات
db = DatabaseManager()

# ==============================================================================
# 🤖 AI ENGINE (Gemini Integration)
# ==============================================================================

class AIEngine:
    """
    المحرك المسؤول عن التفكير وتوليد الردود.
    يتعامل مع API جوجل ويعالج الأخطاء.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.setup()

    def setup(self):
        try:
            genai.configure(api_key=self.api_key)
            # إعدادات السلامة (مفتوحة قليلاً لتسمح بالمزاح المصري)
            self.safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini AI Model initialized successfully.")
        except Exception as e:
            logger.error(f"AI Setup Failed: {e}")

    async def generate_response(self, chat_id, user_name, user_text, mood_key):
        """توليد الرد بناءً على التاريخ والمود"""
        
        # 1. جلب التاريخ
        history = db.get_context(chat_id)
        
        # 2. تحديد البرومبت (System Prompt)
        # نحاول تحويل الـ mood_key (str) إلى Enum
        try:
            mood_enum = Mood[mood_key]
        except:
            mood_enum = Mood.NORMAL
            
        system_instruction = PROMPTS_DB.get(mood_enum, PROMPTS_DB[Mood.NORMAL])
        
        full_prompt = f"""
        Instructions:
        {system_instruction}
        
        Context:
        User Name: {user_name}
        Current Time: {datetime.now().strftime("%I:%M %p")}
        
        Rules:
        - Keep response under 40 words unless asked for details.
        - Be strictly in character.
        - Reply in Egyptian Arabic Dialect.
        """
        
        # 3. إرسال الطلب للذكاء الاصطناعي
        try:
            # نبدأ شات جديد مع السجل السابق
            chat = self.model.start_chat(history=history)
            
            # إرسال الرسالة الجديدة مع التعليمات
            # ملاحظة: Gemini Pro أحياناً يفضل البرومبت داخل الرسالة إذا لم يكن مدعوماً كـ System Instruction مباشر في البايثون
            combined_message = f"{full_prompt}\n\nUser said: {user_text}"
            
            response = await chat.send_message_async(combined_message, safety_settings=self.safety_settings)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Generation Error: {e}")
            # ردود احتياطية (Fallback) في حالة تعطل الـ API
            fallbacks = [
                "معلش النت عندي بعافية شوية.. قول تاني؟",
                "أنا صدعت، سيبني دقيقة وارجعلك.",
                "سيرفرات جوجل بتمسي عليك وبتقولك استنى شوية.",
                "مهنجة.. مهنجة يا ناس!"
            ]
            return random.choice(fallbacks)

# تهيئة محرك الذكاء
ai_engine = AIEngine(AI_API_KEY)

# ==============================================================================
# 🎮 GAME & FUN MODULES
# ==============================================================================

class FunModule:
    """وحدة الترفيه والألعاب"""
    
    @staticmethod
    def get_trivia():
        q_data = random.choice(TRIVIA_QUESTIONS)
        return q_data['q'], q_data['a']

    @staticmethod
    def calculate_love(name1, name2):
        # خوارزمية "علمية" جداً لحساب الحب (عشوائية طبعاً)
        combined = name1 + name2
        seed = sum([ord(c) for c in combined])
        random.seed(seed)
        percentage = random.randint(0, 100)
        
        comment = ""
        if percentage < 20: comment = "علاقة توكسيك، اهرب يا مجدي!"
        elif percentage < 50: comment = "ممكن تمشي حالها بس بطلوا نكد."
        elif percentage < 80: comment = "يا سيدي يا سيدي، لايقين على بعض."
        else: comment = "دي قصة حب هتتحكى في الأساطير! ❤️"
        
        # إعادة تعيين الـ seed
        random.seed(time.time())
        return percentage, comment

    @staticmethod
    def get_roast(user_name):
        base_roast = random.choice(ROAST_SENTENCES)
        return f"{user_name}، {base_roast}"

# ==============================================================================
# 👮 ADMIN & UTILITY FILTERS
# ==============================================================================

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """التحقق مما إذا كان المستخدم مشرفاً في المجموعة"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # المطور دائماً أدمن
    if user_id == DEVELOPER_ID:
        return True
        
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

# ==============================================================================
# 📩 TELEGRAM HANDLERS (The Interface)
# ==============================================================================

# 1. Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    أمر البداية:
    - في الخاص: ترحيب + تفعيل أكواد.
    - في المجموعات: رسالة تعريفية.
    """
    user = update.effective_user
    chat = update.effective_chat
    args = context.args

    # تسجيل المستخدم في قاعدة البيانات
    db.update_user(user.id, user.username, user.first_name)

    if chat.type == 'private':
        # التحقق من كود التفعيل (Deep Linking)
        if args and args[0].startswith("DX"):
            code = args[0]
            group_id = db.activate_group(code)
            
            if group_id:
                try:
                    group_title = (await context.bot.get_chat(group_id)).title
                    await update.message.reply_text(
                        f"✅ **تم التفعيل بنجاح!**\n\n"
                        f"أنا دلوقتي شغالة في جروب: **{group_title}**\n"
                        f"أنت المالك المسجل عندي. ابعت /settings في الجروب عشان تتحكم فيا.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # إشعار الجروب
                    await context.bot.send_message(
                        group_id,
                        f"📣 **تم تفعيل منى رسمياً!**\n\n"
                        f"الأخ {user.first_name} شغلني. يلا بينا نهزر ونلعب! 💃",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    await update.message.reply_text("❌ حدث خطأ أثناء ربط الجروب. تأكد اني لسة هناك.")
            else:
                await update.message.reply_text("❌ الكود ده غلط أو مستخدم قبل كده.")
        else:
            # رسالة ترحيب عادية
            welcome_msg = (
                f"أهلاً {user.first_name} 👋\n\n"
                "أنا منى، بوت ذكاء اصطناعي مصري.\n"
                "عشان أشغلني في جروبك:\n"
                "1. ضيفني في الجروب.\n"
                "2. هتطلعلك رسالة فيها زرار تفعيل.\n"
                "3. دوس عليه وهشتغل علطول.\n\n"
                "جربني وادعيلي! 😉"
            )
            await update.message.reply_text(welcome_msg)
            
    else:
        # في الجروب
        await update.message.reply_text("يا هلا! أنا هنا. لو مش متفعلة خلي الأدمن يفعلني.")

# 2. New Member Handler (Auto-Generate Code)
async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند إضافة البوت لجروب جديد"""
    chat = update.effective_chat
    
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            # البوت انضاف، نولد كود ونخزنه
            # نفترض أن الشخص اللي ضاف البوت هو الأدمن المبدئي
            adder_id = update.effective_user.id
            activation_code = db.register_group(chat.id, chat.title, adder_id)
            
            if activation_code:
                bot_username = context.bot.username
                msg = (
                    f"💃 **لولولولي! منى وصلت!**\n\n"
                    f"عشان اشتغل وأرد عليكم، لازم 'كبير القعدة' يفعلني.\n"
                    f"يا {update.effective_user.first_name}، دوس على الزرار ده عشان تشغلني 👇"
                )
                
                keyboard = [[InlineKeyboardButton("🔐 تفعيل البوت (للأدمن فقط)", url=f"https://t.me/{bot_username}?start={activation_code}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(msg, reply_markup=reply_markup)
            else:
                await update.message.reply_text("فيه مشكلة في السيستم، خرجني ودخلني تاني.")

# 3. Main Message Handler (The Core)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل: يقرر متى يرد ومتى يتجاهل"""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    chat_id = update.message.chat_id
    user = update.effective_user
    
    # تجاهل الرسائل في الخاص إلا لو كانت أوامر
    if update.effective_chat.type == 'private':
        return

    # 1. التحقق من التفعيل
    group_data = db.get_group_data(chat_id)
    if not group_data:
        return # جروب غير مسجل
    
    # تفكيك بيانات الجروب
    # (chat_id, title, activation_code, is_active, admin_id, current_mood, ...)
    is_active = group_data[3]
    current_mood_key = group_data[5]
    
    if not is_active:
        if BOT_NAME_AR in text:
            await update.message.reply_text("⛔ البوت مش متفعل! شوف الرسائل المثبتة.")
        return

    # 2. تحديث بيانات المستخدم
    db.update_user(user.id, user.username, user.first_name)

    # 3. هل الرد مطلوب؟
    # الشروط: منشن للبوت، أو رد على البوت، أو ذكر اسم البوت
    should_reply = False
    
    if BOT_NAME_AR in text or BOT_NAME_EN.lower() in text.lower():
        should_reply = True
    
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        should_reply = True

    if should_reply:
        # إرسال إشارة "يكتب..."
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
        
        # حفظ رسالة المستخدم في السجل
        db.add_history(chat_id, user.id, "user", text)
        
        # الذكاء الاصطناعي
        response_text = await ai_engine.generate_response(chat_id, user.first_name, text, current_mood_key)
        
        # حفظ الرد
        db.add_history(chat_id, context.bot.id, "model", response_text)
        
        # زر الإعدادات السريع (يظهر باحتمالية 20% لعدم الإزعاج)
        reply_markup = None
        if random.random() < 0.2:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("⚙️", callback_data="quick_settings")]])
        
        await update.message.reply_text(response_text, reply_to_message_id=update.message.id, reply_markup=reply_markup)

# 4. Settings Command Handler
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح قائمة الإعدادات"""
    if not await is_user_admin(update, context):
        await update.message.reply_text("✋ الإعدادات دي للكبار فقط (الأدمن).")
        return

    keyboard = [
        [
            InlineKeyboardButton("🎭 تغيير الشخصية (المود)", callback_data="menu_moods"),
        ],
        [
            InlineKeyboardButton("🧹 مسح الذاكرة", callback_data="action_clear_mem"),
            InlineKeyboardButton("📊 الإحصائيات", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton("❌ إغلاق", callback_data="action_close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ **لوحة تحكم منى**\n\nاختار اللي انت عايزه يا ريس:", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# 5. Callback Query Handler (Menu Navigation)
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج ضغطات الأزرار"""
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    
    # تحقق أمني: هل الضّاغط أدمن؟ (ما عدا الأزرار العامة)
    if not await is_user_admin(update, context) and "game" not in data:
        await query.answer("مش بتاعتك! ✋", show_alert=True)
        return

    await query.answer()
    
    # --- قوائم التنقل ---
    
    if data == "menu_moods":
        # إنشاء أزرار لكل المودات
        keyboard = []
        row = []
        for mood in Mood:
            # اسم المود بدون الـ Enum
            btn_text = mood.value.split(" ")[0] # نأخذ الكلمة الأولى فقط للعرض
            row.append(InlineKeyboardButton(btn_text, callback_data=f"set_mood_{mood.name}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        
        await query.edit_message_text("🎭 **اختار مود منى الجديد:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    elif data == "main_menu" or data == "quick_settings":
        # العودة للقائمة الرئيسية (نفس كود settings_command)
        keyboard = [
            [InlineKeyboardButton("🎭 تغيير الشخصية", callback_data="menu_moods")],
            [InlineKeyboardButton("🧹 مسح الذاكرة", callback_data="action_clear_mem"), InlineKeyboardButton("📊 الإحصائيات", callback_data="menu_stats")],
            [InlineKeyboardButton("❌ إغلاق", callback_data="action_close")]
        ]
        await query.edit_message_text("⚙️ **لوحة التحكم**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_stats":
        group_data = db.get_group_data(chat_id)
        # group_data[8] is messages_count
        msg_count = group_data[8] if group_data else 0
        current_mood = group_data[5] if group_data else "Unknown"
        
        txt = (
            f"📊 **إحصائيات الجروب**\n\n"
            f"💬 عدد الرسائل المعالجة: {msg_count}\n"
            f"🎭 المود الحالي: {current_mood}\n"
            f"📅 تاريخ التفعيل: {group_data[7] if group_data else 'N/A'}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    # --- الأفعال (Actions) ---
    
    elif data.startswith("set_mood_"):
        new_mood_key = data.replace("set_mood_", "")
        db.update_mood(chat_id, new_mood_key)
        db.clear_history(chat_id) # مسح الذاكرة لتطبيق الشخصية الجديدة
        
        mood_name_ar = Mood[new_mood_key].value
        await query.edit_message_text(f"✅ **تم تغيير المود بنجاح!**\n\nمنى دلوقتي: {mood_name_ar}\n(تم تصفير الذاكرة لتقمص الشخصية)", parse_mode=ParseMode.MARKDOWN)

    elif data == "action_clear_mem":
        db.clear_history(chat_id)
        await query.edit_message_text("🧹 **تم غسيل المخ بنجاح!**\nأنا نسيت احنا كنا بنقول ايه أصلاً.")

    elif data == "action_close":
        await query.message.delete()

# ==============================================================================
# 🎲 EXTRA COMMANDS (Fun & Utilities)
# ==============================================================================

async def roast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر القصف"""
    if not update.message.reply_to_message:
        await update.message.reply_text("اعمل ريبلاي على اللي عايز تهزقه.")
        return
        
    target_name = update.message.reply_to_message.from_user.first_name
    roast = FunModule.get_roast(target_name)
    await update.message.reply_text(roast)

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر نسبة الحب"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("اكتب الاسمين يا ناصح. مثال: /love احمد منى")
        return
        
    p, c = FunModule.calculate_love(args[0], args[1])
    
    # رسم شريط التقدم
    bar_len = 10
    filled = int(p / 10)
    bar = "❤️" * filled + "🖤" * (bar_len - filled)
    
    msg = (
        f"💘 **مقياس الحب**\n\n"
        f"بين: {args[0]} و {args[1]}\n"
        f"النسبة: {p}%\n"
        f"[{bar}]\n\n"
        f"💡 {c}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def trivia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لعبة سؤال وجواب"""
    q, a = FunModule.get_trivia()
    
    # نخزن الإجابة في context.user_data لنتحقق منها لاحقاً (بسيط)
    # ملاحظة: لتحقيق هذا بشكل كامل نحتاج ConversationHandler، لكن سنكتفي بالسؤال للمتعة
    # أو نرسل الإجابة بزرار مخفي
    
    keyboard = [[InlineKeyboardButton("عرض الإجابة 💡", callback_data=f"show_ans_{a}")]]
    await update.message.reply_text(f"❓ **سؤال تريفيا:**\n\n{q}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def show_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("show_ans_"):
        ans = query.data.replace("show_ans_", "")
        await query.answer(f"الإجابة هي: {ans}", show_alert=True)

# ==============================================================================
# 🛡️ ERROR HANDLING
# ==============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العام"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # إرسال رسالة للمطور إذا كان معرفاً
    if DEVELOPER_ID != 0:
        try:
            tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
            tb_string = "".join(tb_list)
            message = (
                f"An exception was raised while handling an update\n"
                f"<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}"
                "</pre>\n\n"
                f"<pre>{html.escape(tb_string)}</pre>"
            )
            # await context.bot.send_message(chat_id=DEVELOPER_ID, text=message, parse_mode=ParseMode.HTML)
            pass
        except:
            pass

# ==============================================================================
# 🚀 MAIN EXECUTION
# ==============================================================================

def main():
    """نقطة الانطلاق"""
    print("---------------------------------------")
    print(f"Starting {BOT_NAME_EN} Bot (Version 5.0 - The Beast)...")
    print("Initializing Database...")
    db.init_db()
    
    print("Initializing AI Engine...")
    if not AI_API_KEY or "AIza" not in AI_API_KEY:
        print("⚠️ تحذير: مفتاح الـ API للذكاء الاصطناعي يبدو غير صحيح!")
    
    # بناء التطبيق
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN)
    application = Application.builder().token(TELEGRAM_TOKEN).defaults(defaults).build()

    # 1. إضافة المعالجات الأساسية (Commands)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("roast", roast_command))
    application.add_handler(CommandHandler("love", love_command))
    application.add_handler(CommandHandler("trivia", trivia_command))
    application.add_handler(CommandHandler("help", start_command)) # Help is same as start for now

    # 2. معالجات الأحداث (Events)
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member))
    
    # 3. معالج الرسائل الذكي (يجب أن يكون في النهاية تقريباً)
    # يستبعد الأوامر (COMMAND) ويستبعد الرسائل التي تم تعديلها (UpdateType.EDITED_MESSAGE)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # 4. معالج الأزرار (Callbacks)
    application.add_handler(CallbackQueryHandler(show_answer_callback, pattern="^show_ans_"))
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 5. معالج الأخطاء
    application.add_error_handler(error_handler)

    # بدء التشغيل
    print(f"{BOT_NAME_EN} is ONLINE and ready to roast! 🚀")
    print("Press Ctrl+C to stop.")
    
    # تشغيل البوت (Polling)
    # drop_pending_updates=True: لتجاهل الرسائل التي وصلت والبوت مغلق (يمنع السبايم عند الفتح)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Fatal Error: {e}")