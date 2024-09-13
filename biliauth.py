import time
import requests
import tkinter
import threading
import io
from urllib.parse import quote_plus

from PIL import Image, ImageTk

_qrcode_image = None

def bilibiliAuth() -> str:
    global _qrcode_image
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    result = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers = headers
    ).json()
    qr_url = f"https://tool.oschina.net/action/qrcode/generate?data={quote_plus(result["data"]["url"])}&output=image/png&error=M&type=0&margin=4&size=4"
    qrcode_window = tkinter.Tk()
    qrcode_window.title("请使用B站扫码登录")
    qrcode_window.iconbitmap("res/icon.ico")
    qrcode_window.protocol("WM_DELETE_WINDOW", lambda: None)
    qrcode_window.resizable(False, False)
    qrcode_size = int(min(qrcode_window.winfo_screenwidth(), qrcode_window.winfo_screenheight()) * 0.45)
    _qrcode_image = ImageTk.PhotoImage(Image.open(io.BytesIO(requests.get(qr_url).content)).resize((qrcode_size, qrcode_size)))
    tkinter.Label(qrcode_window, image = _qrcode_image).pack()
    
    cookie = None
    
    def _poll():
        nonlocal cookie
        
        params = {
            "qrcode_key": result["data"]["qrcode_key"],
            "source": "main-fe-header",
        }

        while True:
            result_cookie = requests.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                params = params,
                headers = headers
            )
            if result_cookie.json()["data"]["code"] == 0:
                cookie_dict = requests.utils.dict_from_cookiejar(result_cookie.cookies)
                print("\n获取cookie成功")
                cookie = "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])
                return None
            time.sleep(0.4)
    
    threading.Thread(target=_poll, daemon=True).start()
    
    while cookie is None:
        qrcode_window.update()
        time.sleep(1 / 30)
        
    qrcode_window.destroy()
        
    return cookie