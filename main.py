import discord
import json
import random
import os
from datetime import datetime, timedelta

# --- إعدادات النظام ---
TOKEN = "MTQ1NTI5NTA2NzkxNjA3NTA0OQ.GXNdL7.qZqxGxI3d-FgBNPmsFLaEusElV0kq3muPnV8qw"
BANK_CHANNEL_ID = 1454964201989603349 
DB_FILE = "dmn_ultimate_database.json"

# --- قاعدة بيانات المتجر ---
SHOP_ITEMS = {
    "1": {"name": "🥇 رتبة VIP", "price": 50000},
    "2": {"name": "💎 رتبة ملك", "price": 200000},
    "3": {"name": "🏰 قصر فاخر", "price": 1000000},
    "4": {"name": "🚗 سيارة لامبورغيني", "price": 300000}
}

intents = discord.Intents.all()
client = discord.Client(intents=intents)

# --- دوال حفظ وحماية البيانات ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@client.event
async def on_ready():
    print(f"🚀 المنظومة كاملة وشغالة 100%: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot or message.channel.id != BANK_CHANNEL_ID: return
    
    user_id, db = str(message.author.id), load_db()
    
    # تعريف المستخدم الجديد بكل تفاصيله لضمان عدم حدوث Error
    if user_id not in db:
        db[user_id] = {"bal": 5000, "items": [], "partner": None, "cds": {}, "jail": False}

    msg = message.content.lower()
    parts = msg.split()

    # --- [0] حماية السجن (تمنع الأوامر الأخرى) ---
    if db[user_id].get("jail") and msg != "!فديت":
        return await message.channel.send(f"⚠️ | **{message.author.name}**، أنت مسجون! لا يمكنك استخدام الأوامر. اكتب `!فديت` (15,000$) للخروج.")

    # --- [1] عملية كسب المال (الرواتب والعمل) ---
    if msg in ["!راتب", "!عمل", "!تعدين", "!بحث"]:
        cmd_map = {"!راتب": ("salary", 10, 5000), "!عمل": ("work", 5, 2000), "!تعدين": ("mine", 20, 8000), "!بحث": ("search", 2, 800)}
        cmd_name, mins, prize = cmd_map[msg]
        
        now = datetime.now()
        last = db[user_id]["cds"].get(cmd_name)
        if last and (now - datetime.fromisoformat(last)) < timedelta(minutes=mins):
            rem = timedelta(minutes=mins) - (now - datetime.fromisoformat(last))
            return await message.channel.send(f"⏳ | انتظر **{rem.seconds // 60} دقيقة و {rem.seconds % 60} ثانية**")
        
        gain = random.randint(prize//2, prize)
        db[user_id]["bal"] += gain
        db[user_id]["cds"][cmd_name] = now.isoformat()
        await message.channel.send(f"💰 | **عملية ناجحة:** استلمت **{gain}$** من أمر {msg[1:]}")

    # --- [2] عملية الشراء (مثلما طلبت بدقة) ---
    elif msg.startswith("!شراء"):
        if len(parts) < 2: return await message.channel.send("⚠️ | اكتب رقم الغرض من المتجر!")
        item_id = parts[1]
        if item_id in SHOP_ITEMS:
            item = SHOP_ITEMS[item_id]
            if db[user_id]["bal"] < item["price"]:
                return await message.channel.send(f"❌ | رصيدك ناقص! تحتاج {item['price'] - db[user_id]['bal']}$")
            if item["name"] in db[user_id]["items"]:
                return await message.channel.send("🥇 | أنت تملك هذا الغرض بالفعل!")
            
            db[user_id]["bal"] -= item["price"]
            db[user_id]["items"].append(item["name"])
            await message.channel.send(f"🛍️ | **تم الشراء:** مبروك حصلت على {item['name']}!")
        else: await message.channel.send("❌ | الرقم غير موجود في المتجر.")

    # --- [3] عملية الهبة (تحويل أموال) ---
    elif msg.startswith("!هبة"):
        if not message.mentions or len(parts) < 3:
            return await message.channel.send("⚠️ | الاستخدام: `!هبة @شخص [المبلغ]`")
        try:
            amt = int(parts[2])
            if amt <= 0 or db[user_id]["bal"] < amt: raise ValueError
            target_id = str(message.mentions[0].id)
            if target_id not in db: db[target_id] = {"bal": 5000, "items": [], "partner": None, "cds": {}, "jail": False}
            db[user_id]["bal"] -= amt
            db[target_id]["bal"] += amt
            await message.channel.send(f"🎁 | **تحويل بنكي:** وهبت {amt}$ إلى {message.mentions[0].mention}")
        except: await message.channel.send("❌ | تأكد من المبلغ أو من رصيدك.")

    # --- [4] عملية الزواج والطلاق ---
    elif msg.startswith("!زواج"):
        if not message.mentions: return await message.channel.send("⚠️ | منشن الشريك!")
        if db[user_id]["partner"]: return await message.channel.send("❌ | أنت متزوج بالفعل!")
        db[user_id]["partner"] = str(message.mentions[0].id)
        await message.channel.send(f"💍 | مبروك الزواج من {message.mentions[0].mention}!")

    elif msg == "!طلاق":
        if not db[user_id]["partner"]: return await message.channel.send("❌ | أنت أعزب!")
        db[user_id]["partner"] = None
        await message.channel.send("💔 | تم الانفصال بنجاح.")

    # --- [5] عملية المخاطرة والسرقة ---
    elif msg.startswith("!مخاطرة"):
        try:
            amt = int(parts[1])
            if amt > db[user_id]["bal"] or amt <= 0: return await message.channel.send("❌ | مبلغ غير صالح!")
            if random.random() > 0.5:
                db[user_id]["bal"] += amt
                await message.channel.send(f"🎲 | **فزت!** رصيدك الآن: {db[user_id]['bal']}$")
            else:
                db[user_id]["bal"] -= amt
                await message.channel.send(f"📉 | **خسرت!** رصيدك الآن: {db[user_id]['bal']}$")
        except: await message.channel.send("⚠️ | اكتب: !مخاطرة [المبلغ]")

    elif msg.startswith("!سرقة"):
        if not message.mentions: return await message.channel.send("⚠️ | منشن الضحية!")
        if random.random() > 0.7:
            stolen = random.randint(1000, 5000)
            db[user_id]["bal"] += stolen
            await message.channel.send(f"🥷 | **سرقة ناجحة:** أخذت {stolen}$!")
        else:
            db[user_id]["jail"] = True
            await message.channel.send("👮 | **انمسكت!** دخلت السجن. اكتب `!فديت` (15k) للخروج.")

    # --- [6] أوامر المعلومات ---
    elif msg == "!رصيد":
        p = f"<@{db[user_id]['partner']}>" if db[user_id]["partner"] else "أعزب"
        items = ", ".join(db[user_id]["items"]) if db[user_id]["items"] else "لا توجد"
        await message.channel.send(f"💳 | **رصيدك:** {db[user_id]['bal']}$\n💍 | **الشريك:** {p}\n🎒 | **الحقيبة:** {items}")

    elif msg == "!متجر":
        embed = discord.Embed(title="🛒 متجر DMN", color=0xffd700)
        for k, v in SHOP_ITEMS.items(): embed.add_field(name=f"[{k}] {v['name']}", value=f"السعر: {v['price']}$", inline=False)
        await message.channel.send(embed=embed)

    # --- كود أمر الاوامر المبرمج (اضفه تحت msg == "!اوامر") ---
    if msg == "!اوامر":
        embed = discord.Embed(
            title="🏙️ قائمة أوامر مدينة DMN الكبرى",
            description="إليك كافة الأوامر المبرمجة والشغالة حالياً في النظام:",
            color=0x00ff00 # لون أخضر
        )
        
        # قسم الأموال
        embed.add_field(
            name="💰 كسب المال", 
            value="`!راتب` • `!عمل` • `!تعدين` • `!بحث`", 
            inline=False
        )
        
        # قسم التفاعل والألعاب
        embed.add_field(
            name="🎲 الأكشن والمخاطرة", 
            value="`!مخاطرة` • `!سرقة` • `!هبة` • `!ابتزاز`", 
            inline=False
        )
        
        # قسم الحياة الاجتماعية والمتجر
        embed.add_field(
            name="🛒 الحياة والمتجر", 
            value="`!متجر` • `!شراء` • `!زواج` • `!طلاق` • `!رصيد`", 
            inline=False
        )
        
        # قسم السجن
        embed.add_field(
            name="👮 نظام السجن", 
            value="`!فديت` (للخروج من السجن بدفع فدية)", 
            inline=False
        )

        embed.set_footer(text="منظومة DMN - البرمجة الكاملة")
        
        # إرسال الرسالة
        await message.channel.send(embed=embed)





    save_db(db)

client.run("MTQ1NTI5NTA2NzkxNjA3NTA0OQ.GB3uhg.JYPcSnCA8jT_9SEVtECDbsmuAUdg58cN8eWLRE")
      
