import smtplib
import json
import time
import sys
import re  # used for rules matching
from email.mime.text import MIMEText
from email.header import Header
from os.path import exists, dirname, abspath
from getpass import getpass
import os

if os.name == "nt":

    def cleardisplay():
        return os.system("cls")
else:

    def cleardisplay():
        return os.system("clear")


import requests

import biliauth

sys.excepthook = (
    lambda *args: [print("^C"), exec("raise SystemExit")]
    if KeyboardInterrupt in args[0].mro()
    else sys.__excepthook__(*args)
)

selfdir = dirname(sys.argv[0])
if selfdir == "":
    selfdir = abspath(".")
os.chdir(selfdir)


def saveConfig():
    with open("./config.json", "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "sender_email": sender_email,
                    "sender_password": sender_password,
                    "headers": headers,
                    "smtp_server": smtp_server,
                    "smtp_port": smtp_port,
                    "bili_report_api": bili_report_api,
                    "csrf": csrf,
                },
                indent=4,
                ensure_ascii=False,
            )
        )


def getCsrf(cookie: str):
    return re.findall(r"bili_jct=(.*?);", cookie)[0]


def checkSmtpPassword():
    try:
        smtp_con = smtplib.SMTP_SSL(smtp_server, smtp_port)
        smtp_con.login(sender_email, sender_password)
        smtp_con.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        return False


if not exists("./config.json"):
    sender_email = input("Report sender email: ")
    sender_password = getpass("Report sender password: ")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Cookie": "",
    }

    match (input("\n是否使用二维码登录B站, 默认为是(y/n): ").lower() + " ")[
        0
    ]:  # + " " to avoid empty input
        case "n":
            headers["Cookie"] = getpass("Bilibili cookie: ")
        case _:
            headers["Cookie"] = biliauth.bilibiliAuth()

    csrf = getCsrf(headers["Cookie"])

    smtps = {
        "@aliyun.com": {"server": "smtp.aliyun.com", "port": 465},
        "@gmail.com": {"server": "smtp.gmail.com", "port": 465},
        "@sina.com": {"server": "smtp.sina.com.cn", "port": 465},
        "@tom.com": {"server": "smtp.tom.com", "port": 465},
        "@163.com": {"server": "smtp.163.com", "port": 465},
        "@126.com": {"server": "smtp.126.com", "port": 465},
        "@yahoo.com": {"server": "smtp.mail.yahoo.com", "port": 465},
        "@foxmail.com": {"server": "smtp.qq.com", "port": 465},
        "@sohu.com": {"server": "smtp.sohu.com", "port": 465},
        "@hotmail.com": {"server": "smtp.live.com", "port": 587},
        "@outlook.com": {"server": "smtp.office365.com", "port": 587},
        "@qq.com": {"server": "smtp.qq.com", "port": 465},
        "@feishu.cn": {"server": "smtp.feishu.cn", "port": 465},
    }

    print("\nSMTP servers:")
    for k, v in smtps.items():
        print(f"    {k}: server = {v['server']}, port = {v['port']}")

    smtp_server = input("\nSMTP server: ")
    smtp_port = int(input("SMTP port: "))
    bili_report_api = (
        "y" in input("是否额外使用B站评论举报API进行举报, 默认为否(y/n): ").lower()
    )

    saveConfig()
