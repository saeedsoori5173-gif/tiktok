# -*- coding: utf-8 -*-
import os
import sys
import logging
import json
import random
import time
import threading
import requests
import hmac
import hashlib
import uuid
from datetime import datetime

# ==================== إعدادات التسجيل ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== التوكن ومعرف المطور ====================
BOT_TOKEN = "8607873288:AAFokRG9yl-gHfbpowL4h6LDUkqZL5OpArE"
DEVELOPER_ID = 5952132218

# ==================== استيراد مكتبة التيليغرام ====================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== التحقق من المطور ====================
def is_developer(update: Update) -> bool:
    return update.effective_user.id == DEVELOPER_ID

# ==================== إعدادات الجهاز والتشفير ====================
DEVINFO = '{"d":"62656137623230326662363536323731","n":"484f4e4f5220414c492d4e5831","o":"15","t":"d","v":"2.0.8","s":"1,0"}'
KEYBYTES = [0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31, 0x35, 0x30, 0x1c, 0x2f, 0x2c, 0x2c, 0x28, 0x31]
SECRET_KEY = bytes([b ^ 0x43 for b in KEYBYTES])

# ==================== ملف حفظ البيانات ====================
DATA_FILE = "bot_data.json"

# ==================== دوال التوقيع والطلبات ====================
def get_signature(tsval, nonceval, payloadval):
    msg = f"{tsval}-{nonceval}-{payloadval}"
    return hmac.new(SECRET_KEY, msg.encode('utf-8'), hashlib.sha256).hexdigest()

def send_request(payloadval, opname, token=None, csrf=None, needauth=True):
    endpoint = "https://api.tikspark.xyz/graphql"
    payloadstr = json.dumps(payloadval, separators=(',', ':'))

    tsval = str(int(time.time() * 1000))
    nonceval = str(uuid.uuid4())[:16]
    sigval = get_signature(tsval, nonceval, payloadstr)

    opids = {
        "LoginAccount": "3522613813036d73817b2715e67743f8d23d7a85ad08b7e12aa3b29a24a17c43",
        "AttestDevice": "bfaf5a72aeb9a337811da6a6d13e0b73680a18ffde0c59a23701e55b98ac2515",
        "GetOrders": "4d6a8b2c3f1e9a7b5c8d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
        "ActionOrder": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b"
    }

    headers = {
        "X-APOLLO-OPERATION-NAME": opname,
        "Accept": "application/graphql-response+json,application/json;q=0.9",
        "x-language": "ar",
        "x-app-name": "com.inspark",
        "x-device-info": DEVINFO,
        "x-app-sig": sigval,
        "x-app-ts": tsval,
        "x-app-nonce": nonceval,
        "Content-Type": "application/json",
        "User-Agent": "okhttp/4.12.0"
    }

    if opname in opids:
        headers["X-APOLLO-OPERATION-ID"] = opids[opname]

    if needauth and token:
        headers["token"] = token
        if csrf:
            headers["x-csrf-token"] = csrf

    try:
        resp = requests.post(endpoint, headers=headers, data=payloadstr, timeout=10)
        return resp, resp.json()
    except Exception as exc:
        return None, {"error": str(exc)}

# ==================== دوال API ====================
def attest_device(token, csrf):
    payload = {
        "operationName": "AttestDevice",
        "variables": {
            "integrityToken": "CpECARCnMGtZuGqph9Ch_tHPwVT3Lq4pEQUggTVb3VmFvpmp9hslRxDQzLHiG0T-FRz2SjwF2dX1pB2wVdV_bwOmlTSRqPnLY_FoOrqHcw03mEfJT7_HABOV9FgXxqi8tQFqtCHxZFxSNBcd2okJ25c7cH3WW8nCGROXy2MWwOg0OPMevg92gTG5GAnw9gS5uN1_xxOqhBVEwXWudEMyrKmcjpsL45c0rSFeBsZnufno1kisCRR7LjkdqiwYzBaOhy_7efQuVm1lUOrp35AYbomH6sdaQJckukWYCzKklsRglYaz73WGuogXfC8tb9CJ-dVFKYMSONfuk_bkCqHMdAnjnfAhC-8qObLmLFDbjI4QhsTPGmoB_mzxJbyNL5AOeVmj4MBJRwF_WN3WYHzksman0r1VekPvcNn5YAvXtAnADzkWCYNqjhdkGfG2TTx7xiUcj3S_LAZOzfPpzqsRgbbXzLQsSjgxgsaW3et0tQyCLcH8vBwqt4xibdBF0IhX",
            "requestHash": "31WAdD2ywy7JZ0t9aZOLKNpQX8WmO5g1Fh28nstNSWA"
        },
        "query": "mutation AttestDevice($integrityToken: String!, $requestHash: String!) { attestDevice(integrityToken: $integrityToken, requestHash: $requestHash) { ok verified } }"
    }
    _, res = send_request(payload, "AttestDevice", token, csrf, needauth=True)
    return "errors" not in res

