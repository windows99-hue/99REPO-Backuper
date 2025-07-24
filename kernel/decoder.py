from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad
from Crypto.Hash import HMAC, SHA1
import gzip
import json

def decrypt_es3(file_path, password):
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

file_path = r"D:\99之没事写的小程序\99REPO存档器\01\kernel\REPO_SAVE_2025_07_24_11_21_46.es3"

decrypted_data = decrypt_es3(file_path, "Why would you want to cheat?... :o It's no fun. :') :'D")

json_data = json.loads(decrypted_data)

level = json_data['dictionaryOfDictionaries']['value']['runStats']['level']
print("Level:",level)