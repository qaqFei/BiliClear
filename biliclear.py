import json
import re  # used for rules matching
import sys
import time
from datetime import datetime
from os import chdir, environ
from os.path import exists, dirname, abspath

import cv2
import numpy as np
import requests

import biliauth
import gpt
import gui_config
import syscmds
import checker
from compatible_getpass import getpass

sys.excepthook = lambda *args: [print("^C"), exec("raise SystemExit")] if KeyboardInterrupt in args[0].mro() else sys.__excepthook__(*args)

selfdir = dirname(sys.argv[0])
if selfdir == "": selfdir = abspath(".")
chdir(selfdir)

def saveConfig():
    with open("./config.json", "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "headers": headers,
            "bili_report_api": bili_report_api,
            "csrf": csrf,
            "reply_limit": reply_limit,
            "enable_gpt": enable_gpt,
            "gpt_apibase": gpt.openai.api_base,
            "gpt_proxy": gpt.openai.proxy,
            "gpt_apikey": gpt.openai.api_key,
            "gpt_model": gpt.gpt_model,
            "enable_check_lv2avatarat": enable_check_lv2avatarat,
            "enable_check_replyimage": enable_check_replyimage
        }, indent=4, ensure_ascii=False))

def putConfigVariables(config: dict):
    global headers
    global bili_report_api, csrf
    global reply_limit, enable_gpt
    global enable_check_lv2avatarat
    global enable_check_replyimage
    
    headers = config["headers"]
    bili_report_api = config.get("bili_report_api", True)
    csrf = config.get("csrf", getCsrf(headers["Cookie"]))
    reply_limit = config.get("reply_limit", 100)
    enable_gpt = config.get("enable_gpt", False)
    gpt.openai.api_base = config.get("gpt_apibase", gpt.openai.api_base)
    gpt.openai.proxy = config.get("gpt_proxy", gpt.openai.proxy)
    gpt.openai.api_key = config.get("gpt_apikey", "")
    gpt.gpt_model = config.get("gpt_model", "gpt-4o-mini")
    enable_check_lv2avatarat = config.get("enable_check_lv2avatarat", False)
    enable_check_replyimage = config.get("enable_check_replyimage", True)
    if reply_limit <= 20:
        reply_limit = 100
    
def getCsrf(cookie: str):
    try:
        return re.findall(r"bili_jct=(.*?);", cookie)[0]
    except IndexError:
        print("Bilibili Cookie格式错误, 重启BiliClear或删除config.json")
        print("请按回车键退出...")
        syscmds.pause()
        raise SystemExit

def getCookieFromUser():
    if not environ.get("gui", False):
        if "n" in input("是否使用二维码登录B站, 默认为是(y/n): ").lower():
            return getpass("Bilibili cookie: ")
        else:
            return biliauth.bilibiliAuth()

def checkCookie():
    result = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/cookie/info",
        headers = headers,
        data = {
            "csrf": csrf
        }
    ).json()
    return result["code"] == 0 and not result.get("data", {}).get("refresh", True)

if not exists("./config.json"):
    if not environ.get("gui", False):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Cookie": getCookieFromUser()
        }

        csrf = getCsrf(headers["Cookie"])

        bili_report_api = True
        reply_limit = 100
        enable_gpt = False
        gpt.openai.api_key = ""
        gpt.gpt_model = "gpt-4o-mini"
        enable_check_lv2avatarat = False
        enable_check_replyimage = True
    else:
        putConfigVariables(gui_config.get_email_config())
else:
    with open("./config.json", "r", encoding="utf-8") as f:
        try:
            putConfigVariables(json.load(f))
        except Exception as e:
            print("加载config.json失败, 请删除或修改config.json, 错误:", repr(e))
            print("如果你之前更新过BiliClear, 请删除config.json并重新运行")
            print("请按回车键退出...")
            syscmds.pause()
            raise SystemExit

if not checkCookie():
    print("bilibili cookie已过期或失效, 请重新登录")
    headers["Cookie"] = getCookieFromUser()
    csrf = getCsrf(headers["Cookie"])

try:
    saveConfig()
except Exception as e:
    print("警告: 保存config.json失败, 错误:", e)

text_checker = checker.Checker()
face_detector = cv2.CascadeClassifier("./res/haarcascade_frontalface_default.xml")

if not environ.get("gui", False):
    loaded_sleep_time = 3.0
    print(f"加载完成, BiliClear将在{loaded_sleep_time}s后开始运行")
    time.sleep(loaded_sleep_time)
    syscmds.clearScreen()