def login_account(username, password):
    payload = {
        "operationName": "LoginAccount",
        "variables": {
            "data": {
                "id": "",
                "uniqueId": username,
                "nickname": "",
                "avatarMedium": "https://p16-common-sign.tiktokcdn.com/musically-maliva-obj/1594805258216454~tplv-tiktokx-cropcenter:720:720.webp",
                "followerCount": 0,
                "followingCount": 0,
                "videoCount": 0,
                "privateAccount": False,
                "diggCount": 0,
                "authMethod": "local",
                "password": password
            }
        },
        "query": "mutation LoginAccount($data: TiktokInfo) { loginTiktok(data: $data) { accessToken refreshToken user { __typename ...UserFields } } } fragment UserFields on User { _id tiktokId nickname email score diggCount followerCount followingCount friendCount isMembershipExpired heartCount username avatar banned vip vipExpiresAt authMethod isSubscription allowd referralCode referralCount referredBy }"
    }

    resp, res = send_request(payload, "LoginAccount", needauth=False)

    if resp and "errors" not in res:
        try:
            token = res['data']['loginTiktok']['accessToken']
            user_data = res['data']['loginTiktok']['user']
            csrf = resp.headers.get("x-csrf-token", "")
            
            if attest_device(token, csrf):
                return {
                    'success': True,
                    'token': token,
                    'csrf': csrf,
                    'user': user_data,
                    'score': user_data.get('score', 0)
                }
            else:
                return {'success': False, 'error': 'فشل التحقق من الجهاز'}
        except KeyError as e:
            return {'success': False, 'error': f'خطأ في تحليل البيانات: {str(e)}'}
    else:
        err = res.get("errors", [{"message": "Unknown"}])[0]["message"]
        return {'success': False, 'error': err}

def get_pending_orders(token, csrf):
    payload = {
        "operationName": "GetOrders",
        "variables": {},
        "query": "query GetOrders { getOrders { _id status } }"
    }
    _, res = send_request(payload, "GetOrders", token, csrf, needauth=True)
    orders = res.get("data", {}).get("getOrders", [])
    return [task["_id"] for task in orders if task.get("status") == "pending"]

def execute_order(token, csrf, order_id):
    randnum = random.randint(3000, 4500)
    payload = {
        "operationName": "ActionOrder",
        "variables": {
            "orderId": order_id,
            "validationData": {
                "attempts": 1,
                "initialNumber": float(randnum),
                "timeSpent": float(random.randint(4000, 7000)),
                "actualCount": randnum + 1,
                "source": "CLIENT_CRONET"
            }
        },
        "query": "mutation ActionOrder($orderId: ID!, $validationData: ValidationDataInput!) { actionOrder(orderId: $orderId, validationData: $validationData) { score taskProgress { count startTime taskProgressLimit } } }"
    }
    _, res = send_request(payload, "ActionOrder", token, csrf, needauth=True)
    if "errors" in res:
        return {'success': False, 'error': res["errors"][0]["message"]}
    return {
        'success': True,
        'score': res.get('data', {}).get('actionOrder', {}).get('score', 0)
    }

