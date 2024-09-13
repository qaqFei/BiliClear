import json
import re
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
import logging

# 全局变量，用于在 GUI 环境下记录日志
gui_log = None

# 日志配置，如果是非 GUI 模式下
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

sys.excepthook = lambda *args: [logging.error("^C"), exec("raise SystemExit")] if KeyboardInterrupt in args[0].mro() else sys.__excepthook__(*args)

selfdir = dirname(sys.argv[0])
if selfdir == "": selfdir = abspath(".")
chdir(selfdir)

def saveConfig():
    try:
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
        logging.info("配置文件保存成功")
    except Exception as e:
        logging.error(f"保存config.json失败, 错误: {e}")

def loadConfig():
    global headers
    global bili_report_api, csrf
    global reply_limit, enable_gpt
    global enable_check_lv2avatarat
    global enable_check_replyimage

    try:
        config = json.load(f)
        headers = config["headers"]
        bili_report_api = config.get("bili_report_api", False)
        csrf = config.get("csrf", getCsrf(headers["Cookie"]))
        reply_limit = config.get("reply_limit", 100)
        enable_gpt = config.get("enable_gpt", False)
        gpt.openai.api_base = config.get("gpt_apibase", gpt.openai.api_base)
        gpt.openai.proxy = config.get("gpt_proxy", gpt.openai.proxy)
        gpt.openai.api_key = config.get("gpt_apikey", "")
        gpt.gpt_model = config.get("gpt_model", "gpt-4o-mini")
        enable_check_lv2avatarat = config.get("enable_check_lv2avatarat", False)
        enable_check_replyimage = config.get("enable_check_replyimage", False)
        if reply_limit <= 20:
            reply_limit = 100
        logging.info("配置文件加载成功")
    except Exception as e:
        logging.error(f"加载config.json失败, 错误: {repr(e)}")

def getCsrf(cookie: str):
    try:
        return re.findall(r"bili_jct=(.*?);", cookie)[0]
    except IndexError:
        logging.error("Bilibili Cookie格式错误, 重启BiliClear或删除config.json")
        syscmds.pause()
        raise SystemExit

def getCookieFromUser():
    if not environ.get("qt_gui", False):
        if "n" in input("\n是否使用二维码登录B站, 默认为是(y/n): ").lower():
            return getpass("Bilibili cookie: ")
        else:
            return biliauth.bilibiliAuth()

def checkCookie():
    try:
        result = requests.get(
            "https://passport.bilibili.com/x/passport-login/web/cookie/info",
            headers=headers,
            data={
                "csrf": csrf
            }
        ).json()
        return result["code"] == 0 and not result.get("data", {}).get("refresh", True)
    except Exception as e:
        logging.error(f"检查 Cookie 失败: {e}")
        return False

if not exists("./config.json"):
    if not environ.get("qt_gui", False):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Cookie": getCookieFromUser()
        }

        csrf = getCsrf(headers["Cookie"])
        bili_report_api = "y" in input("是否额外使用B站评论举报API进行举报, 默认为否(y/n): ").lower()
        reply_limit = 100
        enable_gpt = False
        gpt.openai.api_key = ""
        gpt.gpt_model = "gpt-4o-mini"
        enable_check_lv2avatarat = False
        enable_check_replyimage = False
    else: # 此else分支不由 qaqFei 维护
        config = gui_config.get_config()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Cookie": config["cookie"]
        }
        csrf = getCsrf(headers["Cookie"])
        bili_report_api = config["bili_report_api"]
        reply_limit = config["reply_limit"]
        enable_gpt = config["enable_gpt"]
        gpt.openai.api_key = config["gpt_api_key"]
        gpt.gpt_model = config["gpt_model"]
        enable_check_lv2avatarat = config["enable_check_lv2avatarat"]
        enable_check_replyimage = config["enable_check_replyimage"]
else:
    with open("./config.json", "r", encoding="utf-8") as f:
        try:
            loadConfig()
        except Exception as e:
            logging.error(f"加载config.json失败, 错误: {repr(e)}")
            syscmds.pause()
            raise SystemExit

if not checkCookie():
    logging.warning("bilibili cookie已过期或失效, 请重新登录")
    headers["Cookie"] = getCookieFromUser()
    csrf = getCsrf(headers["Cookie"])

try:
    saveConfig()
except Exception as e:
    logging.error(f"保存config.json失败, 错误: {e}")

text_checker = checker.Checker()
face_detector = cv2.CascadeClassifier("./res/haarcascade_frontalface_default.xml")

if not environ.get("qt_gui", False): # if gui is webui, it will wait, because 2 people is not the same brain.
    loaded_sleep_time = 3.0
    logging.info(f"加载完成, BiliClear将在{loaded_sleep_time}s后开始运行")
    time.sleep(loaded_sleep_time)
    syscmds.clearScreen()

