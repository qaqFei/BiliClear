import time
import requests
from urllib.parse import quote_plus

import syscmds

def bilibiliAuth() -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    result = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers = headers
    ).json()
    login_url = f"https://tool.oschina.net/action/qrcode/generate?data={quote_plus(result["data"]["url"])}&output=image/png&error=M&type=0&margin=4&size=4"
    
    print(f"请使用下方网站登录B站: \n{login_url}")
    params = {
        "qrcode_key": result["data"]["qrcode_key"],
        "source": "main-fe-header",
    }
    
    print("\n登录成功请按回车键...", end="")
    syscmds.pause()
    result_cookie = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
        params = params,
        headers = headers
    )
    if result_cookie.json()["data"]["code"] == 0:
        cookie_dict = requests.utils.dict_from_cookiejar(result_cookie.cookies)
        print("\n获取cookie成功")
        return "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])
    print("\n获取cookie失败:", result_cookie.json()["data"]["message"], "\n")
    time.sleep(0.5)
    return bilibiliAuth()