# ==================== نظام إدارة الحسابات ====================
class FarmingManager:
    def __init__(self):
        self.data = self.load_data()
        self.running = False
        self.threads = []
        self.lock = threading.Lock()
        self.farming_status = {}

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get_user_accounts(self, user_id):
        return self.data.get(str(user_id), [])

    def add_account(self, user_id, username, session_data):
        user_id_str = str(user_id)
        if user_id_str not in self.data:
            self.data[user_id_str] = []
        if username not in self.data[user_id_str]:
            self.data[user_id_str].append(username)
            if 'sessions' not in self.data:
                self.data['sessions'] = {}
            self.data['sessions'][username] = session_data
            self.save_data()
            return True
        return False

    def remove_account(self, user_id, username):
        user_id_str = str(user_id)
        if user_id_str in self.data and username in self.data[user_id_str]:
            self.data[user_id_str].remove(username)
            if 'sessions' in self.data and username in self.data['sessions']:
                del self.data['sessions'][username]
            self.save_data()
            return True
        return False

    def get_session(self, username):
        return self.data.get('sessions', {}).get(username, None)

    def start_farming(self, user_id):
        accounts = self.get_user_accounts(user_id)
        if not accounts:
            return False, "لا يوجد حسابات"
        if self.running:
            return False, "التجميع يعمل بالفعل"
        self.running = True
        self.farming_status.clear()
        for username in accounts:
            session = self.get_session(username)
            if session:
                self.farming_status[username] = {'status': 'running', 'tasks': 0, 'score': session.get('score', 0)}
                t = threading.Thread(target=self._farm_account, args=(username, session), daemon=True)
                t.start()
                self.threads.append(t)
        return True, f"بدأ التجميع لـ {len(accounts)} حساب"

    def stop_farming(self):
        self.running = False
        for username in self.farming_status:
            self.farming_status[username]['status'] = 'stopped'
        return True, "تم إيقاف التجميع"

    def _farm_account(self, username, session):
        token = session.get('token')
        csrf = session.get('csrf')
        if not token:
            return
        while self.running and self.farming_status.get(username, {}).get('status') == 'running':
            try:
                orders = get_pending_orders(token, csrf)
                if orders:
                    for order_id in orders:
                        if not self.running:
                            break
                        result = execute_order(token, csrf, order_id)
                        if result['success']:
                            with self.lock:
                                self.farming_status[username]['score'] = result['score']
                                self.farming_status[username]['tasks'] += 1
                                if 'sessions' in self.data and username in self.data['sessions']:
                                    self.data['sessions'][username]['score'] = result['score']
                                    self.save_data()
                        else:
                            time.sleep(2)
                else:
                    time.sleep(3)
            except:
                time.sleep(5)

manager = FarmingManager()

