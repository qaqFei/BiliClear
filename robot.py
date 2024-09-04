import smtplib
import json
import time
import sys
import re
from email.mime.text import MIMEText
from email.header import Header
from os import system, chdir
from os.path import exists, dirname, abspath
from getpass import getpass
import requests
from threading import Thread
from queue import Queue
from functools import lru_cache

selfdir = dirname(sys.argv[0])
if selfdir == "": selfdir = abspath(".")
chdir(selfdir)

if not exists("./config.json"):
    sender_email = input("report sender email: ")
    sender_password = getpass("report sender password: ")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Cookie": getpass("bilibili cookie: ")
    }
    
    smtps = {
           "@mali.aliyun.com": "server = smtp.aliyun.com, port = 465",
        "@google.com": "server = smtp.gmail.com, port = 587",
        "@sina.com": "server = smtp.sina.com.cn, port = 25",
        "@top.com": "server = smtp.tom.com, port = 25",
        "@163.com": "server = smtp.163.com, port = 465",
        "@126.com": "server = smtp.126.com, port = 25",
        "@yahoo.com.cn": "server = smtp.mail.yahoo.com.cn, port = 587",
        "@foxmail.com": "server = smtp.foxmail.com, port = 25",
        "@sohu.com": "server = smtp.sohu.com, port = 25"

    }
    print("\nsmtp servers:")
    for k, v in smtps.items():
        print(f"    {k}: {v}")
    smtp_server = input("\nsmtp server: ")
    smtp_port = int(input("smtp port: "))
    
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
    compiled_rules = [re.compile(rule) for rule in rules]

system("cls")

def getVideos():
      return [
        i["param"]
        for i in requests.get(f"https://app.bilibili.com/x/v2/feed/index", headers=headers).json()["data"]["items"]
        if i.get("can_play", 0)
    }

@lru_cache(maxsize=100) # 使用LRU缓存来缓存API响应
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
    for rule in compiled_rules:
        if rule.search(text): # 使用预编译的正则表达式进行匹配
            return True, rule.pattern
    return False, None

def report(data: dict, r: str):
      report_text = f"""
违规用户UID：{data["mid"]}
违规类型：色情
违规信息发布形式：评论, (动态)
问题描述：该评论疑似发布色情信息，破坏了B站的和谐环境
诉求：移除违规内容，封禁账号

评论数据内容(B站API返回, x/v2/reply):
{json.dumps(data, ensure_ascii=False, indent=4)}

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

def bvid2avid(bvid: str):
       result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
        headers=headers
    ).json()
    return result["data"]["aid"]


setMethod()

def worker(queue):
    while True:
        avid = queue.get()
        if avid is None:
            break
        try:
            for reply in getReplys(avid):
                processReply(reply)
        except Exception as e:
            print("err", e)
        finally:
            queue.task_done()

num_threads = 4 # 设置线程数量为4个，可以根据需要调整
work_queue = Queue()
threads = []
for _ in range(num_threads):
    t = Thread(target=worker, args=(work_queue,))
    t.start()
    threads.append(t)

while True:
    try:
        match method:
            case "1":
                for avid in getVideos():
                    work_queue.put(avid)
                work_queue.join() # 等待所有任务完成
            case "2":
                system("cls")
                link = input("输入视频bvid: ")
                work_queue.put(bvid2avid(link))
                work_queue.join() # 等待所有任务完成
            case _:
                print("链接格式错误")
    except (Exception, KeyboardInterrupt) as e:
        print("err", e)
        if isinstance(e, KeyboardInterrupt):
            break
    finally:
        for _ in range(num_threads): # 向队列中添加None来通知线程退出
            work_queue.put(None)
        for t in threads: # 等待所有线程结束
            t.join()
