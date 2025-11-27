import base64
import json
from Crypto.Cipher import AES


def decrypt_wechat_data(session_key, iv, encrypted_data):
    session_key = base64.b64decode(session_key)
    iv = base64.b64decode(iv)
    encrypted_data = base64.b64decode(encrypted_data)

    cipher = AES.new(session_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_data)

    # 去除 PKCS#7 padding
    pad = decrypted[-1]
    decrypted = decrypted[:-pad]

    decrypted_data = json.loads(decrypted.decode('utf-8'))
    return decrypted_data
