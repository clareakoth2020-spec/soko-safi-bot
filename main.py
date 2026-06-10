from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# In-memory session tracking for the live MVP demo
user_sessions = {}

@app.route("/main", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From")
    resp = MessagingResponse()
    msg = resp.message()

    # 1. INITIAL ONBOARDING CHECK
    if sender not in user_sessions:
        user_sessions[sender] = {"step": "lang"}
        msg.body("🌟 Karibu Soko Safi AI! \n\nPlease choose your language / Tafadhali chagua lugha:\n\n1. English\n2. Kiswahili")
        return str(resp)

    session = user_sessions[sender]
    step = session.get("step")
    lang = session.get("lang", "en")

    # 2. ONBOARDING STEP: LANGUAGE
    if step == "lang":
        session["lang"] = "en" if "1" in incoming_msg else "sw"
        session["step"] = "name"
        msg.body("Great! What is your name?" if session["lang"] == "en" else "Sawa! Unaitwa nani?")
        return str(resp)

    # 3. ONBOARDING STEP: NAME
    if step == "name":
        session["name"] = incoming_msg
        session["step"] = "gender"
        msg.body("Are you Male or Female?\n1. Female\n2. Male" if session["lang"] == "en" else "Wewe ni Mwanamke au Mwanamume?\n1. Mwanamke\n2. Mwanamume")
        return str(resp)

    # 4. ONBOARDING STEP: GENDER
    if step == "gender":
        session["gender"] = "Female" if "1" in incoming_msg else "Male"
        session["step"] = "main_menu"
        name = session.get("name", "Trader")
        
        welcome_text = (
            f"🎉 Welcome {name}! You are now successfully registered with Soko Safi AI.\n\n"
            f"We track demographic impact to support small-scale entrepreneurs. Send 'Menu' anytime to access our services."
            if session["lang"] == "en" else
            f"🎉 Karibu {name}! Umesajiliwa kikamilifu na Soko Safi AI.\n\n"
            f"Tunasajili jinsia ili kusaidia wafanyabiashara wadogo. Tuma 'Menu' wakati wowote kupata huduma."
        )
        msg.body(welcome_text)
        return str(resp)

    # --- MAIN SYSTEM OPERATIONS ---
    name = session.get("name", "Trader")
    
    menu_en = f"📋 *Soko Safi Main Menu* (Hi {name})\n\n1. ❄️ Book Cold Storage\n2. ♻️ Waste-to-Credit Calculator\n3. 🌱 Buy Bio-Slurry Fertilizer\n4. 💡 Smart Market Tips\n\nReply with a number (1-4) or type 'Menu' to return here."
    menu_sw = f"📋 *Orodha Kuu ya Soko Safi* (Habari {name})\n\n1. ❄️ Weka Akiba ya Baridi\n2. ♻️ Kikokotoo cha Taka kuwa Mikopo\n3. 🌱 Nunua Mbolea ya Bio-Slurry\n4. 💡 Vidokezo vya Soko\n\nJibu kwa nambari (1-4) au uandike 'Menu' kurudi hapa."

    # Route if user wants to see the menu or resets
    if incoming_msg.lower() in ["menu", "habari", "hi", "m"]:
        session["step"] = "main_menu"
        msg.body(menu_en if lang == "en" else menu_sw)
        return str(resp)

    # SUB-ROUTING HANDLING
    if step == "main_menu":
        if "1" in incoming_msg:
            msg.body("❄️ *Cold Storage Booking*\n\nPlease reply with the number of crates and crop type you want to store today (e.g., '2 crates of tomatoes')." if lang == "en" else "❄️ *Akiba ya Baridi*\n\nTafadhali jibu na idadi ya makreti na aina ya mazao unayotaka kuhifadhi leo (kero: 'makreti 2 ya nyanya').")
            session["step"] = "awaiting_booking"
        
        elif "2" in incoming_msg:
            msg.body("♻️ *Waste-to-Credit Calculator*\n\nOur circular rate is *30 KG of organic waste = 1 Day Free Storage Crate Credit*.\n\nPlease type the total kilograms (KG) of market waste you have collected today (numbers only, e.g., '60'):" if lang == "en" else "♻️ *Kikokotoo cha Taka kuwa Mikopo*\n\nKipimo chetu ni *Kilo 30 za taka = Siku 1 ya Kreti Bure ya Storage*.\n\nTafadhali andika jumla ya kilo (KG) za taka ulizokusanya leo (nambari pekee, kero: '60'):")
            session["step"] = "awaiting_waste_calc"
        
        elif "3" in incoming_msg:
            msg.body("🌱 *Bio-Slurry Organic Fertilizer*\n\nOur nutrient-rich fertilizer processed from market waste is available at KES 50 per bag at our collection point. Reply with the number of bags you want to reserve." if lang == "en" else "🌱 *Mbolea ya Bio-Slurry*\n\nMbolea yetu inayotokana na taka za sokoni inapatikana kwa KES 50 kwa kila mfuko kwenye kituo chetu. Jibu na idadi ya mifuko unayotaka kuweka akiba.")
            session["step"] = "awaiting_fertilizer"
        
        elif "4" in incoming_msg:
            msg.body("💡 *Smart Market Tip*\n\nTo preserve leafy greens before placing them in our cold hubs, keep them on moist shaded mats. This preserves cellular structure and minimizes water weight loss!" if lang == "en" else "💡 *Vidokezo vya Soko*\n\nKuhifadhi mboga za majani kabla ya kuzileta kwenye vituo vyetu, ziweke kwenye mikeka yenye unyevu chini ya kivuli. Hii inalinda majani yasinyauke!")
        else:
            msg.body(menu_en if lang == "en" else menu_sw)
        return str(resp)

    # AUTOMATED WASTE-TO-CREDIT CALCULATOR BRAIN
    if step == "awaiting_waste_calc":
        try:
            # Extract numeric values from user input
            waste_kg = float(''.join(c for c in incoming_msg if c.isdigit() or c=='.'))
            credits_earned = round(waste_kg / 30.0, 1)
            
            if lang == "en":
                calc_response = (
                    f"📊 *Calculation Result*\n\n"
                    f"• Organic Waste: {waste_kg} KG\n"
                    f"• Value Generated: *{credits_earned} Free Storage Day(s)*\n\n"
                    f"Bring this waste to our market processing bin to credit your Soko Safi digital account! Type 'Menu' to go back."
                )
            else:
                calc_response = (
                    f"📊 *Matokeo ya Kikokotoo*\n\n"
                    f"• Taka Zilizokusanywa: {waste_kg} KG\n"
                    f"• Thamani ya Mikopo: *Siku {credits_earned} ya Kreti Bure*\n\n"
                    f"Leta taka hizi kwenye pipa letu sokoni ili kuweka mikopo hii kwenye akaunti yako ya kidijitali! Andika 'Menu' kurudi."
                )
            msg.body(calc_response)
            session["step"] = "main_menu"
        except ValueError:
            msg.body("Please enter a valid number for weight (e.g., 45)." if lang == "en" else "Tafadhali weka nambari halali ya kilo (kero: 45).")
        return str(resp)

    # GENERAL FALLBACK HANDLING
    if "booking" in step or "fertilizer" in step:
        msg.body("Order acknowledged! Our market representative will confirm via SMS shortly. Type 'Menu' to restart." if lang == "en" else "Ombi lako limepokelewa! Mwakilishi wetu atathibitisha kwa SMS punde si punde. Andika 'Menu' kuanza tena.")
        session["step"] = "main_menu"
        return str(resp)

    msg.body(menu_en if lang == "en" else menu_sw)
    return str(resp)

if __name__ == "__main__":
    app.run()
