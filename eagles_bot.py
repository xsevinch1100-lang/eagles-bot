# =============================================
# EAGLES ON TIME - Davomat Bot
# Ishga tushirish: python eagles_bot.py
# =============================================

import telebot
from telebot import types
from datetime import datetime
import json, os

BOT_TOKEN = "8878874901:AAGMib0f2LtiMSiLT9pvBxgRWYbOKptad6o"
ADMIN_ID  = 8259396282
DATA_FILE = "davomat.json"

bot = telebot.TeleBot(BOT_TOKEN)

# ---------- ma'lumotlar ----------
def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ishchilar": {}, "tarix": []}

def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sana():  return datetime.now().strftime("%d.%m.%Y")
def vaqt():  return datetime.now().strftime("%H:%M")

# ---------- menyular ----------
def ishchi_menyu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("✅ Kelish", "🏁 Ketish")
    m.add("📊 Mening davomatim")
    return m

def admin_menyu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("✅ Kelish", "🏁 Ketish")
    m.add("📊 Mening davomatim")
    m.add("➕ Ishchi qo'shish", "❌ Ishchi o'chirish")
    m.add("📋 Bugungi davomat", "👥 Ishchilar ro'yxati")
    return m

def menyu(uid):
    return admin_menyu() if uid == ADMIN_ID else ishchi_menyu()

# ---------- /start ----------
@bot.message_handler(commands=["start"])
def start(msg):
    uid  = str(msg.from_user.id)
    data = load()

    if uid in data["ishchilar"]:
        ism = data["ishchilar"][uid]["ism"]
        bot.send_message(msg.chat.id,
            f"👋 Xush kelibsiz, *{ism}*!\nNima qilmoqchisiz?",
            parse_mode="Markdown", reply_markup=menyu(msg.from_user.id))
        return

    # yangi foydalanuvchi — adminga xabar
    if msg.from_user.id != ADMIN_ID:
        username = f"@{msg.from_user.username}" if msg.from_user.username else "username yo'q"
        tg_name  = f"{msg.from_user.first_name or ''} {msg.from_user.last_name or ''}".strip()
        try:
            bot.send_message(ADMIN_ID,
                f"🔔 *Yangi foydalanuvchi botga kirdi!*\n"
                f"👤 Telegram: {tg_name}\n"
                f"🔗 {username}\n"
                f"🆔 ID: `{msg.from_user.id}`\n\n"
                f"Uni ro'yxatga qo'shish uchun:\n"
                f"➕ *Ishchi qo'shish* → ID: `{msg.from_user.id}`",
                parse_mode="Markdown")
        except: pass
        bot.send_message(msg.chat.id,
            "👋 Salom!\n\n⏳ Siz hali ro'yxatga kiritilmagansiz.\n"
            "Admin sizni tez orada qo'shadi, kuting.")
        return

    # admin o'zi
    bot.send_message(msg.chat.id,
        "👋 *Admin sifatida xush kelibsiz!*",
        parse_mode="Markdown", reply_markup=admin_menyu())

# ---------- KELISH ----------
@bot.message_handler(func=lambda m: m.text == "✅ Kelish")
def kelish(msg):
    uid  = str(msg.from_user.id)
    data = load()
    if uid not in data["ishchilar"]:
        bot.send_message(msg.chat.id, "⛔ Siz ro'yxatda yo'qsiz. Admin bilan bog'laning."); return

    ism = data["ishchilar"][uid]["ism"]
    s   = sana(); v = vaqt()

    bugun = [x for x in data["tarix"] if x["uid"]==uid and x["sana"]==s]
    if any(x["tur"]=="kelish" for x in bugun):
        kel = next(x for x in bugun if x["tur"]=="kelish")
        bot.send_message(msg.chat.id,
            f"⚠️ Siz bugun allaqachon kelishni belgilagansiz!\n🕐 Vaqt: *{kel['vaqt']}*",
            parse_mode="Markdown"); return

    data["tarix"].append({"uid":uid,"ism":ism,"sana":s,"vaqt":v,"tur":"kelish"})
    save(data)

    bot.send_message(msg.chat.id,
        f"✅ *Kelish qayd etildi!*\n👤 {ism}\n🕐 {v}\n📅 {s}\n\nIsh faoliyatingiz yaxshi bo'lsin! 💪",
        parse_mode="Markdown")

    if msg.from_user.id != ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID,
                f"✅ *Kelish*\n👤 {ism}\n🕐 {v} | 📅 {s}",
                parse_mode="Markdown")
        except: pass