def _btyes2cv2im(byte_data):
    nparr = np.frombuffer(byte_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def _img_face(img: cv2.typing.MatLike):
    return not isinstance(
        face_detector.detectMultiScale(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
            scaleFactor=1.2, minNeighbors=1
        ),
        tuple
    )

def _img_qrcode(img: cv2.typing.MatLike):
    return cv2.QRCodeDetector().detect(img)[0]

def getVideos():
    "获取推荐视频列表"
    return [
        i["param"]
        for i in requests.get(f"https://app.bilibili.com/x/v2/feed/index", headers=headers).json()["data"]["items"]
        if i.get("can_play", 0)
    ]

def getReplys(avid: str | int):
    "获取评论"
    maxNum = reply_limit
    page = 1
    replies = []
    while page * 20 <= maxNum:
        time.sleep(0.4)
        result = requests.get(
            f"https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&nohot=1&pn={page}&ps=20",
            headers = headers
        ).json()
        try:
            if not result["data"]["replies"]:
                break
            replies += result["data"]["replies"]
        except Exception:
            break
        page += 1
    return replies

def checkUser(uid: int):
    "检查用户是否需要举报"
    user_crad = requests.get(
        f"https://api.bilibili.com/x/web-interface/card?mid={uid}",
        headers = headers
    ).json()["data"]["card"]
    
    if user_crad["spacesta"] == -2:
        return False # 封了, 没必要
    
    if user_crad["level_info"]["current_level"] != 2:
        return False # 不是 lv.2, 没必要
    
    dynamics = [i["modules"]["module_dynamic"] for i in requests.get(
        f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?host_mid={uid}",
        headers = headers
    ).json()["data"]["items"]]
    
    for dynamic in dynamics:
        if dynamic["desc"] is None:
            continue
        
        text = dynamic["desc"]["text"]
        if isPorn(text):
            return True
        
        if dynamic["major"] is None:
            continue
        elif dynamic["major"]["type"] != "MAJOR_TYPE_DRAW":
            continue
        
        ims = [_btyes2cv2im(requests.get(i["src"]).content) for i in dynamic["major"]["draw"]["items"]]
        if any([_img_qrcode(img) for img in ims]):
            return True
    
    return False
        
def isPorn(text: str):
    "判断评论是否为色情内容 (使用规则, rules.yaml)"
    return text_checker.check(text)

def reqBiliReportReply(data: dict, rule: str | None):
    "调用B站举报评论API"
    result = requests.post(
        "https://api.bilibili.com/x/v2/reply/report",
        headers=headers,
        data={
            "type": 1,
            "oid": data["oid"],
            "rpid": data["rpid"],
            "reason": 0,
            "csrf": csrf,
            "content": f"""
举报原因: 色情, 或...
程序匹配到的规则: {rule}
(此举报信息自动生成, 可能会存在误报)
"""
        }
    ).json()
    time.sleep(3.5)
    result_code = result["code"]
    if result_code not in (0, 12019):
        print("b站举报API调用失败, 返回体：", result)
    elif result_code == 0:
        print("Bilibili举报API调用成功")
    elif result_code == 12019:
        print("举报过于频繁, 等待15s")
        time.sleep(15)
        return reqBiliReportReply(data, rule)

def reportReply(data: dict, r: str | None):
    print("\n违规评论:", repr(data["content"]["message"]))
    print("规则:", r)

    if bili_report_api:
        reqBiliReportReply(data, r)

    print()  # next line

def replyIsViolations(reply: dict):
    "判断评论是否违规, 返回: (是否违规, 违规原因) 如果没有违规, 返回 (False, None)"
    global enable_gpt

    reply_msg = reply["content"]["message"]
    isp, r = isPorn(reply_msg)

    if "doge" in reply_msg:
        return False, None

    if not isp and enable_gpt:
        try:
            isp, r = gpt.gpt_porn(reply_msg) or gpt.gpt_ad(reply_msg), f"ChatGpt - {gpt.gpt_model} 检测到违规内容"
            print(f"调用GPT进行检测, 结果: {isp}")
        except gpt.RateLimitError:
            enable_gpt = False
            saveConfig()
            print("GPT请求达到限制, 已关闭GPT检测")

    if not isp and enable_check_lv2avatarat and reply["member"]["level_info"][
        "current_level"] == 2 and "@" in reply_msg:
        avatar_image = requests.get(
            reply["member"]["avatar"],
            headers=headers
        ).content
        if _img_face(_btyes2cv2im(avatar_image)):
            isp, r = True, "lv.2, 检测到头像中包含人脸,可疑"
        print(f"lv.2和人脸检测, 结果: {isp}")

    if not isp and enable_check_replyimage and reply["member"]["level_info"]["current_level"] == 2:
        try:
            images = [requests.get(i["img_src"], headers=headers).content for i in reply["content"].get("pictures", [])]
            opencv_images = [_btyes2cv2im(img) for img in images]
            have_qrcode = any([_img_qrcode(img) for img in opencv_images])
            have_face = any([_img_face(img) for img in opencv_images])

            if have_qrcode or have_face:
                isp, r = True, "lv.2, 检测到评论中包含二维码或人脸, 可疑"
            print(f"lv.2和二维码、人脸检测, 结果: {isp}")
        except Exception as e:
            print("警告: 二维码或人脸检测时发生错误, 已跳过", repr(e))

    return isp, r

def processReply(reply: dict):
    "处理评论并举报"
    global replyCount, violationsReplyCount
    global checkedReplies, violationsReplies

    replyCount += 1
    isp, r = replyIsViolations(reply)

    if isp:
        violationsReplyCount += 1
        reportReply(reply, r)
        violationsReplies.insert(0, (reply["rpid"], reply["content"]["message"], time.time()))

    checkedReplies.insert(0, (reply["rpid"], reply["content"]["message"], time.time()))
    checkedReplies = checkedReplies[:1500]
    violationsReplies = violationsReplies[:1500]
    return isp, r

def videoIsViolations(avid: str | int):
    isp, r = False, None

    return isp, r

def processVideo(avid: str | int):
    "处理视频并举报"
    isp, r = videoIsViolations(avid)

def _setMethod():
    global method
    method = None
    method_choices = {
        "1": "自动获取推荐视频评论",
        "2": "获取指定视频评论"
    }

    while method not in method_choices.keys():
        if method is not None:
            print("输入错误")

        print("tip: 请定期检查bilibili cookie是否过期 (BiliClear启动时会自动检查)\n")
        for k, v in method_choices.items():
            print(f"{k}. {v}")
        method = input("选择: ")
        syscmds.clearScreen()

def bvid2avid(bvid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
        headers = headers
    ).json()
    return result["data"]["aid"]

videoCount = 0
replyCount = 0
violationsReplyCount = 0
waitRiskControl_TimeRemaining = float("nan")
waitingRiskControl = False
checkedVideos = []
checkedReplies = []
violationsReplies = []


def _checkVideo(avid: str | int):
    processVideo(avid)
    for reply in getReplys(avid):
        processReply(reply)

def checkNewVideos():
    global videoCount, replyCount, violationsReplyCount, checkedVideos

    print("".join([("\n" if videoCount != 0 else ""), "开始检查新一轮推荐视频..."]))
    print(f"已检查视频: {videoCount}")
    print(f"已检查评论: {replyCount}")
    print(
        f"已举报评论: {violationsReplyCount} 评论违规率: {((violationsReplyCount / replyCount * 100) if replyCount != 0 else 0.0):.5f}%")
    print()  # next line

    for avid in getVideos():
        print(f"开始检查视频: av{avid}, 现在时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
        _checkVideo(avid)
        videoCount += 1
        checkedVideos.insert(0, (avid, time.time()))
        checkedVideos = checkedVideos[:1500]
    time.sleep(1.25)

def checkVideo(bvid: str):
    global videoCount, checkedVideos

    avid = bvid2avid(bvid)
    _checkVideo(avid)
    videoCount += 1
    checkedVideos.insert(0, (avid, time.time()))
    checkedVideos = checkedVideos[:1500]
    time.sleep(1.25)

def waitRiskControl(output: bool = True):
    global waitRiskControl_TimeRemaining, waitingRiskControl

    stopSt = time.time()
    stopMinute = 3
    waitRiskControl_TimeRemaining = 60 * stopMinute
    waitingRiskControl = True
    print(f"警告!!! B站API返回了非JSON格式数据, 大概率被风控, 暂停{stopMinute}分钟...")
    while time.time() - stopSt < 60 * stopMinute:
        waitRiskControl_TimeRemaining = 60 * stopMinute - (time.time() - stopSt)
        if output:
            print(f"由于可能被风控, BiliClear暂停{stopMinute}分钟, 还剩余: {waitRiskControl_TimeRemaining:.2f}s")
            time.sleep(1.5)
        else:
            time.sleep(0.005)
    waitingRiskControl = False

if __name__ == "__main__":
    _setMethod()
    while True:
        try:
            match method:
                case "1":
                    checkNewVideos()
                case "2":
                    checkVideo(input("\n输入视频bvid: "))
                case _:
                    print("链接格式错误")
        except Exception as e:
            print("错误", repr(e))
            if isinstance(e, json.JSONDecodeError):
                waitRiskControl()