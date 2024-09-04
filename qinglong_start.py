# cron:21 7 * * *
# new Env("bilibili举报违规")

import json
import re
import sys
from datetime import datetime
from urllib.parse import quote_plus
import smtplib
import json
import time
import re # used for rules matching
from email.mime.text import MIMEText
from email.header import Header
from os import system, chdir
from os.path import exists, dirname, abspath
import requests

def bilibili_saoma():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    }
    res = requests.get(headers=headers, url="https://passport.bilibili.com/x/passport-login/web/qrcode/generate").json()
    login_url = quote_plus(res['data']['url'])
    print('请前往以下网址扫码登录，若显示错误，请等待20s后程序自动结束')
    print("https://tool.oschina.net/action/qrcode/generate?data=" + login_url + "&output=image/png&error=M&type=0&margin=4&size=4")
    params = {
        'qrcode_key': res['data']['qrcode_key'],
        'source': 'main-fe-header',
    }
    for i in range(0, 10):
        response = requests.get(
            'https://passport.bilibili.com/x/passport-login/web/qrcode/poll',
            params=params,
            headers=headers,
        )
        if response.json()['data']['code'] == 0:
            cookies = response.cookies
            print(cookies)
            # 将 RequestsCookieJar 转换为字典
            cookie_dict = requests.utils.dict_from_cookiejar(cookies)
            # 生成 cookies 字符串
            cookie_str = '; '.join([f'{key}={value}' for key, value in cookie_dict.items()])
            # 打印组合后的 cookie 字符串
            return cookie_str
        print(datetime.now(), response.json()['data']['message'])
        time.sleep(3)


def check_json():
    global sender_email,sender_password,headers ,smtp_server ,smtp_port
    config_ok=True
    if not exists("./config.json"):# 不存在配置文件
        # 打开青龙配置文件,读取邮件信息
        print("开始读取邮件配置")
        try:#防止用户未填写导致的意外
            with open('/ql/data/config/config.sh', 'r', encoding="utf-8") as file:
                content = file.read()
            #拿取相关信息
            SMTP_SERVICE = re.findall('SMTP_SERVICE="(.* ?)"', content)[0]
            sender_email = re.findall('SMTP_EMAIL="(.* ?)"', content)[0]
            sender_password = re.findall('SMTP_PASSWORD="(.* ?)"', content)[0]
            #读邮箱服务器json
            with open('services.json', 'r', encoding='utf-8') as file:
                services_json = json.load(file)
            smtp_server = services_json[SMTP_SERVICE]['host']
            smtp_port = services_json[SMTP_SERVICE]['port']
            print("自动读取邮件相关配置成功！")
            print(f"邮件配置信息：sender_email:{sender_email},sender_password:{sender_password},smtp_server:{smtp_server},smtp_port:{smtp_port}")
        except Exception as e:
            print(e)
            print("自动读取邮件相关配置出错，请手动在config.json内补全")
            #为了避免意外，改为空
            sender_email=""
            sender_password = ""
            smtp_server = ""
            smtp_port = ""
            config_ok = False
        #扫码登录bilibili
        try:#保下限
            print("开始扫码登录bilibili\n总共30秒扫码时间，过时未确认请后续手动补全")
            cookie_str=bilibili_saoma()
            if cookie_str != None:
                print("扫码登录成功！")
                print("cookie_str:",cookie_str)
            else:
                print("用户未扫码")
            
        except Exception as e:
            print(e)
            print("扫码登录b站出错，请手动在config.json内补全")
            cookie_str=""
            config_ok = False
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Cookie":cookie_str
        }
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
    return config_ok


def getVideos():
    return [
        i["param"]
        for i in requests.get(f"https://app.bilibili.com/x/v2/feed/index", headers=headers).json()["data"]["items"]
        if i.get("can_play", 0)
    ]


def getReplys(avid: str | int):
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
        if eval(rule):  # 一般来说, 只有rules.txt没有投毒, 就不会有安全问题
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


def bvid2avid(bvid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
        headers=headers
    ).json()
    return result["data"]["aid"]


if __name__ == "__main__":
    if not check_json():
        sys.exit()
    with open("./rules.txt", "r", encoding="utf-8") as f:
        rules = list(filter(lambda x: x and "eval" not in x and "exec" not in x, f.read().splitlines()))

    while True:
        try:
            for avid in getVideos():
                for reply in getReplys(avid):
                    processReply(reply)
                time.sleep(1.25)
        except (Exception, KeyboardInterrupt) as e:
            print("err", e)
            if isinstance(e, KeyboardInterrupt):
                break
