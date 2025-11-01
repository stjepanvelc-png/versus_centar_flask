from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# KONFIGURACIJA MAIL SERVERA
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "versus.centar@gmail.com"  # zamijeni svojim Gmailom
app.config["MAIL_PASSWORD"] = "vjfr bqib wbme dzlt"    # 16-znamenkasta app lozinka
app.config["MAIL_DEFAULT_SENDER"] = ("Versus Centar", "versus.centar@gmail.com")

mail = Mail(app)

# TESTNI EMAIL
with app.app_context():
    msg = Message(
        subject="Test Flask Mail",
        recipients=["stjepan.velc@gmail.com"],  # možeš poslati sam sebi
        body="Ovo je testni e-mail poslan iz Flask aplikacije."
    )
    mail.send(msg)
    print("✅ Testni e-mail je uspješno poslan!")
