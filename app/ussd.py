from flask import Flask, request, make_response

app = Flask(__name__)

# Temporary in-memory session database for tracking registration step
# In production, this would link to your central database
user_sessions = {}

@app.route("/ussd", methods=["POST"])
def ussd_callback():
    # Africa's Talking sends these parameters automatically via HTTP POST
    session_id = request.values.get("sessionId", None)
    phone_number = request.values.get("phoneNumber", None)
    text = request.values.get("text", "")

    # Split the input string to trace user path depth
    input_steps = text.split("*") if text else []
    step_count = len(input_steps)

    response = ""

    # 1. NEW USER REGISTRATION FLOW
    if phone_number not in user_sessions:
        if step_count == 0:
            # Initial Screen: Language Choice
            response = "CON Karibu Soko Safi AI.\nChoose Language:\n1. English\n2. Kiswahili"
        
        elif step_count == 1:
            # User selected language, now ask for name
            lang_choice = input_steps[0]
            user_sessions[phone_number] = {"lang": "en" if lang_choice == "1" else "sw"}
            
            if user_sessions[phone_number]["lang"] == "en":
                response = "CON Welcome! What is your name?"
            else:
                response = "CON Karibu! Unaitwa nani?"
                
        elif step_count == 2:
            # User provided name, now ask for gender
            user_sessions[phone_number]["name"] = input_steps[1]
            lang = user_sessions[phone_number]["lang"]
            
            if lang == "en":
                response = "CON Select Gender:\n1. Female\n2. Male"
            else:
                response = "CON Chagua Jinsia:\n1. Mwanamke\n2. Mwanamume"
                
        elif step_count == 3:
            # Save gender and mark registration complete
            gender_choice = input_steps[2]
            user_sessions[phone_number]["gender"] = "Female" if gender_choice == "1" else "Male"
            user_sessions[phone_number]["registered"] = True
            
            # Immediately show them the main menu path instructions
            lang = user_sessions[phone_number]["lang"]
            if lang == "en":
                response = "END Registration successful! Please redial your shortcode to access the Soko Safi Menu."
            else:
                response = "END Umesajiliwa kikamilifu! Tafadhali piga msimbo tena ili upate Orodha Kuu."

    # 2. MAIN MENU LOGIC (FOR ALREADY REGISTERED TRADERS)
    else:
        lang = user_sessions[phone_number]["lang"]
        name = user_sessions[phone_number]["name"]

        if step_count == 0:
            # Display vertical main menu options
            if lang == "en":
                response = f"CON Habari {name}, select service:\n1. Book Cold Storage\n2. Waste-to-Credit\n3. Buy Fertilizer\n4. Market Tips\n5. Help"
            else:
                response = f"CON Habari {name}, chagua huduma:\n1. Akiba ya Baridi\n2. Taka hadi Mikopo\n3. Nunua Mbolea\n4. Vidokezo vya Soko\n5. Msaada"
        
        elif step_count == 1:
            user_selection = input_steps[0]
            
            # Sub-Menu Option 1: Cold Storage
            if user_selection == "1":
                if lang == "en":
                    response = "END Drop your crates at our market hub before 10 AM to secure space. Soko Safi keeps it fresh!"
                else:
                    response = "END Leta makreti yako kwenye kituo chetu kabla ya saa nne asubuhi. Soko Safi huweka safi!"
            
            # Sub-Menu Option 2: Waste-to-Credit
            elif user_selection == "2":
                if lang == "en":
                    response = "END Rate: 30kg of market waste = 1 crate storage free for a day. Bring your waste to our bin!"
                else:
                    response = "END Kipimo: Kilo 30 za taka za sokoni = kreti 1 bure kwa siku nzima. Leta taka zako sasa!"
            
            # Sub-Menu Option 3: Organic Fertilizer
            elif user_selection == "3":
                if lang == "en":
                    response = "END Nutrient-rich bio-slurry fertilizer is available at KES 50 per bag at our collection point."
                else:
                    response = "END Mbolea ya bio-slurry inapatikana kwa KES 50 kwa kila mfuko kwenye kituo chetu."
            
            # Sub-Menu Option 4: Market Tips
            elif user_selection == "4":
                if lang == "en":
                    response = "END Tip: Keep leafy greens under moist covers or shaded mats to prevent drying before cold storage."
                else:
                    response = "END Kidokezo: Weka mboga mahali penye kivuli au unyevu ili zisinyee kabla ya kuhifadhi."
            
            # Sub-Menu Option 5: Support / Location
            elif user_selection == "5":
                if lang == "en":
                    response = "END Location: Ahero Market Main Gate / Kibuye Market Drainage Line. Phone: 0700000000."
                else:
                    response = "END Mahali: Lango Kuu la Ahero / Mtaro wa Kibuye. Simu: 0700000000."
            
            else:
                if lang == "en":
                    response = "END Invalid option. Please redial."
                else:
                    response = "END Nambari si sahihi. Piga msimbo tena."

    # Return responses formatted cleanly as plain text for carrier telecom systems
    resp = make_response(response, 200)
    resp.headers["Content-Type"] = "text/plain"
    return resp

if __name__ == "__main__":
    app.run()
