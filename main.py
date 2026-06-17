from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import random
import string

app = Flask(__name__)

# Mock Databases for the Demo Environment
# persistent_users logs registered profiles permanently so they bypass onboarding
persistent_users = {
    # Example test entry:
    # "+254719227699": {"name": "Clare", "gender": "Female", "lang": "en", "wallet_credits": 2.5}
}

# Live dynamic operational states
user_sessions = {}
AVAILABLE_STORAGE_SLOTS = 120  # Total physical crate capacity of the cold hub
PRICE_PER_CRATE = 20           # KES per crate per day
PRICE_PER_FERTILIZER = 50      # KES per bottle/bag

# Array of randomized contextual tips for high-level agriculture value
MARKET_TIPS = {
    "en": [
        "💡 *Smart Market Tip 1:* Keep leafy vegetables on moist, shaded mats prior to cooling to prevent rapid structural water loss and wilting.",
        "💡 *Smart Market Tip 2:* Never stack high-ethylene producers like ripe avocados directly next to fresh green tomatoes; it forces rapid pre-mature ripening.",
        "💡 *Smart Market Tip 3:* Clean storage crates with clean chlorinated water weekly to wipe out soft-rot fungal spores before they attach to delicate tomato skins.",
        "💡 *Smart Market Tip 4:* Gently layer soft fruits in shallow crates rather than deep boxes. High structural transit weight causes hidden compression bruising."
    ],
    "sw": [
        "💡 *Vidokezo vya Soko 1:* Weka mboga za majani kwenye mikeka yenye unyevu chini ya kivuli kabla ya kuhifadhi ili kuzuia zisinyeuke haraka.",
        "💡 *Vidokezo vya Soko 2:* Usiweke parachichi zilizoiva karibu na nyanya mbichi; gesi ya parachichi itafanya nyanya ziharibike na kuoza kwa haraka.",
        "💡 *Vidokezo vya Soko 3:* Safisha makreti yako kwa maji safi ya klorini kila wiki ili kuua viini vya kuvu vinavyosababisha nyanya kuoza.",
        "💡 *Vidokezo vya Soko 4:* Panga matunda laini kwa upole kwenye makreti yasiyo ya kina kirefu badala ya masanduku makubwa ili kuzuia yasipondane."
    ]
}

