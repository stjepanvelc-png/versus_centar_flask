from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import shutil
from datetime import datetime

# Učitaj .env varijable
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "privremeni_kljuc")

# Povezivanje baze
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///versus.db"
db = SQLAlchemy(app)

# --- MODELI ---
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(100), nullable=False)
    opis = db.Column(db.Text, nullable=True)
    cijena = db.Column(db.Float, nullable=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(100))
    email = db.Column(db.String(120))
    poruka = db.Column(db.Text)

# --- ADMIN DASHBOARD ---
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged"):
        flash("Prijavi se kao admin za pristup dashboardu.", "warning")
        return redirect(url_for("admin_login"))

    broj_kurseva = Course.query.count()
    broj_poruka = Contact.query.count()

    # Dohvati zadnji backup
    backup_dir = "backup"
    zadnji_backup = "Nema backup fajlova."
    if os.path.exists(backup_dir):
        backup_fajlovi = sorted(os.listdir(backup_dir), reverse=True)
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

# --- BACKUP FUNKCIJA ---
@app.route("/backup_db", methods=["POST"])
def backup_db():
    try:
        # Kreiraj folder ako ne postoji
        if not os.path.exists("backup"):
            os.makedirs("backup")

        # Generiši timestamp ime fajla
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"versus_backup_{timestamp}.db"
        backup_path = os.path.join("backup", backup_filename)

        # Kopiraj bazu
        shutil.copy("versus.db", backup_path)
        flash(f"✅ Backup baze je uspješno napravljen! ({backup_filename})", "success")

    except Exception as e:
        flash(f"❌ Došlo je do greške prilikom backupa: {str(e)}", "danger")

    return redirect(url_for("admin_dashboard"))
