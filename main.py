from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# This dictionary stores our users' progress and data in memory while the server runs
user_sessions = {}

@app.route("/main", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From")
    
    resp = MessagingResponse()
    msg = resp.message()

    # 1. NEW USER REGISTRATION FLOW
    if sender not in user_sessions:
        user_sessions[sender] = {"step": "ask_lang"}
        msg.body("Habari! Karibu Soko Safi AI. Let's get started. Please choose your language:\n\n1. English\n2. Kiswahili")
        return str(resp)

    current_session = user_sessions[sender]
    current_step = current_session.get("step")

    # Step A: Capture Language Choice
    if current_step == "ask_lang":
        if "1" in incoming_msg:
            current_session["lang"] = "en"
            current_session["step"] = "ask_name"
            msg.body("Awesome! What is your name? (Just type your name)")
        elif "2" in incoming_msg or "kiswahili" in incoming_msg.lower():
            current_session["lang"] = "sw"
            current_session["step"] = "ask_name"
            msg.body("Sawa kabisa! Unaitwa nani? (Andika jina lako tu)")
        else:
            msg.body("Please reply with 1 for English or 2 for Kiswahili.\n\nTafadhali jibu na 1 kwa Kiingereza au 2 kwa Kiswahili.")
        return str(resp)

    # Step B: Capture Name
    if current_step == "ask_name":
        current_session["name"] = incoming_msg
        current_session["step"] = "ask_gender"
        
        if current_session["lang"] == "en":
            msg.body(f"Thank you, {incoming_msg}! To help us understand our market impact, are you Male or Female?\n\n1. Female\n2. Male")
        else:
            msg.body(f"Asante, {incoming_msg}! Ili kutusaidia kujua jinsi tunavyosaidia soko letu, wewe ni Mwanamke au Mwanamume?\n\n1. Mwanamke\n2. Mwanamume")
        return str(resp)

    # Step C: Capture Gender & Onboard to Main Menu
    if current_step == "ask_gender":
        if "1" in incoming_msg:
            current_session["gender"] = "Female"
        elif "2" in incoming_msg:
            current_session["gender"] = "Male"
        else:
            current_session["gender"] = incoming_msg # Fallback if they type it out
            
        current_session["step"] = "main_menu"
        # Fall through to show the main menu immediately after registering

    # 2. MAIN MENU LOGIC (FOR REGISTERED USERS)
    name = current_session.get("name", "Trader")
    lang = current_session.get("lang", "en")

    # Define vertical menus
    english_menu = (
        f"Habari {name}! Welcome back to Soko Safi AI. How can we help you today?\n\n"
        "1. ❄️ Book Cold Storage\n"
        "2. ♻️ Turn Waste to Credits\n"
        "3. 🌱 Buy Organic Fertilizer\n"
        "4. 💡 Get Free Market Tips\n"
        "5. 📞 Help / Our Location\n\n"
        "Reply with a number (1-5) or type 'Menu' anytime."
    )

    kiswahili_menu = (
        f"Habari {name}! Karibu tena Soko Safi AI. Tutakusaidia vipi leo?\n\n"
        "1. ❄️ Weka Akiba ya Baridi (Storage)\n"
        "2. ♻️ Badilisha Taka kuwa Mikopo (Credits)\n"
        "3. 🌱 Nunua Mbolea ya Kikaboni\n"
        "4. 💡 Pata Vidokezo vya Soko\n"
        "5. 📞 Msaada / Mahali Tulipo\n\n"
        "Jibu na namba (1-5) au andika 'Menu' wakati wowote."
    )

    clean_input = incoming_msg.lower().strip()

    # Reset back to menu if they type "menu" or "habari"
    if clean_input in ["menu", "habari", "hi", "hello"]:
        msg.body(english_menu if lang == "en" else kiswahili_menu)
        return str(resp)

    # Handle Menu Choices
    if "1" in clean_input:
        if lang == "en":
            msg.body("Great choice! Our clean, cold rooms will stop your produce from rotting in the heat. Please type the type of produce and how many crates you want to store (e.g., '2 crates of tomatoes').")
        else:
            msg.body("Uamuzi mzuri! Vyumba vyetu vya baridi vitazuia bidhaa zako zisioze kwa joto. Tafadhali andika aina ya bidhaa na idadi ya makreti unayotaka kuweka (kwa mfano, 'makreti 2 ya nyanya').")
            
    elif "2" in clean_input:
        if lang == "en":
            msg.body("Let's turn waste into wealth! ♻️\n\nRemember: 30kg of organic waste pays for 1 crate of cold storage for a whole day. How many KGs of waste are you bringing to the hub today?")
        else:
            msg.body("Wacha tugeuze taka kuwa pesa! ♻️\n\nKumbuka: Kilo 30 za taka za sokoni zinalipia kreti 1 ya akiba ya baridi kwa siku nzima. Je, unaleta kilo ngapi za taka leo?")
            
    elif "3" in clean_input:
        if lang == "en":
            msg.body("Our high-quality organic bio-slurry fertilizer keeps your soil rich and healthy with no toxic chemicals. A bag goes for KES 50. Type 'ORDER' to book yours.")
        else:
            msg.body("Mbolea yetu ya kikaboni ya bio-slurry inafanya udongo wako kuwa na rutuba bila kemikali zenye sumu. Mfuko mmoja ni KES 50. Andika 'ORDER' ili kuagiza.")
            
    elif "4" in clean_input:
        if lang == "en":
            msg.body("💡 Today's Soko Tip: Keep your leafy greens like Sukuma Wiki or spinach under moist racks or in the shade to prevent quick wilting before bringing them to our cold room!")
        else:
            msg.body("💡 Kidokezo cha Soko leo: Weka mboga zako kama Sukuma Wiki au mchicha mahali penye kivuli au chini ya rafu zenye unyevu ili zisinyae haraka kabla ya kuzileta kwenye chumba chetu cha baridi!")
            
    elif "5" in clean_input:
        if lang == "en":
            msg.body("📍 Find Us: We are located right at the Ahero Market main gate, and inside Kibuye Market near the main drainage line.\n\n📞 Call/WhatsApp our Hub Manager directly at +254 700 000 000 if you need immediate storage help!")
        else:
            msg.body("📍 Mahali Tulipo: Tunapatikana karibu na lango kuu la Soko la Ahero, na ndani ya Soko la Kibuye karibu na mtaro mkuu.\n\n📞 Piga simu au WhatsApp Meneja wetu wa Hub moja kwa moja kwa +254 700 000 000 kama unahitaji msaada sasa hivi!")
            
    else:
        # If they type something random, gently remind them of the menu options
        msg.body(english_menu if lang == "en" else kiswahili_menu)

    return str(resp)

if __name__ == "__main__":
    app.run()
