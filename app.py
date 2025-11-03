from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import datetime
import os
import shutil

from utils import auto_backup

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# 🔹 Učitaj .env datoteku
load_dotenv()

# 🔹 Osnovni direktorij projekta
basedir = os.path.abspath(os.path.dirname(__file__))

# 🔹 Konfiguracija baze podataka
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'versus.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 🔹 Inicijalizacija baze
db = SQLAlchemy(app)

# 🔹 Automatsko kreiranje baze ako ne postoji
if not os.path.exists(os.path.join(basedir, 'versus.db')):
    with app.app_context():
        db.create_all()
        print("✅ Kreirana nova baza podataka (versus.db)")

# 🔹 E-mail konfiguracija
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == "True"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)

# 🔹 Modeli
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(100), nullable=False)
    opis = db.Column(db.String(255), nullable=True)
    cijena = db.Column(db.Float, nullable=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    poruka = db.Column(db.String(500), nullable=False)

# 🔹 Početna stranica
@app.route("/")
def index():
    return render_template("index.html")

# 🔹 Model za tečajeve
class Course(db.Model):
    __tablename__ = 'course'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(100), nullable=False)
    opis = db.Column(db.Text, nullable=True)
    cijena = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Course {self.naziv}>"

# 🔹 Dodavanje novog tečaja
@app.route("/add_course", methods=["GET", "POST"])
def add_course():
    if not session.get("admin_logged"):
        flash("⛔ Pristup dozvoljen samo administratoru.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        naziv = request.form["naziv"]
        opis = request.form["opis"]
        cijena = request.form["cijena"]

        try:
            # ➕ Kreiraj novi tečaj
            novi_tecaj = Course(naziv=naziv, opis=opis, cijena=float(cijena))
            db.session.add(novi_tecaj)

            # ✅ Prvo spremi u bazu
            db.session.commit()

            # 💾 Tek sad napravi backup jer je baza ažurirana
            from auto_backup import backup_database
            backup_database()

            flash("✅ Tečaj je uspješno dodan i backup je napravljen!", "success")
            return redirect(url_for("courses"))

        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Greška pri dodavanju tečaja: {e}", "danger")
            return redirect(url_for("add_course"))

    return render_template("add_course.html")

# Uredi tečaj
@app.route("/edit_course/<int:id>", methods=["GET", "POST"])
def edit_course(id):
    if not session.get("admin_logged"):
        flash("⛔ Pristup dozvoljen samo administratoru.", "danger")
        return redirect(url_for("admin_login"))
    course = Course.query.get_or_404(id)

    if request.method == "POST":
        course.naziv = request.form["naziv"]
        course.opis = request.form["opis"]
        course.cijena = float(request.form["cijena"])

        try:
            db.session.commit()
            flash("✅ Tečaj je uspješno ažuriran!", "success")
            return redirect(url_for("courses"))
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Greška prilikom ažuriranja: {e}", "danger")

    return render_template("edit_course.html", course=course)

# Brisanje tečaja
@app.route("/delete_course/<int:id>", methods=["POST"])
def delete_course(id):
    if not session.get("admin_logged"):
        flash("⛔ Pristup dozvoljen samo administratoru.", "danger")
        return redirect(url_for("admin_login"))
    course = Course.query.get_or_404(id)
    try:
        db.session.delete(course)
        db.session.commit()
        flash("❌ Tečaj je uspješno obrisan.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Greška pri brisanju tečaja: {e}", "danger")

    return redirect(url_for("courses"))

# 🔹 Prikaz svih tečajeva
@app.route("/courses")
def courses():
    svi_kursevi = Course.query.all()
    return render_template("courses.html", courses=svi_kursevi)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(150), nullable=False)
    opis = db.Column(db.Text, nullable=True)

# 🔹 Pregled svih događaja
@app.route("/events")
def events():
    svi_dogadjaji = Event.query.all()
    return render_template("events.html", events=svi_dogadjaji)
    

# 🔹 Dodavanje događaja (samo admin)
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if not session.get("admin_logged"):
        flash("Pristup dopušten samo administratoru.", "warning")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        naziv = request.form["naziv"]
        opis = request.form["opis"]

        try:
            novi = Event(naziv=naziv, opis=opis)
            db.session.add(novi)
            db.session.commit()
            flash("✅ Događaj je uspješno dodan!", "success")
            return redirect(url_for("events"))
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Greška pri dodavanju događaja: {e}", "danger")

    return render_template("add_event.html")