# ---------- KETISH ----------
@bot.message_handler(func=lambda m: m.text == "🏁 Ketish")
def ketish(msg):
    uid  = str(msg.from_user.id)
    data = load()
    if uid not in data["ishchilar"]:
        bot.send_message(msg.chat.id, "⛔ Siz ro'yxatda yo'qsiz."); return

    ism = data["ishchilar"][uid]["ism"]
    s   = sana(); v = vaqt()

    bugun  = [x for x in data["tarix"] if x["uid"]==uid and x["sana"]==s]
    has_in  = next((x for x in bugun if x["tur"]=="kelish"), None)
    has_out = next((x for x in bugun if x["tur"]=="ketish"), None)

    if not has_in:
        bot.send_message(msg.chat.id, "⚠️ Avval ✅ *Kelish* tugmasini bosing!", parse_mode="Markdown"); return
    if has_out:
        bot.send_message(msg.chat.id,
            f"⚠️ Siz bugun allaqachon ketishni belgilagansiz!\n🕐 Vaqt: *{has_out['vaqt']}*",
            parse_mode="Markdown"); return

    kel_dt = datetime.strptime(has_in["vaqt"], "%H:%M")
    ket_dt = datetime.strptime(v, "%H:%M")
    mins   = int((ket_dt - kel_dt).total_seconds() // 60)
    soat   = mins // 60; daqiqa = mins % 60

    data["tarix"].append({"uid":uid,"ism":ism,"sana":s,"vaqt":v,"tur":"ketish","ish_soat":f"{soat}:{daqiqa:02d}"})
    save(data)

    bot.send_message(msg.chat.id,
        f"🏁 *Ketish qayd etildi!*\n👤 {ism}\n"
        f"🕐 Kelish: {has_in['vaqt']} → Ketish: {v}\n"
        f"⏱ Ish vaqti: *{soat} soat {daqiqa} daqiqa*\n📅 {s}\n\nYaxshi dam oling! 🌙",
        parse_mode="Markdown")

    if msg.from_user.id != ADMIN_ID:
        try:
            bot.send_message(ADMIN_ID,
                f"🏁 *Ketish*\n👤 {ism}\n"
                f"🕐 {has_in['vaqt']} → {v} | ⏱ {soat}s {daqiqa}d | 📅 {s}",
                parse_mode="Markdown")
        except: pass

# ---------- DAVOMAT ----------
@bot.message_handler(func=lambda m: m.text == "📊 Mening davomatim")
def mening_davomat(msg):
    uid  = str(msg.from_user.id)
    data = load()
    if uid not in data["ishchilar"]:
        bot.send_message(msg.chat.id, "⛔ Siz ro'yxatda yo'qsiz."); return

    ism    = data["ishchilar"][uid]["ism"]
    yozuvlar = [x for x in data["tarix"] if x["uid"]==uid]
    if not yozuvlar:
        bot.send_message(msg.chat.id, "📊 Hali davomat ma'lumoti yo'q."); return

    kunlar = {}
    for y in yozuvlar:
        kunlar.setdefault(y["sana"], {})[y["tur"]] = y

    matn = f"📊 *{ism} — so'nggi davomat*\n\n"
    for s in sorted(kunlar.keys(), reverse=True)[:7]:
        k = kunlar[s]
        kel = k.get("kelish",{}).get("vaqt","—")
        ket = k.get("ketish",{}).get("vaqt","—")
        ish = k.get("ketish",{}).get("ish_soat","")
        matn += f"📅 *{s}*\n  ✅ {kel}  →  🏁 {ket}"
        if ish: matn += f"  |  ⏱ {ish}"
        matn += "\n\n"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")

# ---------- ADMIN: BUGUNGI DAVOMAT ----------
@bot.message_handler(func=lambda m: m.text == "📋 Bugungi davomat")
def bugungi(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "⛔ Faqat admin uchun."); return
    data = load(); s = sana()
    bugun = [x for x in data["tarix"] if x["sana"]==s]
    if not bugun:
        bot.send_message(msg.chat.id, f"📋 Bugun ({s}) hali hech kim davomat belgilamagan."); return

    ishchilar = {}
    for y in bugun:
        ishchilar.setdefault(y["uid"], {"ism":y["ism"]})[y["tur"]] = y

    matn = f"📋 *Bugungi davomat — {s}*\n\n"
    for uid, info in ishchilar.items():
        kel = info.get("kelish",{}).get("vaqt","—")
        ket = info.get("ketish",{}).get("vaqt","—")
        ish = info.get("ketish",{}).get("ish_soat","")
        matn += f"👤 *{info['ism']}*\n  ✅ {kel}  →  🏁 {ket}"
        if ish: matn += f"  |  ⏱ {ish}"
        matn += "\n\n"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")

# ---------- ADMIN: ISHCHILAR RO'YXATI ----------
@bot.message_handler(func=lambda m: m.text == "👥 Ishchilar ro'yxati")
def royxat(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "⛔ Faqat admin uchun."); return
    data = load()
    if not data["ishchilar"]:
        bot.send_message(msg.chat.id, "👥 Hali hech kim yo'q."); return
    matn = f"👥 *Ishchilar ({len(data['ishchilar'])} nafar)*\n\n"
    for i,(uid,info) in enumerate(data["ishchilar"].items(), 1):
        un = f"@{info.get('username','')}" if info.get('username') else "—"
        matn += f"{i}. *{info['ism']}* | {un}\n"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")

# ---------- ADMIN: ISHCHI QO'SHISH ----------
@bot.message_handler(func=lambda m: m.text == "➕ Ishchi qo'shish")
def qoshish_boshlash(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "⛔ Faqat admin uchun."); return
    bot.send_message(msg.chat.id,
        "Ishchining *Telegram ID* sini kiriting:\n\n"
        "_(Ishchi botga /start bosganida ID si sizga yuboriladi)_",
        parse_mode="Markdown")
    bot.register_next_step_handler(msg, qoshish_id)

def qoshish_id(msg):
    try:
        uid = str(int(msg.text.strip()))
    except:
        bot.send_message(msg.chat.id, "❌ Noto'g'ri ID. Faqat raqam kiriting."); return
    bot.send_message(msg.chat.id, f"Endi *{uid}* uchun ism familiyani kiriting:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: qoshish_ism(m, uid))

def qoshish_ism(msg, uid):
    ism  = msg.text.strip()
    data = load()
    data["ishchilar"][uid] = {
        "ism": ism,
        "username": "",
        "qoshilgan": sana()
    }
    save(data)
    bot.send_message(msg.chat.id,
        f"✅ *{ism}* ro'yxatga qo'shildi!\n🆔 ID: `{uid}`",
        parse_mode="Markdown")
    try:
        bot.send_message(int(uid),
            f"✅ *{ism}*, siz tizimga qo'shildingiz!\n\nEndi davomat belgilashingiz mumkin:",
            parse_mode="Markdown", reply_markup=ishchi_menyu())
    except: pass

# ---------- ADMIN: ISHCHI O'CHIRISH ----------
@bot.message_handler(func=lambda m: m.text == "❌ Ishchi o'chirish")
def ochirish_boshlash(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "⛔ Faqat admin uchun."); return
    data = load()
    if not data["ishchilar"]:
        bot.send_message(msg.chat.id, "Ro'yxat bo'sh."); return
    matn = "O'chirmoqchi bo'lgan ishchining *raqamini* yuboring:\n\n"
    ishchilar_list = list(data["ishchilar"].items())
    for i,(uid,info) in enumerate(ishchilar_list, 1):
        matn += f"{i}. {info['ism']}\n"
    bot.send_message(msg.chat.id, matn, parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: ochirish_bajar(m, ishchilar_list))

def ochirish_bajar(msg, ishchilar_list):
    try:
        idx = int(msg.text.strip()) - 1
        uid, info = ishchilar_list[idx]
    except:
        bot.send_message(msg.chat.id, "❌ Noto'g'ri raqam."); return
    data = load()
    del data["ishchilar"][uid]
    save(data)
    bot.send_message(msg.chat.id, f"✅ *{info['ism']}* o'chirildi.", parse_mode="Markdown")

# ---------- ISHGA TUSHIRISH ----------
print("🤖 EAGLES ON TIME bot ishga tushdi!")
print("To'xtatish uchun: Ctrl+C")
bot.infinity_polling()
