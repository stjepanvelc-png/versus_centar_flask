from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import datetime
import os
import shutil

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

# 🔹 Prikaz svih tečajeva
@app.route("/courses")
def courses():
    svi_kursevi = Course.query.all()
    return render_template("courses.html", courses=svi_kursevi)

# 🔹 Dodavanje novog tečaja
@app.route("/add_course", methods=["GET", "POST"])
def add_course():
    if request.method == "POST":
        naziv = request.form["naziv"]
        opis = request.form["opis"]
        cijena = float(request.form["cijena"])
        novi = Course(naziv=naziv, opis=opis, cijena=cijena)
        db.session.add(novi)
        db.session.commit()
        flash("Tečaj uspješno dodan!", "success")
        return redirect(url_for("courses"))
    return render_template("add_course.html")

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

# 🔹 Admin dashboard (jedina verzija!)
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged"):
        return redirect(url_for("admin_login"))

    broj_kurseva = Course.query.count()
    broj_poruka = Contact.query.count()

    backup_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "backups")
    zadnji_backup = None
    if os.path.exists(backup_dir):
        backup_fajlovi = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith(".db")],
            key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
            reverse=True
        )
        if backup_fajlovi:
            zadnji_backup = datetime.fromtimestamp(
                os.path.getmtime(os.path.join(backup_dir, backup_fajlovi[0]))
            ).strftime("%d.%m.%Y %H:%M")

    return render_template(
        "admin_dashboard.html",
        broj_kurseva=broj_kurseva,
        broj_poruka=broj_poruka,
        zadnji_backup=zadnji_backup
    )
    
@app.route("/messages")
def messages():
    if not session.get("admin_logged"):
        flash("Prijavi se kao admin za pristup porukama.", "warning")
        return redirect(url_for("admin_login"))

    sve_poruke = Contact.query.all()
    return render_template("messages.html", poruke=sve_poruke)

# 🔹 Backup funkcija
@app.route("/admin/backup", methods=["POST"])
def admin_backup():
    if not session.get("admin_logged"):
        return redirect(url_for("admin_login"))

    try:
        from auto_backup import backup_database
        backup_database()
        flash("✅ Backup baze je uspješno napravljen i pohranjen!", "success")
    except Exception as e:
        flash(f"⚠️ Greška pri izradi backupa: {e}", "danger")

    return redirect(url_for("admin_dashboard"))

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

# 🔹 Pokretanje aplikacije
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("🔥 Flask server pokrenut – sve rute aktivne.")
    app.run(debug=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)