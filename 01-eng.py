import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad
from Crypto.Hash import HMAC, SHA1
import gzip
import json
from clc99 import *
import easygui
import configparser
import sys
import shutil
import keyboard

print_good("Welcome to the 99 R.E.P.O Save Archiver!")
print_status("Initializing program...")

running = True
self_dir = os.path.dirname(os.path.abspath(__file__)) + "\\"
last_backup_time = 0  # Prevents duplicate backups within a short time

##### Backup #####

def decrypt_es3(file_path, password="Why would you want to cheat?... :o It's no fun. :') :'D"):
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()

    # Extract the IV (first 16 bytes)
    iv = encrypted_data[:16]
    encrypted_data = encrypted_data[16:]

    # Derive the key using PBKDF2
    key = PBKDF2(password, iv, dkLen=16, count=100, prf=lambda p, s: HMAC.new(p, s, SHA1).digest())

    # Decrypt the data using AES-128-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

    # Check if the data is GZip compressed
    if decrypted_data[:2] == b'\x1f\x8b':  # GZip magic number
        decrypted_data = gzip.decompress(decrypted_data)
    
    return decrypted_data

def GetLevel(FilePath):
    decrypted_data = decrypt_es3(FilePath, "Why would you want to cheat?... :o It's no fun. :') :'D")
    json_data = json.loads(decrypted_data)
    level = json_data['dictionaryOfDictionaries']['value']['runStats']['level']
    return level

def CheckLevelIfChanged(NewLevel):
    return NewLevel != NowLevel

def GiveMe_a_Dir():
    if not os.path.exists(SaverSavePath + "\\" + SavePathDir):
        print_warning("Directory does not exist, creating new folder...")
        os.makedirs(SaverSavePath + "\\" + SavePathDir)

def BackupSave(level):
    global last_backup_time
    current_time = time.time()
    
    # Prevents duplicate backups within 5 seconds
    if current_time - last_backup_time < 5:
        #print_status("Duplicate backup prevented")
        return
    
    if not CheckLevelIfChanged(level):
        print_status("Save file unchanged")
        return
    
    print_status("Backing up Level {}...".format(level))
    GiveMe_a_Dir()
    try:
        backup_path = SaverSavePath + "\\" + SavePathDir + "\\" + SavePathName + ".level{}".format(level)
        shutil.copy(SavePath, backup_path)
        last_backup_time = current_time
    except Exception as e:
        print_error("Failed to back up save: {}".format(e))
        return False
    print_good("Level {} successfully backed up!".format(level))

def WatchSave(filepath):
    global observer, NowLevel, running
    
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File '{filepath}' does not exist")

    class FileModifiedHandler(FileSystemEventHandler):
        def __init__(self):
            self.debounce_timer = None
            
        def on_modified(self, event):
            global NowLevel
            if not event.is_directory and os.path.abspath(event.src_path) == os.path.abspath(filepath):
                # Debounce to prevent multiple triggers
                if self.debounce_timer is not None:
                    return
                
                self.debounce_timer = time.time()
                print_status("Save file {} modified".format(filepath))
                try:
                    level = GetLevel(filepath)
                    BackupSave(level)
                    NowLevel = level  # Update current level
                except Exception as e:
                    print_error("Error processing save modification: {}".format(e))
                finally:
                    time.sleep(1)  # Add brief delay
                    self.debounce_timer = None

    event_handler = FileModifiedHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(filepath), recursive=False)
    observer.start()
    
    def exit_program():
        global running
        print_warning("Detected 'P' key press, exiting program...")
        running = False
        observer.stop()
        observer.join(timeout=2)
        sys.exit(0)
    
    def restore_program():
        global running
        print_warning("Detected 'O' key press, entering restore mode...")
        #running = False
        observer.stop()
        observer.join(timeout=2)
        enter_restore_mode()
    
    keyboard.add_hotkey('p', exit_program)
    keyboard.add_hotkey('o', restore_program)
    
    while running:
        time.sleep(1)

def CheckDirValid(path):
    return os.path.isdir(path)

##### Restore #####
def enter_restore_mode():
    print_status("Entered restore mode")
    print_status("Available backups:")
    
    backup_dir = os.path.join(SaverSavePath, SavePathDir)
    if not os.path.exists(backup_dir):
        print_error("No backup directory found")
        return
    
    backups = []
    for file in os.listdir(backup_dir):
        if file.startswith(SavePathName) and "level" in file:
            level = file.split("level")[-1]
            backups.append((file, level))
    
    if not backups:
        print_error("No backup saves found")
        return
    
    for i, (file, level) in enumerate(backups, 1):
        print_good(f"{i}. Level {level} backup")
    
    while True:
        try:
            choice = input("Enter the number of the backup to restore (or 'q' to quit): ")
            if choice.lower() == 'q':
                print_status("Exiting restore mode")
                return
            
            choice = int(choice)
            if 1 <= choice <= len(backups):
                selected_file = backups[choice-1][0]
                backup_path = os.path.join(backup_dir, selected_file)
                backup_name = os.path.splitext(os.path.join(backup_dir, selected_file))[0]
                backup_name = os.path.basename(backup_name)
                # Restore selected save
                if not os.path.exists(os.path.dirname(SavePath)):
                    print_status("Creating new directory")
                    os.makedirs(os.path.dirname(SavePath))
                shutil.copy(backup_path, os.path.dirname(SavePath) + "\\" + backup_name)
                print_good(f"Successfully restored Level {backups[choice-1][1]} save")
                return
            else:
                print_error("Invalid choice, please try again")
        except ValueError:
            print_error("Please enter a valid number")

# Main program
if __name__ != "__main__":
    sys.exit(1)

config = configparser.ConfigParser()
config.read(self_dir+'config.ini', encoding="utf-8")

SaverSavePath = config.get('Settings', 'SaverSavePath')
if SaverSavePath == "":
    print_error("Backup path not set in config file. Please set a valid backup path in the config file.")
    sys.exit(1)
if not CheckDirValid(SaverSavePath):
    print_error("Invalid backup path in config file. Please check the path.")
    sys.exit(1)

print_status("Please select the save file to monitor")
SavePath = easygui.fileopenbox("Please select the save file to monitor", "Select save file")

if SavePath is None:
    sys.exit(0)

SavePathName = os.path.basename(SavePath)
SavePathDir = os.path.splitext(os.path.basename(SavePath))[0]

NowLevel = GetLevel(SavePath)
print_status("Current save level: Level {}".format(NowLevel))

print_ok("Initialization complete!")
print_status("Now monitoring save file for changes. Press 'P' to exit, 'O' to restore a save.")

WatchSave(SavePath)