from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# This handles the main page so you don't see "Not Found"
@app.route("/", methods=["GET"])
def home():
    return "Soko Safi AI is running!"

# This is the secret door Twilio uses
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").lower()
    resp = MessagingResponse()
    msg = resp.message()

    if "1" in incoming_msg:
        msg.body("Confirmed! Cold storage booked. Please keep your Security Tag #SS-999 ready.")
    elif "2" in incoming_msg:
        msg.body("Biodigester waste collection initiated. Our team is on the way!")
    else:
        msg.body("Habari! Welcome to Soko Safi AI. Reply 1 for Cold Storage or 2 for Waste Collection.")
    
    return str(resp)

if __name__ == "__main__":
    app.run()
