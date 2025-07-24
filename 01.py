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

print_good("欢迎使用99 R.E.P.O 存档备份器！")
print_status("正在初始化程序...")

running = True
self_dir = os.path.dirname(os.path.abspath(__file__)) + "\\"
last_backup_time = 0  # 用于防止短时间内重复备份

#####备份#####

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
        print_warning("文件夹不存在，新建文件夹...")
        os.makedirs(SaverSavePath + "\\" + SavePathDir)

def BackupSave(level):
    global last_backup_time
    current_time = time.time()
    
    # 防止5秒内重复备份
    if current_time - last_backup_time < 5:
        #print_status("短时间内重复备份被阻止")
        return
    
    if not CheckLevelIfChanged(level):
        print_status("存档未变化")
        return
    
    print_status("正在备份第{}关...".format(level))
    GiveMe_a_Dir()
    try:
        backup_path = SaverSavePath + "\\" + SavePathDir + "\\" + SavePathName + ".level{}".format(level)
        shutil.copy(SavePath, backup_path)
        last_backup_time = current_time
    except Exception as e:
        print_error("备份存档失败: {}".format(e))
        return False
    print_good("第{}关备份成功！".format(level))

def WatchSave(filepath):
    global observer, NowLevel
    
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"文件 '{filepath}' 不存在")

    class FileModifiedHandler(FileSystemEventHandler):
        def __init__(self):
            self.debounce_timer = None
            
        def on_modified(self, event):
            global NowLevel
            if not event.is_directory and os.path.abspath(event.src_path) == os.path.abspath(filepath):
                # 使用延迟处理来防止多次触发
                if self.debounce_timer is not None:
                    return
                
                self.debounce_timer = time.time()
                print_status("存档{}被修改".format(filepath))
                try:
                    level = GetLevel(filepath)
                    BackupSave(level)
                    NowLevel = level  # 更新当前关卡
                except Exception as e:
                    print_error("处理存档修改时出错: {}".format(e))
                finally:
                    time.sleep(1)  # 添加短暂延迟
                    self.debounce_timer = None

    event_handler = FileModifiedHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(filepath), recursive=False)
    observer.start()
    
    def exit_program():
        global running
        print_warning("检测到按下 P 键，程序退出...")
        running = False
        observer.stop()
        observer.join(timeout=2)
        sys.exit(0)
    
    keyboard.add_hotkey('p', exit_program)
    
    while running:
        time.sleep(1)

def CheckDirVaild(path):
    return os.path.isdir(path)

#####回档#####

# 主程序
if __name__ != "__main__":
    sys.exit(1)

config = configparser.ConfigParser()
config.read(self_dir+'config.ini', encoding="utf-8")

SaverSavePath = config.get('Settings', 'SaverSavePath')
if SaverSavePath == "":
    print_error("配置文件中未设置存档备份路径，程序将无法运行。请先在配置文件中设置存档备份路径。")
    sys.exit(1)
if not CheckDirVaild(SaverSavePath):
    print_error("配置文件中设置的存档备份路径无效，请检查路径是否正确。")
    sys.exit(1)

print_status("请选择您想监控的存档位置")
SavePath = easygui.fileopenbox("请选择您想监控的存档位置", "选择存档位置")

if SavePath is None:
    sys.exit(0)

SavePathName = os.path.basename(SavePath)
SavePathDir = os.path.splitext(os.path.basename(SavePath))[0]

NowLevel = GetLevel(SavePath)
print_status("当前存档关卡:第{}关".format(NowLevel))

print_ok("初始化完成！")
print_status("开始监控存档文件变化,按P键退出,按O键恢复存档")

WatchSave(SavePath)