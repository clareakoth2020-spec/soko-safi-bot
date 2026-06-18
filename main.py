from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import random
import string

app = Flask(__name__)

# --- GLOBAL VARIABLES & VARIABLES FOR THE DEMO ---
# Memory database to remember registered users by phone number
persistent_users = {}

user_sessions = {}
AVAILABLE_STORAGE_SLOTS = 120  # Remaining crates in the cold hub
PRICE_PER_CRATE = 20           # KES per crate each day
PRICE_PER_FERTILIZER = 50      # KES per bag of fertilizer

# Simple, helpful market tips
MARKET_TIPS = {
    "en": [
        "💡 *Tip 1:* Keep your green vegetables on a wet mat in the shade before bringing them to us. This stops them from drying out and losing weight!",
        "💡 *Tip 2:* Do not store ripe avocados near raw green tomatoes. The avocados make the tomatoes rot and spoil very fast.",
        "💡 *Tip 3:* Wash your plastic storage crates with clean water and a little bleach every week. This kills the germs that make tomatoes rot.",
        "💡 *Tip 4:* Arrange soft fruits gently and do not pack too many in one deep box. The heavy weight at the top crushes the fruits at the bottom."
    ],
    "sw": [
        "💡 *Dokezo 1:* Weka mboga za majani kwenye mkeka uliolowa maji chini ya kivuli kabla ya kuzileta kwetu ili zisikauke na kupoteza uzito.",
        "💡 *Dokezo 2:* Usiweke parachichi zilizoiva karibu na nyanya mbichi. Parachichi zitafanya nyanya ziharibike na kuoza haraka sana.",
        "💡 *Dokezo 3:* Safisha makreti yako kwa maji safi na jiki kila wiki. Hii inaua viini vinavyofanya nyanya kuoza.",
        "💡 *Dokezo 4:* Panga matunda laini kwa upole na usiweke mengi kwenye sanduku kubwa ili yasiidhinike na kuponda yale ya chini."
    ]
}

