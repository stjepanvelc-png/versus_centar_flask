# 🔁 Automatski backup baze nakon dodavanja novog tečaja
import shutil
from datetime import datetime
import os

def auto_backup():
    try:
        # Folder za backup
        backup_dir = "backup"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Naziv fajla s vremenom
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"versus_auto_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Kopiraj glavnu bazu
        shutil.copy("versus.db", backup_path)
        print(f"✅ Automatski backup kreiran: {backup_filename}")

    except Exception as e:
        print(f"⚠️ Greška pri automatskom backupu: {e}")
