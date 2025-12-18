import json
import time
import uuid
import base64
import requests

from django.conf import settings
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


def _sign_message(message: str) -> str:
    """
    使用商户私钥进行 RSA SHA256 签名
    """
    with open(settings.WX_MCH_PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode()


def wechat_post(url: str, body: dict) -> dict:
    """
    微信支付 V3 POST 请求（JSAPI 下单）
    """
    body_json = json.dumps(body, separators=(',', ':'), ensure_ascii=False)
    timestamp = str(int(time.time()))
    nonce_str = uuid.uuid4().hex

    path = url.replace("https://api.mch.weixin.qq.com", "")

    message = "\n".join([
        "POST",
        path,
        timestamp,
        nonce_str,
        body_json,
        ""
    ])

    signature = _sign_message(message)

    authorization = (
        f'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{settings.WX_MCHID}",'
        f'nonce_str="{nonce_str}",'
        f'timestamp="{timestamp}",'
        f'serial_no="{settings.WX_MCH_CERT_SERIAL_NO}",'
        f'signature="{signature}"'
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": authorization
    }

    resp = requests.post(
        url,
        headers=headers,
        data=body_json.encode("utf-8"),
        timeout=10
    )

    if resp.status_code not in (200, 201):
        raise Exception(f"WeChat Pay Error {resp.status_code}: {resp.text}")

    return resp.json()

def build_jsapi_pay_params(prepay_id: str) -> dict:
    """
    构造 wx.requestPayment 所需参数
    """
    time_stamp = str(int(time.time()))
    nonce_str = uuid.uuid4().hex
    package = f"prepay_id={prepay_id}"

    message = "\n".join([
        settings.WX_APPID,
        time_stamp,
        nonce_str,
        package,
        ""
    ])

    pay_sign = _sign_message(message)

    return {
        "timeStamp": time_stamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign
    }