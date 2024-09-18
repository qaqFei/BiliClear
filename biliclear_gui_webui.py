import time
import sys
import json
from threading import Thread
from ctypes import windll
from os import environ; environ["gui"] = "enable"

import biliclear
import web_canvas as webcvapis

def worker():
    while True:
        try:
            while designateVideos:
                biliclear.checkVideo(designateVideos.pop())
            biliclear.checkNewVideos()
        except KeyError as e:
            print("错误", repr(e))
            if isinstance(e, json.JSONDecodeError):
                biliclear.waitRiskControl(False)

def render():
    while True:
        root.clear_canvas(wait_execute=True)
        
        root.create_rectangle( # background
            0, 0, w, h,
            fillStyle = "rgb(30, 30, 30)",
            wait_execute = True
        )
        
        root.create_text(
            w * 0.02,
            h * 0.02,
            text = "BiliClear 数据统计",
            font = f"{(w + h) / 45}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "#FFFFFF",
            wait_execute = True
        )
        
        root.create_text(
            w * 0.02,
            h * 0.1,
            text = f"已检查视频: {biliclear.videoCount}",
            font = f"{(w + h) / 125}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "#FFFFFFEE",
            wait_execute = True
        )
        
        root.create_text(
            w * 0.02,
            h * 0.13,
            text = f"已检查评论: {biliclear.replyCount}",
            font = f"{(w + h) / 125}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = "#FFFFFFEE",
            wait_execute = True
        )
        
        root.create_text(
            w * 0.02,
            h * 0.16,
            text = f"违规评论: {biliclear.violationsReplyCount}",
            font = f"{(w + h) / 125}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"#FFFFFFEE",
            wait_execute = True
        )
        
        replyPornRate = (biliclear.violationsReplyCount / biliclear.replyCount * 100) if biliclear.replyCount != 0 else 0.0
        root.create_text(
            w * 0.02,
            h * 0.19,
            text = f"评论违规率: {replyPornRate:.5f}%",
            font = f"{(w + h) / 125}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"#{"FFFFFF" if replyPornRate <= 0.1 else ("EEAAAA" if replyPornRate <= 0.5 else "EE4444")}EE",
            wait_execute = True
        )
        
        root.create_text(
            w * 0.02,
            h * 0.22,
            text = f"B站API风控中: {biliclear.waitingRiskControl}{f" 剩余时间: {biliclear.waitRiskControl_TimeRemaining:.2f}s" if biliclear.waitingRiskControl else ""}",
            font = f"{(w + h) / 125}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"#{"44CC44" if not biliclear.waitingRiskControl else "CC4444"}EE",
            wait_execute = True
        )
        
        root.create_text(
            w * 0.02,
            h * 0.25,
            text = f"tip: Ctrl + I 可以手动输入bv号, Ctrl + U 可以手动输入uid",
            font = f"{(w + h) / 100}px BiliClear_UIFont",
            textAlign = "left",
            textBaseline = "top",
            fillStyle = f"#FFFFFF88",
            wait_execute = True
        )
        
        root.run_js_code(
            f"""
                ctx.save();
                ctx.beginPath();
                ctx.moveTo({w * 0.02}, {h * 0.31});
                ctx.lineTo({w * 0.32}, {h * 0.31});
                ctx.lineTo({w * 0.32}, {h * 0.61});
                ctx.lineTo({w * 0.02}, {h * 0.61});
                ctx.lineTo({w * 0.02}, {h * 0.31});
                ctx.clip();
            """,
            add_code_array = True
        )
        
        item_y = h * 0.61 + getListItemAnimationDy(biliclear.checkedVideos, 1, 0.5) * (w + h) / 150 * 1.25
        texts = []
        for i in biliclear.checkedVideos:
            texts.append(f"已检查视频: av{i[0]}")
            
        for text in texts:
            root.create_text(
                w * 0.02,
                item_y,
                text = text,
                font = f"{(w + h) / 150}px BiliClear_UIFont",
                textAlign = "left",
                textBaseline = "bottom",
                fillStyle = "#FFFFFFDD",
                wait_execute = True
            )
            item_y -= (w + h) / 150 * 1.25
            if item_y < 0.0:
                break
        
        root.run_js_code(
            "ctx.restore();",
            add_code_array = True
        )
        
        root.run_js_code(
            f"""
                ctx.save();
                ctx.beginPath();
                ctx.moveTo({w * 0.02}, {h * 0.66});
                ctx.lineTo({w * 1.0}, {h * 0.66});
                ctx.lineTo({w * 1.0}, {h * 0.96});
                ctx.lineTo({w * 0.02}, {h * 0.96});
                ctx.lineTo({w * 0.02}, {h * 0.66});
                ctx.clip();
            """,
            add_code_array = True
        )
        
        item_y = h * 0.96 + getListItemAnimationDy(biliclear.checkedReplies, 2, 0.5) * (w + h) / 150 * 1.25
        texts = []
        for i in biliclear.checkedReplies:
            reply_content = i[1]
            if len(reply_content) > 10:
                reply_content = reply_content[:10] + "..."
            texts.append(f"已检查评论: rpid{i[0]}    内容: {repr(reply_content)[1:-1]}")
            
        for text in texts:
            root.create_text(
                w * 0.02,
                item_y,
                text = text,
                font = f"{(w + h) / 150}px BiliClear_UIFont",
                textAlign = "left",
                textBaseline = "bottom",
                fillStyle = "#FFFFFFDD",
                wait_execute = True
            )
            item_y -= (w + h) / 150 * 1.25
            if item_y < 0.0:
                break
        
        root.run_js_code(
            "ctx.restore();",
            add_code_array = True
        )
        
        try:
            root.run_js_wait_code()
        except Exception:
            pass
        
        time.sleep(1 / 60)