def generate_secure_tag():
    """Generates a secure unique code for physical warehouse authorization tracking"""
    return "SSAI-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route("/main", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From")
    resp = MessagingResponse()
    msg = resp.message()

    # --- PERSISTENT USER RECOGNITION LOOP ---
    if sender in persistent_users and sender not in user_sessions:
        # User is already fully registered in our database, greet them warmly instantly
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
            f"🌟 *Welcome Back, {name}!* \n\nSoko Safi AI recognizes your profile. How can we serve your marketplace enterprise today?\n\n_Type *'Menu'* to display your system operation options._"
            if lang == "en" else
            f"🌟 *Karibu Tena, {name}!* \n\nSoko Safi AI inatambua nambari yako. Je, tukusaidie vipi leo katika biashara yako?\n\n_Andika *'Menu'* ili kuona orodha ya huduma._"
        )
        msg.body(welcome_back)
        return str(resp)

    # --- NEW CONVERSATION INITIALIZATION ---
    if sender not in user_sessions:
        user_sessions[sender] = {"step": "lang", "wallet_credits": 0.0}
        msg.body("🌟 Karibu Soko Safi AI! \n\nPlease choose your language / Tafadhali chagua lugha:\n\n1. English\n2. Kiswahili")
        return str(resp)

    session = user_sessions[sender]
    step = session.get("step")
    lang = session.get("lang", "en")
    name = session.get("name", "Trader")

    # --- 1. NEW REGISTRATION ONBOARDING PIPELINE ---
    if step == "lang":
        session["lang"] = "en" if "1" in incoming_msg else "sw"
        session["step"] = "name"
        msg.body("Great! What is your name?" if session["lang"] == "en" else "Sawa! Unaitwa nani?")
        return str(resp)

    elif step == "name":
        session["name"] = incoming_msg
        session["step"] = "gender"
        msg.body("Are you Male or Female?\n1. Female\n2. Male" if session["lang"] == "en" else "Wewe ni Mwanamke au Mwanamume?\n1. Mwanamke\n2. Mwanamume")
        return str(resp)

    elif step == "gender":
        session["gender"] = "Female" if "1" in incoming_msg else "Male"
        session["step"] = "main_menu"
        
        # Save to persistent storage dictionary immediately to bypass next time
        persistent_users[sender] = {
            "name": session["name"],
            "gender": session["gender"],
            "lang": session["lang"],
            "wallet_credits": 0.0
        }
        
        reg_text = (
            f"🎉 Welcome {session['name']}! You are now successfully registered with Soko Safi AI.\n\n"
            f"We track demographic impact to support small-scale entrepreneurs. Send 'Menu' anytime to access your control panel."
            if session["lang"] == "en" else
            f"🎉 Karibu {session['name']}! Umesajiliwa kikamilifu na Soko Safi AI.\n\n"
            f"Tunasajili jinsia ili kusaidia wafanyabiashara wadogo. Tuma 'Menu' wakati wowote kupata huduma."
        )
        msg.body(reg_text)
        return str(resp)

    # --- 2. MENU INTERACTIVE FRAMEWORK ---
    menu_en = f"📋 *Soko Safi Main Menu* (Hi {name})\n\n1. ❄️ Book Cold Storage\n2. ♻️ Waste-to-Credit System\n3. 🌱 Buy Bio-Slurry Fertilizer\n4. 💡 Smart Market Tips\n\nReply with a number (1-4) or type 'Menu' to reset here."
    menu_sw = f"📋 *Orodha Kuu ya Soko Safi* (Habari {name})\n\n1. ❄️ Weka Akiba ya Baridi\n2. ♻️ Mfumo wa Taka kuwa Mikopo\n3. 🌱 Nunua Mbolea ya Bio-Slurry\n4. 💡 Vidokezo vya Soko\n\nJibu kwa nambari (1-4) au uandike 'Menu' kurudi hapa."

    # Global explicit reset interception trigger
    if incoming_msg.lower() in ["menu", "habari", "hi", "m"]:
        session["step"] = "main_menu"
        msg.body(menu_en if lang == "en" else menu_sw)
        return str(resp)

    # --- 3. SUB-MENU CORE CONTROLLERS ---
    if step == "main_menu":
        # OPTION 1: COLD STORAGE MAIN INTERACTION
        if "1" in incoming_msg:
            session["step"] = "storage_slots"
            storage_text = (
                f"❄️ *Soko Safi Cold Hub Capacity*\n\n"
                f"• Current Available Space: *{AVAILABLE_STORAGE_SLOTS} Crates*\n"
                f"• Fee: KES {PRICE_PER_CRATE} per crate/day\n\n"
                f"Please type the number of crates you want to book right now:"
                if lang == "en" else
                f"❄️ *Uwezo wa Kituo cha Hifadhi ya Baridi*\n\n"
                f"• Nafasi Iliyobaki: *Makreti {AVAILABLE_STORAGE_SLOTS}*\n"
                f"• Gharama: KES {PRICE_PER_CRATE} kwa kila kreti/siku\n\n"
                f"Tafadhali andika idadi ya makreti unayotaka kuhifadhi sasa hivi:"
            )
            msg.body(storage_text)

        # OPTION 2: WASTE TO CREDIT MULTI-BUTTON SUB ROUTING
        elif "2" in incoming_msg:
            session["step"] = "waste_menu"
            waste_menu_text = (
                f"♻️ *Waste-to-Credit Ledger Portal*\n\n"
                f"1. 📈 Check Current Credit Balance\n"
                f"2. 🧮 Calculate New Earned Credits"
                if lang == "en" else
                f"♻️ *Mfumo wa Taka na Mikopo*\n\n"
                f"1. 📈 Angalia Salio la Mikopo Yako\n"
                f"2. 🧮 Piga Hesabu ya Mikopo Mipya"
            )
            msg.body(waste_menu_text)

        # OPTION 3: BIO-FERTILIZER PACKAGES
        elif "3" in incoming_msg:
            session["step"] = "fertilizer_quantity"
            fert_text = (
                f"🌱 *Bio-Slurry Organic Fertilizer Product Portal*\n\n"
                f"• Price: KES {PRICE_PER_FERTILIZER} per customized container bag.\n\n"
                f"How many bags do you want to purchase today? (Please enter numbers only):"
                if lang == "en" else
                f"🌱 *Mbolea ya Kikaboni ya Bio-Slurry*\n\n"
                f"• Bei: KES {PRICE_PER_FERTILIZER} kwa kila mfuko.\n\n"
                f"Je, unahitaji mifuko mingapi leo? (Tafadhali weka nambari pekee):"
            )
            msg.body(fert_text)

        # OPTION 4: CONTEXTUAL ROTATING MARKET ADVISORY PUSH
        elif "4" in incoming_msg:
            random_tip = random.choice(MARKET_TIPS[lang])
            follow_up = (
                f"{random_tip}\n\n_Need another insight? Type *4* to pull up an alternate advisory tip, or type *'Menu'* to return to main operations._"
                if lang == "en" else
                f"{random_tip}\n\n_Je, unahitaji dokezo lingine? Tuma nambari *4* au uandike *'Menu'* kurudi kwenye orodha kuu._"
            )
            msg.body(follow_up)
            # Maintain step state at main_menu so they can keep pulling tips by pressing '4'
            
        else:
            msg.body(menu_en if lang == "en" else menu_sw)
        return str(resp)

    # --- 4. COLD STORAGE PROCESSING LOGIC ---
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
                f"💳 *Booking Calculation Invoice*\n\n"
                f"• Crates Specified: {requested_crates}\n"
                f"• Cost Parameters: {requested_crates} x KES {PRICE_PER_CRATE}\n"
                f"• Total Amount Due: *KES {total_cost}*\n\n"
                f"To initiate payment securely via Mpesa or Bank Paybill, please type the exact amount (*{total_cost}*) to trigger transaction configuration details:"
                if lang == "en" else
                f"💳 *Invoisi ya Malipo ya Hifadhi*\n\n"
                f"• Makreti Yaliyochaguliwa: {requested_crates}\n"
                f"• Maelezo ya Gharama: {requested_crates} x KES {PRICE_PER_CRATE}\n"
                f"• Jumla Kuu ya Malipo: *KES {total_cost}*\n\n"
                f"Ili kulipia kupitia Mpesa au Paybill ya Benki, tafadhali andika kiasi halisi cha fedha (*{total_cost}*) ili kuona maelezo ya malipo:"
            )
            msg.body(billing_prompt)
        except ValueError:
            msg.body(f"Invalid volume value. Please request a quantity number between 1 and remaining space ({AVAILABLE_STORAGE_SLOTS}):" if lang == "en" else f"Idadi batili. Tafadhali weka nambari kati ya 1 na nafasi iliyobaki ({AVAILABLE_STORAGE_SLOTS}):")
        return str(resp)

    # --- 5. FERTILIZER LOGIC BRANCH ---
    if step == "fertilizer_quantity":
        try:
            requested_bags = int(''.join(filter(str.isdigit, incoming_msg)))
            if requested_bags <= 0:
                raise ValueError()
            
            session["ordered_bags"] = requested_bags
            total_cost = requested_bags * PRICE_PER_FERTILIZER
            session["pending_payment"] = total_cost
            session["payment_type"] = "Bio-Slurry Fertilizer Order"
            session["step"] = "billing_gateway"
            
            billing_prompt = (
                f"💳 *Product Invoice Generation*\n\n"
                f"• Fertilizer Requested: {requested_bags} Bags\n"
                f"• Financial Multiplier: {requested_bags} x KES {PRICE_PER_FERTILIZER}\n"
                f"• Net Amount Due: *KES {total_cost}*\n\n"
                f"To complete your purchase transaction via Mpesa or Bank Paybill, please re-type the exact total figure (*{total_cost}*) to receive payment routes:"
                if lang == "en" else
                f"💳 *Invoisi ya Mbolea Mipya*\n\n"
                f"• Mifuko Inayohitajika: {requested_bags}\n"
                f"• Thamani ya Fedha: {requested_bags} x KES {PRICE_PER_FERTILIZER}\n"
                f"• Jumla ya Malipo: *KES {total_cost}*\n\n"
                f"Ili kukamilisha malipo kupitia Mpesa au Paybill ya Benki, tafadhali andika kiasi cha fedha (*{total_cost}*) ili kuona maelezo ya akaunti:"
            )
            msg.body(billing_prompt)
        except ValueError:
            msg.body("Please type a valid structured whole quantity value number:" if lang == "en" else "Tafadhali weka idadi ya mifuko kwa kutumia nambari pekee:")
        return str(resp)

    # --- 6. BILLING DEPLOYMENT SYSTEM ---
    if step == "billing_gateway":
        expected_payment = session.get("pending_payment", 0)
        
        # Capture verification mechanism
        payment_gateway_text = (
            f"📥 *Soko Safi Secure Escrow Node Gateway*\n\n"
            f"Please input and complete your payment using the official parameters below:\n\n"
            f"• *Lipa na M-PESA Paybill Option*\n"
            f"  - Business Number: *400200*\n"
            f"  - Account Number: *0719227699* (Soko Safi AI Node)\n"
            f"  - Exact Amount: KES {expected_payment}\n\n"
            f"• *Alternative Co-operative Bank Route*\n"
            f"  - Paybill Number: *400200*\n"
            f"  - Direct Ledger Account: *011000000000*\n\n"
            f"Once you complete the terminal prompt, type *'CONFIRM'* to verify entry logistics."
            if lang == "en" else
            f"📥 *Njia Salama ya Malipo - Soko Safi AI*\n\n"
            f"Tafadhali kamilisha malipo kwa kutumia maelezo yafuatayo:\n\n"
            f"• *Njia ya Lipa na M-PESA Paybill*\n"
            f"  - Nambari ya Biashara (Bus. No): *400200*\n"
            f"  - Nambari ya Akaunti (Acc. No): *0719227699*\n"
            f"  - Kiasi Halisi: KES {expected_payment}\n\n"
            f"• *Njia ya Benki ya Co-operative*\n"
            f"  - Nambari ya Paybill: *400200*\n"
            f"  - Nambari ya Akaunti ya Benki: *011000000000*\n\n"
            f"Baada ya kukamilisha muamala kwenye simu yako, andika *'CONFIRM'* ili kuthibitisha."
        )
        session["step"] = "payment_receipting"
        msg.body(payment_gateway_text)
        return str(resp)

    if step == "payment_receipting":
        if "confirm" in incoming_msg.lower():
            secure_tag = generate_secure_tag()
            payment_type = session.get("payment_type", "Soko Safi Order")
            
            if "Storage" in payment_type:
                crates = session.get("booked_crates", 0)
                # Deduct slots globally in real-time
                global AVAILABLE_STORAGE_SLOTS
                AVAILABLE_STORAGE_SLOTS = max(0, AVAILABLE_STORAGE_SLOTS - crates)
                
                receipt_text = (
                    f"✅ *Payment Verified & Escrow Logged!*\n\n"
                    f"• Service: {payment_type}\n"
                    f"• Secured Allocation: *{crates} Hub Crates Reserved*\n"
                    f"• Security Auth Tag: `{secure_tag}`\n\n"
                    f"Present this secure authorization tag text to the on-site operator at Ahero/Kibuye cold hub storage room during intake drop-off.\n\n"
                    f"🤝 Thank you for choosing Soko Safi AI! Welcome again to clean marketplace operations."
                    if lang == "en" else
                    f"✅ *Malipo Yamethibitishwa na Kusajiliwa!*\n\n"
                    f"• Huduma: {payment_type}\n"
                    f"• Nafasi Yako: *Makreti {crates} Yamehifadhiwa*\n"
                    f"• Nambari ya Siri (Tag): `{secure_tag}`\n\n"
                    f"Onyesha nambari hii ya siri kwa msimamizi wetu katika kituo cha hifadhi cha Ahero/Kibuye wakati wa kuleta mazao yako.\n\n"
                    f"🤝 Asante sana kwa kuchagua Soko Safi AI! Karibu tena kufanya biashara safi sokoni."
                )
            else:
                bags = session.get("ordered_bags", 0)
                receipt_text = (
                    f"✅ *Payment Verified & Escrow Logged!*\n\n"
                    f"• Product Purchased: {payment_type}\n"
                    f"• Volume Secured: *{bags} Organic Fertilizer Bag(s)*\n"
                    f"• Collection Reference Tag: `{secure_tag}`\n\n"
                    f"Present this tag to your marketplace agricultural distribution node to pick up your packaged product boxes.\n\n"
                    f"🤝 Thank you for choosing Soko Safi AI! Welcome again to clean marketplace operations."
                    if lang == "en" else
                    f"✅ *Malipo Yamethibitishwa Kikamilifu!*\n\n"
                    f"• Bidhaa: {payment_type}\n"
                    f"• Mifuko Uliyochukua: *Mifuko {bags} ya Mbolea*\n"
                    f"• Nambari ya Msimbo (Tag): `{secure_tag}`\n\n"
                    f"Onyesha msimbo huu kwenye kituo chetu sokoni ili kuchukua mbolea yako ya Bio-Slurry.\n\n"
                    f"🤝 Asante sana kwa kuchagua Soko Safi AI! Karibu tena kufanya biashara safi sokoni."
                )
                
            msg.body(receipt_text)
            session["step"] = "main_menu"  # Loop safely back to core menu loop
        else:
            msg.body("Please complete transaction execution or type 'CONFIRM' to release authorization code tags:" if lang == "en" else "Tafadhali kamilisha malipo kisha uandike neno 'CONFIRM' ili kupata risiti yako:")
        return str(resp)

    # --- 7. DETAILED SUB-MENU ACCOUNTING ENGINE (WASTE SYSTEM) ---
    if step == "waste_menu":
        current_wallet_balance = session.get("wallet_credits", 0.0)
        
        # Option A: View current wallet status
        if "1" in incoming_msg:
            session["step"] = "main_menu"
            balance_text = (
                f"📈 *Soko Safi Digital Wallet Ledger*\n\n"
                f"• Registered Holder: {name}\n"
                f"• Available Safe Storage Balance: *{current_wallet_balance} Crate Days*\n\n"
                f"Earn more anytime by dropping raw sorting waste scraps at our hub processors! Type 'Menu' to go back."
                if lang == "en" else
                f"📈 *Salio la Akaunti ya Soko Safi*\n\n"
                f"• Mwenye Akaunti: {name}\n"
                f"• Salio la Kreti za Akiba: *Siku {current_wallet_balance} ya Kreti Bure*\n\n"
                f"Sanya taka zaidi sokoni ili kuongeza salio lako wakati wowote! Andika 'Menu' kurudi."
            )
            msg.body(balance_text)
            
        # Option B: Run calculation logic and compound historical balance data
        elif "2" in incoming_msg:
            session["step"] = "awaiting_waste_calc"
            msg.body(
                f"♻️ *Waste Calculator Interface*\n\n"
                f"Circular Rate: *30 KG Waste = 1 Full Crate Day Code*\n"
                f"Your historical unused wallet savings: *{current_wallet_balance} Credits*\n\n"
                f"Please input the weight of organic waste (KG) dropped off today:"
                if lang == "en" else
                f"♻️ *Kikokotoo Kipya cha Taka*\n\n"
                f"Kipimo: *Kilo 30 za taka = Siku 1 ya Kreti Bure*\n"
                f"Salio lako la sasa ambalo halijatumiwa: *Mikopo {current_wallet_balance}*\n\n"
                f"Tafadhali andika uzito wa taka (KG) ulizokusanya leo:"
            )
        else:
            msg.body("Invalid input path choice. Select 1 or 2:" if lang == "en" else "Chaguo batili. Tafadhali chagua nambari 1 au 2:")
        return str(resp)

    if step == "awaiting_waste_calc":
        try:
            waste_kg = float(''.join(c for c in incoming_msg if c.isdigit() or c=='.'))
            new_credits_earned = round(waste_kg / 30.0, 1)
            
            # Extract and update cumulative compound values
            historical_credits = session.get("wallet_credits", 0.0)
            compounded_net_total = round(historical_credits + new_credits_earned, 1)
            
            # Commit newly generated compound total straight into our local persistent system models
            session["wallet_credits"] = compounded_net_total
            if sender in persistent_users:
                persistent_users[sender]["wallet_credits"] = compounded_net_total
                
            calc_response = (
                f"📊 *Waste Ledger Aggregation Results*\n\n"
                f"• Fresh Bio-Waste Received: {waste_kg} KG\n"
                f"• New Value Generated: +{new_credits_earned} Credits\n"
                f"• Unused Rollover Savings: {historical_credits} Credits\n"
                f"• *Total Cumulative Wallet Balance: {compounded_net_total} Crate Storage Days*\n\n"
                f"Bring this scrap waste directly to our conversion bio-bins to confirm ledger deposit. 🤝 Thank you for choosing Soko Safi AI! Type 'Menu' to continue."
                if lang == "en" else
                f"📊 *Matokeo ya Mahesabu ya Taka*\n\n"
                f"• Taka Mpya Zilizopokelewa: {waste_kg} KG\n"
                f"• Mikopo Mipya Iliyozalishwa: +{new_credits_earned}\n"
                f"• Salio lako la Kale: {historical_credits}\n"
                f"• *Jumla Kuu ya Mikopo Kwenye Wallet: Mikopo {compounded_net_total} (Siku za Hifadhi)*\n\n"
                f"Leta taka hizi kwenye mapipa yetu ili kuidhinisha salio lako jipya. 🤝 Asante kwa kuchagua Soko Safi AI! Andika 'Menu' kuendelea."
            )
            msg.body(calc_response)
            session["step"] = "main_menu"
        except ValueError:
            msg.body("Please enter a valid numeric value for waste calculation (e.g. 45):" if lang == "en" else "Tafadhali weka nambari halali ya kilo pekee (kero: 45):")
        return str(resp)

    # General system fallback handling safely looping inputs back home
    msg.body(menu_en if lang == "en" else menu_sw)
    return str(resp)

if __name__ == "__main__":
    app.run()