# 🔹 Uredi događaj (samo admin)
@app.route("/edit_event/<int:id>", methods=["GET", "POST"])
def edit_event(id):
    if not session.get("admin_logged"):
        flash("Pristup dopušten samo administratoru.", "warning")
        return redirect(url_for("admin_login"))

    event = Event.query.get_or_404(id)

    if request.method == "POST":
        event.naziv = request.form["naziv"]
        event.opis = request.form["opis"]

        try:
            db.session.commit()
            flash("✅ Događaj je uspješno ažuriran!", "success")
            return redirect(url_for("events"))
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Greška pri ažuriranju događaja: {e}", "danger")

    return render_template("edit_event.html", event=event)

# 🔹 Prijava na događaj
@app.route("/register_event/<int:event_id>", methods=["GET", "POST"])
def register_event(event_id):
    events = {
        1: "Python Osnove",
        2: "Web razvoj Flask"
    }
    event_naziv = events.get(event_id, "Nepoznat događaj")

    if request.method == "POST":
        ime = request.form["ime"]
        email = request.form["email"]
        poruka = request.form.get("poruka", "")

        try:
            nova_prijava = EventRegistration(
                ime=ime,
                email=email,
                event_naziv=event_naziv,
                poruka=poruka
            )
            db.session.add(nova_prijava)
            db.session.commit()

            # 📬 Pošalji potvrdu e-mailom
            msg = Message(
                subject=f"Potvrda prijave za {event_naziv}",
                recipients=[email],
                body=f"Hvala {ime}, uspješno ste se prijavili na događaj '{event_naziv}'."
            )
            mail.send(msg)

            flash("✅ Uspješno ste se prijavili! Potvrda je poslana e-mailom.", "success")
            return redirect(url_for("events"))
        except Exception as e:
            db.session.rollback()
            flash(f"⚠️ Greška pri prijavi: {e}", "danger")

    return render_template("register_event.html", event_naziv=event_naziv)

# 🔹 Kontakt forma
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        ime = request.form["ime"]
        email = request.form["email"]
        poruka = request.form["poruka"]

        nova_poruka = Contact(ime=ime, email=email, poruka=poruka)
        db.session.add(nova_poruka)
        db.session.commit()

        # Slanje e-mail obavijesti
        try:
            msg = Message(
                subject=f"Nova poruka od {ime}",
                recipients=[os.getenv("MAIL_NOTIFY_TO")],
                body=f"Ime: {ime}\nEmail: {email}\n\nPoruka:\n{poruka}"
            )
            mail.send(msg)
        except Exception as e:
            print("⚠️ Slanje e-maila nije uspjelo:", e)

        return render_template("thank_you.html", ime=ime)
    return render_template("contact.html")

# 🔹 Login za korisnike
@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "12345":
            session["logged_in"] = True
            flash("Uspješna prijava!", "success")
            return redirect(url_for("user_messages"))
        else:
            flash("Pogrešno korisničko ime ili lozinka!", "danger")

    return render_template("user_login.html")

# USER: Pregled vlastitih poruka (za obične korisnike)
@app.route("/user/messages")
def user_messages():
    if not session.get("logged_in"):
        flash("Prijavi se za pristup svojim porukama.", "warning")
        return redirect(url_for("user_login"))
    
    sve_poruke = Contact.query.all()
    return render_template("messages.html", poruke=sve_poruke)

# 🔹 Admin login
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # provjera kredencijala iz .env fajla
        if (
            username == os.getenv("ADMIN_USERNAME")
            and password == os.getenv("ADMIN_PASSWORD")
        ):
            session["admin_logged"] = True
            flash("Dobrodošao nazad, admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Neispravni podaci za prijavu.", "danger")
            return render_template("login.html")

    # prikaz forme kad se otvori stranica
    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged", None)
    flash("Uspješno ste se odjavili.", "info")
    return redirect(url_for("admin_login"))

@app.route("/test")
def test():
    return "Radi ✅"

@app.route("/snaga_uma")
def snaga_uma():
    return render_template("snaga_uma.html")