def getListItemAnimationDy(lst: list, index: int, atime: float):
    dy = 0.0
    for i in lst:
        t = i[index]
        itemp = (time.time() - t) / atime
        if 0.0 <= itemp <= 1.0:
            dy += 1.0 - itemp
    return dy

def addDesignateVideo():
    bvid = root.run_js_code("prompt('请输入BV号: ');")
    if isinstance(bvid, str) and bvid.startswith("BV"):
        designateVideos.append(bvid)
        root.run_js_code(f"alert('已添加BV号: {bvid}, 请耐心等待本轮推荐视频检查完毕');")
    else:
        root.run_js_code("alert('输入有误, 请重新输入');")

def processUser():
    uid = root.run_js_code("prompt('请输入UID: ');")
    if isinstance(uid, str) and uid.isdigit():
        biliclear.processUser(uid)
        root.run_js_code(f"alert('UID: {uid} 已检查完毕');")
    else:
        root.run_js_code("alert('输入有误, 请重新输入');")

def resize(nw: int, nh: int):
    global w, h
    w, h = nw, nh

designateVideos = []

root = webcvapis.WebCanvas(
    width = 1, height = 1,
    x = 0, y = 0,
    title = "BiliClear GUI",
    debug = "--debug" in sys.argv,
    frameless = "--frameless" in sys.argv
)
    
webdpr = root.run_js_code("window.devicePixelRatio;")
    
w, h = int(root.winfo_screenwidth() * 0.65), int(root.winfo_screenheight() * 0.65)
root.resize(w, h)
w_legacy, h_legacy = root.winfo_legacywindowwidth(), root.winfo_legacywindowheight()
dw_legacy, dh_legacy = w - w_legacy, h - h_legacy
dw_legacy *= webdpr; dh_legacy *= webdpr
dw_legacy, dh_legacy = int(dw_legacy), int(dh_legacy)
del w_legacy, h_legacy
root.resize(w + dw_legacy, h + dh_legacy)
root.move(int(root.winfo_screenwidth() / 2 - (w + dw_legacy) / webdpr / 2), int(root.winfo_screenheight() / 2 - (h + dh_legacy) / webdpr / 2))

with open("./res/ChillRoundGothic_Normal.otf", "rb") as f:
    root.reg_res(f.read(), "BiliClear_UIFont")
root.run_js_code(f"loadFont('BiliClear_UIFont', \"{root.get_resource_path("BiliClear_UIFont")}\");")
while not root.run_js_code("font_loaded;"):
    time.sleep(0.1)

root.reg_res(open("./res/2233.gif", "rb").read(), "img2233")
img2233path = root.get_resource_path("img2233")
root.run_js_code(f"load2233(('{img2233path}'));")
while not root.run_js_code("loaded2233"):
    time.sleep(0.1)
    
root.shutdown_fileserver()

root.jsapi.set_attr("addDesignateVideo", addDesignateVideo)
root.jsapi.set_attr("processUser", processUser)
root.run_js_code("_addDesignateVideo = (e) => {if (e.ctrlKey && !e.repeat && e.key.toLowerCase() == 'i') pywebview.api.call_attr('addDesignateVideo');};")
root.run_js_code("_processUser = (e) => {if (e.ctrlKey && !e.repeat && e.key.toLowerCase() == 'u') pywebview.api.call_attr('processUser');};")
root.run_js_code("window.addEventListener('keydown', _addDesignateVideo);")
root.run_js_code("window.addEventListener('keydown', _processUser);")
root.reg_event("resized", resize)

if "--window-host" in sys.argv:
    windll.user32.SetParent(root.winfo_hwnd(), eval(sys.argv[sys.argv.index("--window-host") + 1]))
    
Thread(target=worker, daemon=True).start()
Thread(target=render, daemon=True).start()
root.loop_to_close()
windll.kernel32.ExitProcess(0)