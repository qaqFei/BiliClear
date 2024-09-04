import smtplib
import json
import time
import sys
import re # used for rules matching
from email.mime.text import MIMEText
from email.header import Header
from os import system, chdir
from os.path import exists, dirname, abspath
from getpass import getpass

import requests

selfdir = dirname(sys.argv[0])
if selfdir == "": selfdir = abspath(".")
chdir(selfdir)

if not exists("./config.json"):
    sender_email = input("Report sender email: ")
    sender_password = getpass("Report sender password: ")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Cookie": getpass("Bilibili cookie: ")
    }
    
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
        "@feishu.cn": {"server": "smtp.feishu.cn", "port": 465}
    }
    
    print("\nSMTP servers:")
    for k, v in smtps.items():
        print(f"    {k}: server = {v['server']}, port = {v['port']}")
    
    smtp_server = input("\nSMTP server: ")
    smtp_port = int(input("SMTP port: "))
    
    with open("./config.json", "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "sender_email": sender_email,
            "sender_password": sender_password,
            "headers": headers,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port
        }, indent=4, ensure_ascii=False))
else:
    with open("./config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        sender_email = config["sender_email"]
        sender_password = config["sender_password"]
        headers = config["headers"]
        smtp_server = config["smtp_server"]
        smtp_port = config["smtp_port"]

with open("./rules.txt", "r", encoding="utf-8") as f:
    rules = list(filter(lambda x: x and "eval" not in x and "exec" not in x, f.read().splitlines()))

system("cls")


def getVideos():
    return [
        i["param"]
        for i in requests.get(f"https://app.bilibili.com/x/v2/feed/index", headers=headers).json()["data"]["items"]
        if i.get("can_play", 0)
    ]

def getReplys(avid: str|int):
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

def isPorn(text: str):
    for rule in rules:
        if eval(rule): # 一般来说, 只有rules.txt没有投毒, 就不会有安全问题
            return True, rule
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
    smtp_con = smtplib.SMTP_SSL(smtp_server, smtp_port)
    smtp_con.login(sender_email, sender_password)
    smtp_con.sendmail(sender_email, ["help@bilibili.com"], msg.as_string())
    smtp_con.quit()

def processReply(reply: dict):
    isp, r = isPorn(reply["content"]["message"])
    if isp:
        print("porn", repr(reply["content"]["message"]), "\nrule:", r, "\n")
        report(reply, r)
    else:
        print(f" not porn, {time.time()}\r", end="")

def setMethod():
    global method
    method = None
    method_choices = {
        "1": "自动获取推荐视频评论",
        "2": "获取指定视频评论"
    }
    
    while method not in method_choices.keys():
        if method is not None:
            print("输入错误")
        
        print("tip: 请定期检查bilibili cookie是否过期\n")
        for k, v in method_choices.items():
            print(f"{k}. {v}")
        method = input("选择: ")
        system("cls")
        
def bvid2avid(bvid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
        headers=headers
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
                system("cls")
                link = input("输入视频bvid: ")
                for reply in getReplys(bvid2avid(link)):
                    processReply(reply)
                time.sleep(1.25)
            case _:
                print("链接格式错误")
    except (Exception, KeyboardInterrupt) as e:
        print("err", e)
        if isinstance(e, KeyboardInterrupt):
            break