@app.route("/kontakt_snaga_uma", methods=["POST"])
def kontakt_snaga_uma():
    try:
        ime = request.form["ime"]
        email = request.form["email"]
        poruka = request.form["poruka"]

        # 📩 Poruka ide njoj
        msg_to_admin = Message(
            subject=f"Nova poruka za Snaga Uma - {ime}",
            sender=email,
            recipients=["snaguma17@gmail.com"],
            body=f"Ime: {ime}\nE-mail: {email}\n\nPoruka:\n{poruka}"
        )
        mail.send(msg_to_admin)

        # 📤 Auto-odgovor pošiljatelju
        auto_reply = Message(
            subject="Hvala na kontaktu - Snaga Uma",
            sender="snaguma17@gmail.com",
            recipients=[email],
            body=f"""
Poštovani {ime},

Hvala vam što ste nas kontaktirali! 🌿 
Vaša poruka je primljena i tim Snaga Uma će vam se javiti u najkraćem mogućem roku.

Lijep pozdrav,  
Snaga Uma – Partnersko savjetovanje
"""
        )
        mail.send(auto_reply)

        flash("✅ Poruka je uspješno poslana! Primiti ćete potvrdu putem e-maila.", "success")
    except Exception as e:
        flash(f"⚠️ Greška pri slanju poruke: {e}", "danger")

    return redirect(url_for("snaga_uma"))

# 🔹 Admin dashboard (jedina verzija!)
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged"):
        flash("⛔ Prijavi se kao admin da pristupiš upravljačkoj ploči.", "warning")
        return redirect(url_for("admin_login"))

    broj_kurseva = Course.query.count()
    broj_poruka = Contact.query.count()
    broj_dogadjaja = Event.query.count()

    # provjera posljednjeg backup fajla
    backup_dir = "backup"
    zadnji_backup = "Nema dostupnih kopija."
    if os.path.exists(backup_dir):
        fajlovi = sorted(os.listdir(backup_dir), reverse=True)
        if fajlovi:
            zadnji_backup = fajlovi[0]

    return render_template(
        "admin_dashboard.html",
        broj_kurseva=broj_kurseva,
        broj_poruka=broj_poruka,
        broj_dogadjaja=broj_dogadjaja,
        zadnji_backup=zadnji_backup
    )

# 🔹 Pregled poruka (za admina)    
@app.route("/messages")
def messages():
    if not session.get("admin_logged"):
        flash("Prijavi se kao admin za pristup porukama.", "warning")
        return redirect(url_for("admin_login"))

    sve_poruke = Contact.query.all()
    return render_template("messages.html", poruke=sve_poruke)

# 🔹 Backup funkcija
from utils import auto_backup

# 🔹 Odjava (za oba tipa korisnika)
@app.route("/logout")
def logout():
    session.clear()
    flash("Odjavljen si!", "info")
    return redirect(url_for("index"))

# 🔹 Provjera autorizacije
@app.before_request
def require_login():
    # Ako URL počinje s "/admin" ali NIJE login stranica
    if request.path.startswith("/admin") and not request.path.startswith("/admin/login"):
        if not session.get("admin_logged"):
            return redirect(url_for("admin_login"))
    
    # Ako su ovo "user-only" rute
    if request.path.startswith("/user") and not request.path.startswith("/user/login"):
        if not session.get("logged_in"):
            return redirect(url_for("user_login"))
        
# 📅 Model za prijave na događaje
class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    event_naziv = db.Column(db.String(150), nullable=False)
    poruka = db.Column(db.Text)
    datum_prijave = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prijava {self.ime} za {self.event_naziv}>"
    
# 🔹 Brisanje događaja
@app.route("/delete_event/<int:id>", methods=["POST"])
def delete_event(id):
    if not session.get("admin_logged"):
        flash("❌ Pristup odbijen! Samo admin može brisati događaje.", "danger")
        return redirect(url_for("events"))

    try:
        event = Event.query.get_or_404(id)
        db.session.delete(event)
        db.session.commit()
        flash("✅ Događaj uspješno obrisan!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"⚠️ Greška pri brisanju događaja: {e}", "danger")

    return redirect(url_for("events"))

# 🔹 Pokretanje aplikacije
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("🔥 Flask server pokrenut – sve rute aktivne.")
    app.run(debug=True)
