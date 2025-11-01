import os
import time
import shutil
from datetime import datetime

# putanja do baze i direktorija za backup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "versus.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

# kreiraj folder ako ne postoji
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_database():
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = os.path.join(BACKUP_DIR, f"versus_backup_{timestamp}.db")
        shutil.copy2(DB_PATH, backup_file)
        print(f"💾 Backup napravljen: {backup_file}")

        # zadrži samo zadnjih 5 backup fajlova
        backups = sorted(os.listdir(BACKUP_DIR))
        if len(backups) > 5:
            for old in backups[:-5]:
                os.remove(os.path.join(BACKUP_DIR, old))
                print(f"🧹 Obrisana stara kopija: {old}")
    else:
        print("⚠️ Baza nije pronađena!")

def auto_backup_loop():
    while True:
        backup_database()
        print("⏳ Sljedeći backup za 6 sati...\n")
        time.sleep(6 * 60 * 60)  # 6 sati u sekundama

if __name__ == "__main__":
    print("🚀 Pokrenut automatski backup sustav")
    auto_backup_loop()
