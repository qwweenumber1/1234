import os
import shutil
import zipfile
from datetime import datetime
import glob

# Configuration
BACKUP_DIR = "backups"
DIRS_TO_BACKUP = ["uploads", "uploaded_files"]
DB_FILES_PATTERN = "data/*.db"
MAX_BACKUPS = 7

def create_backup():
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    print(f"Starting backup: {backup_filename}...")

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Backup Databases
            db_files = glob.glob(DB_FILES_PATTERN)
            for db_file in db_files:
                if os.path.isfile(db_file):
                    zipf.write(db_file, db_file)
                    print(f"  Added database: {db_file}")

            # 2. Backup Upload Folders
            for folder in DIRS_TO_BACKUP:
                if os.path.exists(folder):
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                    print(f"  Added folder: {folder}")
                else:
                    print(f"  Warning: Folder {folder} not found, skipping.")

        print(f"Backup successfully created: {backup_path}")
        return True
    except Exception as e:
        print(f"Error during backup: {str(e)}")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return False

def cleanup_old_backups():
    print("Checking for old backups...")
    backups = glob.glob(os.path.join(BACKUP_DIR, "backup_*.zip"))
    backups.sort(key=os.path.getmtime, reverse=True)

    if len(backups) > MAX_BACKUPS:
        to_delete = backups[MAX_BACKUPS:]
        for backup in to_delete:
            try:
                os.remove(backup)
                print(f"  Deleted old backup: {backup}")
            except Exception as e:
                print(f"  Error deleting {backup}: {str(e)}")
    else:
        print("  No old backups to delete.")

if __name__ == "__main__":
    if create_backup():
        cleanup_old_backups()
    print("Done.")
