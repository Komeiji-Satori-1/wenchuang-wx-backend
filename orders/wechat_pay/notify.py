import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def decrypt_wechat_resource(resource: dict) -> dict:
    """
    解密微信支付回调 resource
    """
    api_v3_key = settings.WX_API_V3_KEY.encode("utf-8")

    ciphertext = base64.b64decode(resource["ciphertext"])
    nonce = resource["nonce"].encode("utf-8")
    associated_data = resource.get("associated_data")

    aad = associated_data.encode("utf-8") if associated_data else None

    aesgcm = AESGCM(api_v3_key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)

    return json.loads(plaintext.decode("utf-8"))