def _btyes2cv2im(byte_data):
    # 将二进制数据转换为OpenCV图像格式
    nparr = np.frombuffer(byte_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def _img_face(img):
    return not isinstance(
        face_detector.detectMultiScale(
            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
            scaleFactor=1.2, minNeighbors=1
        ),
        tuple
    )

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
            headers=headers
        ).json()
        try:
            if not result["data"]["replies"]:
                break
            replies += result["data"]["replies"]
        except Exception:
            break
        page += 1
    return replies

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
        logging.error(f"b站举报API调用失败, 返回体：{result}")
    elif result_code == 0:
        logging.info("Bilibili举报API调用成功")
    elif result_code == 12019:
        logging.warning("举报过于频繁, 等待60s")
        time.sleep(60)
        return reqBiliReportReply(data, rule)

def reportReply(data: dict, r: str | None):
    "举报评论"
    report_text = f"""
违规用户UID：{data["mid"]}
违规信息发布形式：评论, (动态)
问题描述：破坏了B站和互联网的和谐环境
诉求：移除违规内容，封禁账号

评论数据内容(B站API返回, x/v2/reply):
`
{json.dumps(data, ensure_ascii=False, indent=4)}
`

(此举报信息自动生成, 可能会存在误报)
评论内容匹配到的规则: {r}
"""
    logging.info(f"违规评论: {repr(data['content']['message'])}")
    logging.info(f"规则: {r}")

    if bili_report_api:
        reqBiliReportReply(data, r)

def replyIsViolations(reply: dict):
    "判断评论是否违规, 返回: (是否违规, 违规原因) 如果没有违规, 返回 (False, None)"
    global enable_gpt

    reply_msg = reply["content"]["message"]
    isp, r = isPorn(reply_msg)

    if "doge" in reply_msg:
        return False, None

    # 使用 GPT 进行内容检测
    if not isp and enable_gpt:
        try:
            isp, r = gpt.gpt_porn(reply_msg) or gpt.gpt_ad(reply_msg), f"ChatGpt - {gpt.gpt_model} 检测到违规内容"
            logging.debug(f"调用GPT进行检测, 结果: {isp}")
        except gpt.RateLimitError:
            enable_gpt = False
            saveConfig()
            logging.warning("GPT请求达到限制, 已关闭GPT检测")

    # lv.2用户头像检测（人脸检测）
    if not isp and enable_check_lv2avatarat and reply["member"]["level_info"][
        "current_level"] == 2 and "@" in reply_msg:
        avatar_image = requests.get(
            reply["member"]["avatar"],
            headers=headers
        ).content
        if _img_face(_btyes2cv2im(avatar_image)):  # 检测头像中的人脸
            isp, r = True, "lv.2, 检测到头像中包含人脸,可疑"
        logging.debug(f"lv.2和人脸检测, 结果: {isp}")

    # lv.2评论图片检测（二维码和人脸检测）
    if not isp and enable_check_replyimage and reply["member"]["level_info"]["current_level"] == 2:
        # try:
            # 获取评论中的图片并转换为OpenCV格式
            images = [requests.get(i["img_src"], headers=headers).content for i in reply["content"]["pictures"]]
            opencv_images = [_btyes2cv2im(image) for image in images]

            # 检测二维码
            have_qrcode = any([cv2.QRCodeDetector().detect(img)[0] for img in opencv_images])

            # 检测人脸
            have_face = any([_img_face(img) for img in opencv_images])

            if have_qrcode or have_face:
                isp, r = True, "lv.2, 检测到评论中包含二维码或人脸, 可疑"
            logging.debug(f"lv.2和二维码、人脸检测, 结果: {isp}")
        # except Exception as e:
        #     logging.warning(f"警告: 二维码或人脸检测时发生错误, 已跳过 {repr(e)}")

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
            logging.error("输入错误")

        print("tip: 请定期检查bilibili cookie是否过期 (BiliClear启动时会自动检查)\n")
        for k, v in method_choices.items():
            print(f"{k}. {v}")
        method = input("选择: ")
        syscmds.clearScreen()

def bvid2avid(bvid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
        headers=headers
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

    logging.info("开始检查新一轮推荐视频...")
    logging.info(f"已检查视频: {videoCount}")
    logging.info(f"已检查评论: {replyCount}")
    logging.info(f"已举报评论: {violationsReplyCount} 评论违规率: {((violationsReplyCount / replyCount * 100) if replyCount != 0 else 0.0):.5f}%")

    for avid in getVideos():
        logging.info(f"开始检查视频: av{avid}, 现在时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    logging.warning(f"警告!!! B站API返回了非JSON格式数据, 大概率被风控, 暂停{stopMinute}分钟...")
    while time.time() - stopSt < 60 * stopMinute:
        waitRiskControl_TimeRemaining = 60 * stopMinute - (time.time() - stopSt)
        if output:
            logging.warning(f"由于可能被风控, BiliClear暂停{stopMinute}分钟, 还剩余: {waitRiskControl_TimeRemaining:.2f}s")
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
                    logging.error("链接格式错误")
        except Exception as e:
            logging.error(f"错误 {repr(e)}")
            if isinstance(e, json.JSONDecodeError):
                waitRiskControl()
