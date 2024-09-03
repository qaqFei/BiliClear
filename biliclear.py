import smtplib
import json
import time
from email.mime.text import MIMEText
from email.header import Header
from os import system
from getpass import getpass

import requests

sender_email = input("report sender email: ")
sender_password = getpass("report sender password: ")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Cookie": getpass("bilibili cookie: ")
}
system("cls")


def getVideos():
    return [
        i["param"]
        for i in requests.get(f"https://app.bilibili.com/x/v2/feed/index", headers=headers).json()["data"]["items"]
        if i.get("can_play", 0)
    ]

def getReplys(avid: str):
    maxNum = 100
    page = 1
    replies = []
    while page * 20 <= maxNum:
        result = requests.get(
            f"https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&nohot=1&pn={page}&ps=20",
            headers=headers
        ).json()
        try:
            replies += result["data"]["replies"]
        except Exception:
            break
        page += 1
    return replies

def getID(link: str):
    segments = link.split('/')
    for segment in segments:
        if segment.startswith('AV') or segment.startswith('BV'):
            return segment
    return None

def isPorn(text: str):
    rs = [
        '"动态" in text and "好东西" in text',
        '"今晚" in text and "动态" in text',
        '"最让我难以忘怀的是" in text and "真的好猛" in text',
        '"草坪练习" in text and "对光" in text',
        '"白天去美食火锅推荐，热辣过瘾" in text',
        '"在想你" in text and "而你在" in text',
        '"练习了" in text and "还是需要努力" in text and "感觉" in text',
        '"http" in text and "https" not in text',
        '"请叫我英雄" in text and "妹妹" in text and text.count("个") >= 2',
        '"每次呼吸" in text and "停一停" in text and text.count("[") >= 2',
        '".co" in text and "http" in text and text.count("[") >= 2',
        '"真不错" in text and "大" in text and "天然的" in text',
        '"选择" in text and "服从" in text and "当然" in text',
        '"是不是" in text and "我想" in text and "一探究竟" in text',
        '"忘记" in text and "炸了" in text and "几" in text',
        '"嘻嘻嘻" in text and "别管" in text and "清楚" in text',
        '"动作" in text and "上不来" in text and "感觉" in text',
        '"小贺" in text and "这边的" in text',
        '"密" in text and "桃" in text and "一样" in text',
        '"小蝴蝶" in text and "细节" in text and "！" in text',
        '"舞蹈了" in text and "练习" in text and "开心了" in text',
        '"你可能不知道" in text and "在" in text and "叫" in text',
    ]
    for r in rs:
        if eval(r):
            return True, r
    return False, None

def report(data: dict, r: str):
    report_text = f"""
违规用户UID：{data["mid"]}
违规类型：色情
违规信息发布形式：评论, (动态)
问题描述：该评论疑似发布色情信息，破坏了B站的和谐环境
诉求：移除违规内容，封禁账号

评论数据内容(B站API返回, x/v2/reply):
`
{json.dumps(data, ensure_ascii=False, indent=4)}
`

(此举报信息自动生成, 可能会存在误报)
评论内容匹配到的规则: {r}
"""
    msg = MIMEText(report_text, "plain", "utf-8")
    msg["From"] = Header("Report", "utf-8")
    msg["To"] = Header("Bilibili", "utf-8")
    msg["Subject"] = Header("违规内容举报", "utf-8")
    smtp_con = smtplib.SMTP_SSL("smtp.163.com", 465)
    smtp_con.login(sender_email, sender_password)
    smtp_con.sendmail(sender_email, ["help@bilibili.com"], msg.as_string())
    smtp_con.quit()

def processReply(reply: dict):
    isp, r = isPorn(reply["content"]["message"])
    if isp:
        print("porn", repr(reply["content"]["message"]))
        report(reply, r)
    else:
        print(f" not porn, {time.time()}\r", end="")

def setMethod():
    global method
    method = None
    while method not in ["1", "2"]:
        if method is not None:
            print("输入错误")
        method = input("1.自动获取推荐视频评论\n2.获取指定视频评论\n选择: ")
        system("cls")

setMethod()
while True:
    try:
        match method:
            case "1":
                for avid in getVideos():
                    for reply in getReplys(avid):
                        processReply(reply)
                    time.sleep(1.25)
            case "2":
                system("cls")
                link = input("输入视频bvid: ")
                videoID = getID(link)
                if videoID is not None:
                    for reply in getReplys(videoID):
                        processReply(reply)
                else:
                    print("链接格式错误")
    except (Exception, KeyboardInterrupt) as e:
        print("err", e)
        if e is KeyboardInterrupt or isinstance(e, KeyboardInterrupt):
            break