# ==================== دوال البوت ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_developer(update):
        await update.message.reply_text("⛔ غير مصرح لك!")
        return
    user_id = update.effective_user.id
    accounts = manager.get_user_accounts(user_id)
    total_score = 0
    active = 0
    for acc in accounts:
        session = manager.get_session(acc)
        if session:
            total_score += session.get('score', 0)
        if manager.farming_status.get(acc, {}).get('status') == 'running':
            active += 1

    keyboard = [
        [InlineKeyboardButton("📱 إضافة حساب", callback_data="add")],
        [InlineKeyboardButton("👤 حساباتي", callback_data="list")],
        [InlineKeyboardButton("🔄 حالة التجميع", callback_data="status")],
        [InlineKeyboardButton("▶️ بدء التجميع", callback_data="start_farm")],
        [InlineKeyboardButton("⏹️ إيقاف التجميع", callback_data="stop_farm")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("❌ حذف حساب", callback_data="remove")],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"🌟 **بوت التجميع التلقائي**\n"
        f"─────────────────────\n\n"
        f"👤 **الحسابات:** {len(accounts)}\n"
        f"💰 **النقاط:** {total_score}\n"
        f"🟢 **النشطة:** {active}\n\n"
        f"📌 اختر العملية:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_developer(update):
        await update.callback_query.answer("⛔ غير مصرح لك!", show_alert=True)
        return
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "add":
        await query.message.reply_text("📝 أرسل: `username:password`", parse_mode='Markdown')
        context.user_data['waiting_for'] = 'add_account'
    elif data == "list":
        await show_accounts(query.message, user_id)
    elif data == "status":
        await show_farming_status(query.message, user_id)
    elif data == "start_farm":
        success, msg = manager.start_farming(user_id)
        await query.message.reply_text(f"{'✅' if success else '❌'} {msg}")
    elif data == "stop_farm":
        success, msg = manager.stop_farming()
        await query.message.reply_text(f"{'✅' if success else '❌'} {msg}")
    elif data == "stats":
        await show_stats(query.message, user_id)
    elif data == "remove":
        await query.message.reply_text("🗑️ أرسل اسم المستخدم للحذف:")
        context.user_data['waiting_for'] = 'remove_account'
    elif data == "help":
        await show_help(query.message)
    elif data == "back":
        await start(update, context)

async def show_accounts(message, user_id):
    accounts = manager.get_user_accounts(user_id)
    if not accounts:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        await message.reply_text("❌ لا يوجد حسابات!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    text = "👤 **حساباتي**\n─────────────────────\n\n"
    total = 0
    for i, username in enumerate(accounts, 1):
        session = manager.get_session(username)
        score = session.get('score', 0) if session else 0
        total += score
        status = manager.farming_status.get(username, {}).get('status', 'غير معروف')
        emoji = '🟢' if status == 'running' else '🟡' if status == 'idle' else '🔴'
        text += f"{i}. **{username}**\n   💰 {score}\n   {emoji} {status}\n\n"
    text += f"💰 **المجموع:** {total}"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_farming_status(message, user_id):
    accounts = manager.get_user_accounts(user_id)
    if not accounts:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        await message.reply_text("❌ لا يوجد حسابات!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    text = "🔄 **حالة التجميع**\n─────────────────────\n\n"
    active = 0
    for username in accounts:
        status = manager.farming_status.get(username, {}).get('status', 'غير معروف')
        score = manager.farming_status.get(username, {}).get('score', 0)
        tasks = manager.farming_status.get(username, {}).get('tasks', 0)
        if status == 'running':
            active += 1
            emoji = '🟢'
        elif status == 'idle':
            emoji = '🟡'
        else:
            emoji = '🔴'
        text += f"{emoji} **{username}**\n   💰 {score}\n   ✅ {tasks}\n\n"
    text += f"🟢 النشطة: {active}/{len(accounts)}"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_stats(message, user_id):
    accounts = manager.get_user_accounts(user_id)
    if not accounts:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
        await message.reply_text("❌ لا يوجد حسابات!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    total_score = 0
    total_tasks = 0
    active = 0
    for username in accounts:
        session = manager.get_session(username)
        if session:
            total_score += session.get('score', 0)
        status = manager.farming_status.get(username, {}).get('status', '')
        if status == 'running':
            active += 1
        total_tasks += manager.farming_status.get(username, {}).get('tasks', 0)
    text = f"📊 **الإحصائيات**\n─────────────────────\n\n👤 الحسابات: {len(accounts)}\n🟢 النشطة: {active}\n💰 النقاط: {total_score}\n✅ المهام: {total_tasks}"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_help(message):
    text = "ℹ️ **المساعدة**\n─────────────────────\n\n1️⃣ أضف حساب: `user:pass`\n2️⃣ ابدأ التجميع\n3️⃣ شاهد الإحصائيات\n\n⚡ التجميع يعمل لكل حساب بخيط مستقل"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_developer(update):
        await update.message.reply_text("⛔ غير مصرح لك!")
        return
    user_id = update.effective_user.id
    text = update.message.text.strip()
    waiting = context.user_data.get('waiting_for')

    if waiting == 'add_account':
        if ':' not in text:
            await update.message.reply_text("❌ استخدم: username:password")
            return
        username, password = text.split(':', 1)
        username = username.strip()
        password = password.strip()
        await update.message.reply_text(f"⏳ جاري تسجيل الدخول...")
        result = login_account(username, password)
        if result['success']:
            session_data = {'token': result['token'], 'csrf': result['csrf'], 'score': result['score'], 'user': result['user']}
            if manager.add_account(user_id, username, session_data):
                await update.message.reply_text(f"✅ **تم التسجيل!**\n👤 {result['user'].get('username', username)}\n💰 {result['score']} نقطة")
            else:
                await update.message.reply_text("⚠️ الحساب موجود مسبقاً!")
        else:
            await update.message.reply_text(f"❌ فشل: {result['error']}")
        context.user_data['waiting_for'] = None
    elif waiting == 'remove_account':
        username = text.strip()
        if manager.remove_account(user_id, username):
            await update.message.reply_text(f"✅ تم حذف {username}")
        else:
            await update.message.reply_text("❌ لم يتم العثور على الحساب!")
        context.user_data['waiting_for'] = None
    else:
        await update.message.reply_text("❌ أمر غير معروف، استخدم /start")

# ==================== تشغيل البوت ====================
def main():
    print("🚀 تشغيل بوت التجميع (للمطور فقط)")
    print(f"📱 التوكن: {BOT_TOKEN[:10]}...")
    print(f"🔑 المطور: {DEVELOPER_ID}")

    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("✅ البوت يعمل الآن!")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            stop_signals=None
        )
    except Exception as e:
        logger.error(f"خطأ فادح: {e}")
        print("\n📦 تأكد من تثبيت المكتبات: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
