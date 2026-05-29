from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# This stores user data temporarily while the app is running
user_data = {} 

@app.route("/main", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").lower().strip()
    sender = request.values.get("From")
    resp = MessagingResponse()
    msg = resp.message()

    # If we don't know this person yet
    if sender not in user_data:
        if "name" not in user_data.get(sender, {}):
            if "language" not in user_data.get(sender, {}):
                msg.body("Habari! Karibu Soko Safi. Chagua lugha:\n1. English\n2. Kiswahili")
                user_data[sender] = {"step": "lang"}
                return str(resp)
            
            # Save Language and ask for Name
            user_data[sender]["lang"] = "English" if "1" in incoming_msg else "Kiswahili"
            user_data[sender]["step"] = "name"
            msg.body("Great! What is your name?" if user_data[sender]["lang"] == "English" else "Sawa! Unaitwa nani?")
            return str(resp)

        # Save Name and ask Gender
        user_data[sender]["name"] = incoming_msg
        user_data[sender]["step"] = "gender"
        msg.body("Are you Male or Female?" if user_data[sender]["lang"] == "English" else "Wewe ni Mwanamume au Mwanamke?")
        return str(resp)

    # Main Menu for registered users
    name = user_data[sender].get("name", "Trader")
    menu = f"Habari {name}! Welcome to Soko Safi. How can we help?\n\n1. ❄️ Cold Storage\n2. ♻️ Waste-to-Credit\n3. 🌱 Buy Fertilizer\n4. 💡 Market Tips\n5. 📞 Help / Location"
    
    if "1" in incoming_msg:
        msg.body("Cold storage booked! Please drop your produce at our Ahero Hub by 10 AM.")
    elif "2" in incoming_msg:
        msg.body("Exchange waste for credits! 30kg of waste = 1 crate storage. How many KGs are you bringing?")
    elif "3" in incoming_msg:
        msg.body("Our organic fertilizer is available for KES 50 per bag. Reply 'ORDER' to book.")
    elif "4" in incoming_msg:
        msg.body("Market Tip: Keep tomatoes in the shade to stop them from softening too fast!")
    elif "5" in incoming_msg:
        msg.body("Call us at 0700-000-000 or visit us at Ahero Market, near the main gate.")
    else:
        msg.body(menu)

    return str(resp)

if __name__ == "__main__":
    app.run()
