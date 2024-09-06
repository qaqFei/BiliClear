import time
from urllib.parse import quote_plus
import requests
import qrcode


def get_bilibili_qrcode_url(headers: dict) -> dict:
    """生成用于B站登录的二维码URL和key。"""
    response = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers=headers,
    )
    return response.json()["data"]


def display_qrcode_ascii(qrcode_url: str):
    """在控制台以ASCII字符形式显示二维码。"""
    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(qrcode_url)

    qr.print_ascii(invert=True)

    print(
        f"如有扫描问题请使用下方网站登录B站: \nhttps://tool.oschina.net/action/qrcode/generate?data={quote_plus(qrcode_url)}&output=image/png&error=M&type=0&margin=4&size=4"
    )


def poll_bilibili_login(qrcode_key: str, headers: dict) -> requests.Response:
    """轮询B站登录状态，检查是否成功。"""
    params = {"qrcode_key": qrcode_key, "source": "main-fe-header"}
    return requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
        params=params,
        headers=headers,
    )


def bilibiliAuth() -> str:
    """登录B站并返回cookie。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    # 获取二维码的URL和key
    data = get_bilibili_qrcode_url(headers)
    display_qrcode_ascii(data["url"])

    # 轮询登录状态
    last_status = None
    while True:
        result_cookie = poll_bilibili_login(data["qrcode_key"], headers)
        result_json = result_cookie.json()
        code = result_json["data"]["code"]
        if code == 0:
            cookie_dict = requests.utils.dict_from_cookiejar(result_cookie.cookies)
            print("\n获取cookie成功")
            return "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])

        elif code == 86038:
            print("\n二维码已失效，重新生成中...")
            data = get_bilibili_qrcode_url(headers)
            display_qrcode_ascii(data["url"])
            last_status = "expired"

        elif code == 86101:
            current_status = "waiting"
            if current_status != last_status:
                print("等待登录中...")
                last_status = current_status
            time.sleep(1)

        elif code == 86090:
            current_status = "verified"
            if current_status != last_status:
                print("扫码成功，请在手机上确认登录")
                last_status = current_status
            time.sleep(1)
        else:
            print(result_json)
            time.sleep(1)