else:
    with open("./config.json", "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
            sender_email = config["sender_email"]
            sender_password = config["sender_password"]
            headers = config["headers"]
            smtp_server = config["smtp_server"]
            smtp_port = config["smtp_port"]
            bili_report_api = config.get("bili_report_api", False)
            csrf = config.get("csrf", getCsrf(headers["Cookie"]))
        except Exception:
            print("load config.json failed, please delete it or fix it")
            print("if you updated biliclear, please delete config.json and run again")
            input("按任意键退出...")
            raise SystemExit

    try:
        saveConfig()
    except Exception:
        print("warning: save config.json failed")

if not checkSmtpPassword():
    print("warning: SMTP password is wrong, please check it")

with open("./rules.txt", "r", encoding="utf-8") as f:
    rules = list(
        filter(
            lambda x: x and "eval" not in x and "exec" not in x, f.read().splitlines()
        )
    )

print("loaded, biliclear will run after 2.0s.")
time.sleep(2.0)
cleardisplay()


def getVideos():
    return [
        i["param"]
        for i in requests.get(
            "https://app.bilibili.com/x/v2/feed/index", headers=headers
        ).json()["data"]["items"]
        if i.get("can_play", 0)
    ]


def getReplys(avid: str | int):
    maxNum = 100
    page = 1
    replies = []
    while page * 20 <= maxNum:
        result = requests.get(
            f"https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&nohot=1&pn={page}&ps=20",
            headers=headers,
        ).json()
        try:
            replies += result["data"]["replies"]
        except Exception:
            break
        page += 1
    return replies


def isPorn(text: str):
    for rule in rules:
        if eval(rule):  # 一般来说, 只有rules.txt没有投毒, 就不会有安全问题
            return True, rule
    return False, None


def req_bili_report_api(data: dict):
    result = requests.post(
        "https://api.bilibili.com/x/v2/reply/report",
        headers=headers,
        data={
            "type": 1,
            "oid": data["oid"],
            "rpid": data["rpid"],
            "reason": 2,
            "csrf": csrf,
        },
    ).json()
    time.sleep(2.0)
    result_code = result["code"]
    if result_code not in (0, 12019):
        print("b站举报API调用失败, 返回体：", result)
    elif result_code == 0:
        print("Bilibili举报API调用成功")
    elif result_code == 12019:
        print("举报过于频繁, 等待60s")
        time.sleep(60)
        return req_bili_report_api(data)


def report(data: dict, r: str):
    report_text = f"""
违规用户UID：{data["mid"]}
违规类型：色情
违规信息发布形式：评论, (动态)
问题描述：该评论疑似发布色情信息，破坏了B站和互联网的和谐环境
诉求：移除违规内容，封禁账号

评论数据内容(B站API返回, x/v2/reply):
`
{json.dumps(data, ensure_ascii=False, indent=4)}
`

(此举报信息自动生成, 可能会存在误报)
评论内容匹配到的规则: {r}
"""
    print("违规评论:", repr(reply["content"]["message"]))
    print("rule:", r)

    msg = MIMEText(report_text, "plain", "utf-8")
    msg["From"] = str(Header("Report", "utf-8"))
    msg["To"] = str(Header("Bilibili", "utf-8"))
    msg["Subject"] = str(Header("违规内容举报", "utf-8"))
    smtp_con = smtplib.SMTP_SSL(smtp_server, smtp_port)
    smtp_con.login(sender_email, sender_password)
    smtp_con.sendmail(sender_email, ["help@bilibili.com"], msg.as_string())
    smtp_con.quit()

    if bili_report_api:
        req_bili_report_api(data)

    print()  # next line


def processReply(reply: dict):
    isp, r = isPorn(reply["content"]["message"])
    if isp and r is not None:
        report(reply, r)
    else:
        print(f" 一切正常... (吗?), {time.time()}\r", end="")


def setMethod():
    global method
    method = None
    method_choices = {"1": "自动获取推荐视频评论", "2": "获取指定视频评论"}

    while method not in method_choices.keys():
        if method is not None:
            print("输入错误")

        print("tip: 请定期检查bilibili cookie是否过期\n")
        for k, v in method_choices.items():
            print(f"{k}. {v}")
        method = input("选择: ")
        cleardisplay()


def bvid2avid(bvid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=headers
    ).json()
    return result["data"]["aid"]


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
                cleardisplay()
                link = input("输入视频bvid: ")
                for reply in getReplys(bvid2avid(link)):
                    processReply(reply)
                time.sleep(1.25)
            case _:
                print("链接格式错误")
    except Exception as e:
        print("err", e)