@app.route("/main", methods=["POST"])
def whatsapp_reply():
    global AVAILABLE_STORAGE_SLOTS 
    
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From")
    resp = MessagingResponse()
    msg = resp.message()

    # --- REMEMBER OLD USERS ---
    if sender in persistent_users and sender not in user_sessions:
        profile = persistent_users[sender]
        user_sessions[sender] = {
            "step": "main_menu",
            "name": profile["name"],
            "gender": profile["gender"],
            "lang": profile["lang"],
            "wallet_credits": profile.get("wallet_credits", 0.0)
        }
        
        name = profile["name"]
        lang = profile["lang"]
        
        welcome_back = (
            f"🌟 *Welcome back, {name}!* \n\nSoko Safi AI remembers you. How can we help your business today?\n\n_Type *'Menu'* to see what you can do._"
            if lang == "en" else
            f"🌟 *Karibu tena, {name}!* \n\nSoko Safi AI inakutambua. Tutaihudumia biashara yako vipi leo?\n\n_Andika *'Menu'* ili kuona huduma zetu._"
        )
        msg.body(welcome_back)
        return str(resp)

    # --- START NEW CONVERSATION ---
    if sender not in user_sessions:
        user_sessions[sender] = {"step": "lang", "wallet_credits": 0.0}
        msg.body("🌟 Karibu Soko Safi AI! \n\nPlease choose your language / Tafadhali chagua lugha:\n\n1. English\n2. Kiswahili")
        return str(resp)

    session = user_sessions[sender]
    step = session.get("step")
    lang = session.get("lang", "en")
    name = session.get("name", "Trader")

    # --- 1. REGISTRATION SIGN-UP ---
    if step == "lang":
        session["lang"] = "en" if "1" in incoming_msg else "sw"
        session["step"] = "name"
        msg.body("Great! What is your name?" if session["lang"] == "en" else "Sawa! Unaitwa nani?")
        return str(resp)

    elif step == "name":
        session["name"] = incoming_msg
        session["step"] = "gender"
        msg.body("Are you:\n1. Female\n2. Male" if session["lang"] == "en" else "Wewe ni:\n1. Mwanamke\n2. Mwanamume")
        return str(resp)

    elif step == "gender":
        session["gender"] = "Female" if "1" in incoming_msg else "Male"
        session["step"] = "main_menu"
        
        # Save user to memory database
        persistent_users[sender] = {
            "name": session["name"],
            "gender": session["gender"],
            "lang": session["lang"],
            "wallet_credits": 0.0
        }
        
        reg_text = (
            f"🎉 Welcome {session['name']}! You are now registered with Soko Safi AI.\n\n"
            f"Type *'Menu'* anytime to look at our services and use your account."
            if session["lang"] == "en" else
            f"🎉 Karibu {session['name']}! Umesajiliwa na Soko Safi AI.\n\n"
            f"Andika *'Menu'* wakati wowote ili kuona huduma zetu na kutumia akaunti yako."
        )
        msg.body(reg_text)
        return str(resp)

    # --- 2. MAIN MENU ---
    menu_en = f"📋 *Soko Safi Main Menu* (Hi {name})\n\n1. ❄️ Book Cold Storage\n2. ♻️ Waste-to-Credit\n3. 🌱 Buy Fertilizer\n4. 💡 Useful Market Tips\n\nReply with a number (1-4) or type 'Menu' to restart."
    menu_sw = f"📋 *Orodha Kuu ya Soko Safi* (Habari {name})\n\n1. ❄️ Weka Akiba ya Baridi\n2. ♻️ Taka Kuwa Mikopo\n3. 🌱 Nunua Mbolea\n4. 💡 Vidokezo vya Soko\n\nJibu na namba (1-4) au uandike 'Menu' ili kuanza tena."

    # Reset trigger word
    if incoming_msg.lower() in ["menu", "habari", "hi", "m"]:
        session["step"] = "main_menu"
        msg.body(menu_en if lang == "en" else menu_sw)
        return str(resp)

    # --- 3. SUB-MENU CHOICES ---
    if step == "main_menu":
        # 1. COLD STORAGE
        if "1" in incoming_msg:
            session["step"] = "storage_slots"
            storage_text = (
                f"❄️ *Cold Storage space*\n\n"
                f"• Space left today: *{AVAILABLE_STORAGE_SLOTS} Crates*\n"
                f"• Price: KES {PRICE_PER_CRATE} for each crate per day\n\n"
                f"How many crates do you want to book? Enter numbers only:"
                if lang == "en" else
                f"❄️ *Nafasi ya Hifadhi ya Baridi*\n\n"
                f"• Makreti yaliyobaki: *Makreti {AVAILABLE_STORAGE_SLOTS}*\n"
                f"• Gharama: KES {PRICE_PER_CRATE} kwa kila kreti/siku\n\n"
                f"Unataka kuweka akiba ya makreti mangapi? Andika namba pekee:"
            )
            msg.body(storage_text)

        # 2. WASTE-TO-CREDIT 
        elif "2" in incoming_msg:
            session["step"] = "waste_menu"
            waste_menu_text = (
                f"♻️ *Waste-to-Credit Menu*\n\n"
                f"1. 📈 Check my credit balance\n"
                f"2. 🧮 Count new waste credits"
                if lang == "en" else
                f"♻️ *Orodha ya Taka na Mikopo*\n\n"
                f"1. 📈 Angalia salio langu la mikopo\n"
                f"2. 🧮 Piga hesabu ya mikopo mipya ya taka"
            )
            msg.body(waste_menu_text)

        # 3. BUY FERTILIZER
        elif "3" in incoming_msg:
            session["step"] = "fertilizer_quantity"
            fert_text = (
                f"🌱 *Bio-Slurry Fertilizer*\n\n"
                f"• Price: KES {PRICE_PER_FERTILIZER} for each bag.\n\n"
                f"How many bags do you want to buy today? Enter numbers only:"
                if lang == "en" else
                f"🌱 *Mbolea ya Bio-Slurry*\n\n"
                f"• Bei: KES {PRICE_PER_FERTILIZER} kwa kila mfuko.\n\n"
                f"Je, unahitaji mifuko mingapi leo? Weka namba pekee:"
            )
            msg.body(fert_text)

        # 4. TIPS
        elif "4" in incoming_msg:
            random_tip = random.choice(MARKET_TIPS[lang])
            follow_up = (
                f"{random_tip}\n\n_Want another tip? Reply with *4*, or type *'Menu'* to go back._"
                if lang == "en" else
                f"{random_tip}\n\n_Unahitaji dokezo lingine? Tuma namba *4* au uandike *'Menu'* kurudi._"
            )
            msg.body(follow_up)
            
        else:
            msg.body(menu_en if lang == "en" else menu_sw)
        return str(resp)

    # --- 4. COLD STORAGE COUNT LOGIC ---
    if step == "storage_slots":
        try:
            requested_crates = int(''.join(filter(str.isdigit, incoming_msg)))
            if requested_crates <= 0 or requested_crates > AVAILABLE_STORAGE_SLOTS:
                raise ValueError()
            
            session["booked_crates"] = requested_crates
            total_cost = requested_crates * PRICE_PER_CRATE
            session["pending_payment"] = total_cost
            session["payment_type"] = "Cold Storage Booking"
            session["step"] = "billing_gateway"
            
            billing_prompt = (
                f"💳 *Your Total Bill*\n\n"
                f"• Crates chosen: {requested_crates}\n"
                f"• Total money to pay: *KES {total_cost}*\n\n"
                f"Please write the number *{total_cost}* to open the bank payment steps:"
                if lang == "en" else
                f"💳 *Bili Yako Maalum*\n\n"
                f"• Makreti uliyochagua: {requested_crates}\n"
                f"• Jumla ya pesa za kulipa: *KES {total_cost}*\n\n"
                f"Tafadhali andika namba *{total_cost}* ili uone jinsi ya kutuma pesa:"
            )
            msg.body(billing_prompt)
        except ValueError:
            msg.body(f"Wrong number. Please type a number between 1 and space left ({AVAILABLE_STORAGE_SLOTS}):" if lang == "en" else f"Namba mbaya. Weka namba kati ya 1 na nafasi iliyobaki ({AVAILABLE_STORAGE_SLOTS}):")
        return str(resp)

    # --- 5. FERTILIZER BATCH COUNT ---
    if step == "fertilizer_quantity":
        try:
            requested_bags = int(''.join(filter(str.isdigit, incoming_msg)))
            if requested_bags <= 0:
                raise ValueError()
            
            session["ordered_bags"] = requested_bags
            total_cost = requested_bags * PRICE_PER_FERTILIZER
            session["pending_payment"] = total_cost
            session["payment_type"] = "Bio-Slurry Fertilizer"
            session["step"] = "billing_gateway"
            
            billing_prompt = (
                f"💳 *Your Total Bill*\n\n"
                f"• Bags chosen: {requested_bags}\n"
                f"• Total money to pay: *KES {total_cost}*\n\n"
                f"Please write the number *{total_cost}* to open the bank payment steps:"
                if lang == "en" else
                f"💳 *Bili Yako Maalum*\n\n"
                f"• Mifuko uliyochagua: {requested_bags}\n"
                f"• Jumla ya pesa za kulipa: *KES {total_cost}*\n\n"
                f"Tafadhali andika namba *{total_cost}* ili uone jinsi ya kutuma pesa:"
            )
            msg.body(billing_prompt)
        except ValueError:
            msg.body("Please type a valid number of bags:" if lang == "en" else "Tafadhali weka idadi ya mifuko kwa kutumia namba pekee:")
        return str(resp)

    # --- 6. EQUITY BANK & M-PESA GATEWAY ---
    if step == "billing_gateway":
        expected_payment = session.get("pending_payment", 0)
        
        payment_gateway_text = (
            f"📥 *How to pay KES {expected_payment}:*\n\n"
            f"Choose ONE way to pay below:\n\n"
            f"👉 *OPTION 1: M-Pesa Till Number (Buy Goods)*\n"
            f"• Till Number: *3378560*\n\n"
            f"👉 *OPTION 2: Equity Bank Paybill*\n"
            f"• Business Number: *247247*\n"
            f"• Account Number: *0290179939286*\n\n"
            f"Once you send the money on your phone, *please type and send the M-Pesa/Equity Transaction Code* (e.g. RG85XX390) here to verify:"
            if lang == "en" else
            f"📥 *Jinsi ya kulipa KES {expected_payment}:*\n\n"
            f"Chagua njia MOJA ya kulipa hapa chini:\n\n"
            f"👉 *NJIA YA 1: M-Pesa Till Number (Buy Goods)*\n"
            f"• Namba ya Till: *3378560*\n\n"
            f"👉 *NJIA YA 2: Equity Bank Paybill*\n"
            f"• Namba ya Biashara (Paybill): *247247*\n"
            f"• Namba ya Akaunti: *0290179939286*\n\n"
            f"Baada ya kutuma pesa kwenye simu yako, *tafadhali andika na utume ule msimbo wa muamala/Transaction Code* (kero: RG85XX390) hapa hapa:"
        )
        session["step"] = "payment_receipting"
        msg.body(payment_gateway_text)
        return str(resp)

    if step == "payment_receipting":
        tx_code = incoming_msg.strip().upper()
        payment_type = session.get("payment_type", "Order")
        
        if len(tx_code) < 4:
            msg.body("Please enter a valid payment transaction reference code:" if lang == "en" else "Tafadhali weka msimbo halali wa muamala ulioongezwa kwenye simu yako:")
            return str(resp)
            
        if "Storage" in payment_type:
            crates = session.get("booked_crates", 0)
            AVAILABLE_STORAGE_SLOTS = max(0, AVAILABLE_STORAGE_SLOTS - crates)
            
            receipt_text = (
                f"✅ *Payment Done & Confirmed!*\n\n"
                f"• Service: {payment_type}\n"
                f"• Confirmed Code: {tx_code}\n"
                f"• Space Booked: *{crates} Crates Saved*\n\n"
                f"Please show this message and your code *{tx_code}* to our worker at the cold room hub when dropping your produce.\n\n"
                f"🤝 Thank you for choosing Soko Safi AI! Welcome again."
                if lang == "en" else
                f"✅ *Malipo Yamethibitishwa!*\n\n"
                f"• Huduma: {payment_type}\n"
                f"• Msimbo wa Muamala: {tx_code}\n"
                f"• Nafasi Yako: *Makreti {crates} Yamehifadhiwa*\n\n"
                f"Onyesha ujumbe huu na msimbo wako *{tx_code}* kwa mfanyakazi wetu wa hifadhi ya baridi ukileta mazao yako.\n\n"
                f"🤝 Asante kwa kuchagua Soko Safi AI! Karibu tena."
            )
        else:
            bags = session.get("ordered_bags", 0)
            receipt_text = (
                f"✅ *Payment Done & Confirmed!*\n\n"
                f"• Product: {payment_type}\n"
                f"• Confirmed Code: {tx_code}\n"
                f"• Amount Saved: *{bags} Fertilizer Bag(s)*\n\n"
                f"Show this code *{tx_code}* at our marketplace point to collect your bags.\n\n"
                f"🤝 Thank you for choosing Soko Safi AI! Welcome again."
                if lang == "en" else
                f"✅ *Malipo Yamethibitishwa!*\n\n"
                f"• Bidhaa: {payment_type}\n"
                f"• Msimbo wa Muamala: {tx_code}\n"
                f"• Kiasi: *Mifuko {bags} ya Mbolea*\n\n"
                f"Onyesha msimbo huu *{tx_code}* kwenye kituo chetu sokoni ili kuchukua mifuko yako.\n\n"
                f"🤝 Asante kwa kuchagua Soko Safi AI! Karibu tena."
            )
            
        msg.body(receipt_text)
        session["step"] = "main_menu" 
        return str(resp)

    # --- 7. WASTE WALLET LOGIC ---
    if step == "waste_menu":
        current_wallet_balance = session.get("wallet_credits", 0.0)
        
        if "1" in incoming_msg:
            session["step"] = "main_menu"
            balance_text = (
                f"📈 *Your Soko Safi Balance*\n\n"
                f"• Account Owner: {name}\n"
                f"• Free Crate Storage Balance: *{current_wallet_balance} Days*\n\n"
                f"Bring more market waste sorting scraps to earn free days! Type 'Menu' to go back."
                if lang == "en" else
                f"📈 *Salio Lako la Soko Safi*\n\n"
                f"• Mmiliki wa Akaunti: {name}\n"
                f"• Salio la Kreti za Bure: *Siku {current_wallet_balance}*\n\n"
                f"Leta taka zaidi sokoni ili upate siku za bure! Andika 'Menu' kurudi."
            )
            msg.body(balance_text)
            
        elif "2" in incoming_msg:
            session["step"] = "awaiting_waste_calc"
            msg.body(
                f"♻️ *Waste Calculator Engine*\n\n"
                f"Rate: *30 KG Waste = 1 Free Crate Day*\n"
                f"Your old unused credit balance: *{current_wallet_balance} Days*\n\n"
                f"Please type the total kilograms (KG) of waste you collected today:"
                if lang == "en" else
                f"♻️ *Kikokotoo Kipya cha Taka*\n\n"
                f"Kipimo: *Kilo 30 za Taka = Siku 1 ya Kreti Bure*\n"
                f"Salio lako la zamani ambalo hujatumia: *Siku {current_wallet_balance}*\n\n"
                f"Tafadhali andika jumla ya kilo (KG) za taka ulizokusanya leo:"
            )
        else:
            msg.body("Wrong choice. Type 1 or 2:" if lang == "en" else "Chaguo mbaya. Tuma 1 au 2:")
        return str(resp)

    if step == "awaiting_waste_calc":
        try:
            waste_kg = float(''.join(c for c in incoming_msg if c.isdigit() or c=='.'))
            new_credits_earned = round(waste_kg / 30.0, 1)
            
            historical_credits = session.get("wallet_credits", 0.0)
            compounded_net_total = round(historical_credits + new_credits_earned, 1)
            
            session["wallet_credits"] = compounded_net_total
            if sender in persistent_users:
                persistent_users[sender]["wallet_credits"] = compounded_net_total
                
            calc_response = (
                f"📊 *Waste Accounting Calculations*\n\n"
                f"• Fresh Waste brought: {waste_kg} KG\n"
                f"• New Credits earned: +{new_credits_earned} Days\n"
                f"• Old Balance: {historical_credits} Days\n"
                f"• *Your New Total Balance: {compounded_net_total} Free Crate Days*\n\n"
                f"Drop this waste at our bio-bins to add it to your profile ledger. 🤝 Thank you for choosing Soko Safi AI! Type 'Menu' to go back."
                if lang == "en" else
                f"📊 *Mahesabu ya Taka na Mikopo*\n\n"
                f"• Taka ulizoleta leo: {waste_kg} KG\n"
                f"• Mikopo mipya: +{new_credits_earned} Siku\n"
                f"• Salio la zamani: {historical_credits} Siku\n"
                f"• *Salio Lako Jipya Jumla: Siku {compounded_net_total} za Kreti Bure*\n\n"
                f"Weka taka hizi kwenye pipa letu maalum ili ziongezwe kwenye akaunti yako. 🤝 Asante kwa kuchagua Soko Safi AI! Andika 'Menu' kurudi."
            )
            msg.body(calc_response)
            session["step"] = "main_menu"
        except ValueError:
            msg.body("Please type a valid number for waste kilograms (e.g. 45):" if lang == "en" else "Tafadhali weka namba halali ya kilo pekee (kero: 45):")
        return str(resp)

    msg.body(menu_en if lang == "en" else menu_sw)
    return str(resp)
@app.route("/ping", methods=["GET"])
def keep_alive():
    return "Soko Safi Engine Active", 200
if __name__ == "__main__":
    app.run()
