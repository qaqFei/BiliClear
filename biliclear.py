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
import biliauth


class BiliClear:
    def __init__(self):
        self.selfdir = dirname(sys.argv[0])
        if self.selfdir == "":
            self.selfdir = abspath(".")
        chdir(self.selfdir)

        self.headers = {}
        self.rules = []
        self.sender_email = ""
        self.sender_password = ""
        self.smtp_server = ""
        self.smtp_port = ""
        self.csrf = ""
        self.bili_report_api = False

        self.load_config()
        self.load_rules()

    def load_config(self):
        """加载配置文件或创建新的配置"""
        if not exists("./config.json"):
            self.sender_email = input("Report sender email: ")
            self.sender_password = getpass("Report sender password: ")
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Cookie": ""
            }

            match (input("\n是否使用二维码登录B站, 默认为是(y/n): ").lower() + " ")[0]:
                case "n":
                    self.headers["Cookie"] = getpass("Bilibili cookie: ")
                case _:
                    self.headers["Cookie"] = biliauth.bilibiliAuth()

            self.csrf = self.get_csrf(self.headers["Cookie"])

            print("\nSMTP servers:")
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

            for k, v in smtps.items():
                print(f"    {k}: server = {v['server']}, port = {v['port']}")

            self.smtp_server = input("\nSMTP server: ")
            self.smtp_port = int(input("SMTP port: "))
            self.bili_report_api = "y" in input("是否额外使用B站评论举报API进行举报, 默认为否(y/n): ").lower()

            self.save_config()
        else:
            with open("./config.json", "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                    self.sender_email = config["sender_email"]
                    self.sender_password = config["sender_password"]
                    self.headers = config["headers"]
                    self.smtp_server = config["smtp_server"]
                    self.smtp_port = config["smtp_port"]
                    self.bili_report_api = config.get("bili_report_api", False)
                    self.csrf = config.get("csrf", self.get_csrf(self.headers["Cookie"]))
                except Exception:
                    print("load config.json failed, please delete it or fix it")
                    raise SystemExit

    def save_config(self):
        """保存配置文件"""
        with open("./config.json", "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "sender_email": self.sender_email,
                "sender_password": self.sender_password,
                "headers": self.headers,
                "smtp_server": self.smtp_server,
                "smtp_port": self.smtp_port,
                "bili_report_api": self.bili_report_api,
                "csrf": self.csrf
            }, indent=4, ensure_ascii=False))

    def load_rules(self):
        """加载规则文件"""
        with open("./rules.txt", "r", encoding="utf-8") as f:
            self.rules = list(filter(lambda x: x and "eval" not in x and "exec" not in x, f.read().splitlines()))

    def get_csrf(self, cookie):
        """获取 csrf 值"""
        return re.findall(r"bili_jct=(.*?);", cookie)[0]

    def get_videos(self):
        """获取推荐视频"""
        return [
            i["param"]
            for i in
            requests.get(f"https://app.bilibili.com/x/v2/feed/index", headers=self.headers).json()["data"]["items"]
            if i.get("can_play", 0)
        ]

    def get_replys(self, avid):
        """获取视频评论"""
        max_num = 100
        page = 1
        replies = []
        while page * 20 <= max_num:
            result = requests.get(
                f"https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&nohot=1&pn={page}&ps=20",
                headers=self.headers
            ).json()
            try:
                replies += result["data"]["replies"]
            except Exception:
                break
            page += 1
        return replies

    def is_porn(self, text):
        """判断评论是否违规"""
        for rule in self.rules:
            if eval(rule):
                return True, rule
        return False, None

    def req_bili_report_api(self, data):
        """通过 B 站举报 API 进行举报"""
        result = requests.post(
            "https://api.bilibili.com/x/v2/reply/report",
            headers=self.headers,
            data={
                "type": 1,
                "oid": data["oid"],
                "rpid": data["rpid"],
                "reason": 2,
                "csrf": self.csrf
            }
        ).json()
        result_code = result["code"]
        time.sleep(2.0)
        if result_code not in (0, 12019):
            print("b站举报API调用失败, 返回体：", result)
        elif result_code == 0:
            print("Bilibili举报API调用成功")
        elif result_code == 12019:
            print("举报过于频繁, 等待60s")
            time.sleep(60)
            return self.req_bili_report_api(data)

    def report(self, data, r):
        """发送举报邮件并调用举报 API"""
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
        print("违规评论:", repr(data["content"]["message"]))
        print("rule:", r)

        msg = MIMEText(report_text, "plain", "utf-8")
        msg["From"] = Header("Report", "utf-8")
        msg["To"] = Header("Bilibili", "utf-8")
        msg["Subject"] = Header("违规内容举报", "utf-8")
        smtp_con = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        smtp_con.login(self.sender_email, self.sender_password)
        smtp_con.sendmail(self.sender_email, ["help@bilibili.com"], msg.as_string())
        smtp_con.quit()

        if self.bili_report_api:
            self.req_bili_report_api(data)

        print()  # Next line

    def process_reply(self, reply):
        """处理单条评论"""
        isp, rule = self.is_porn(reply["content"]["message"])
        if isp:
            self.report(reply, rule)

    def bvid_to_avid(self, bvid):
        """通过 bvid 获取 avid"""
        result = requests.get(
            f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
            headers=self.headers
        ).json()
        return result["data"]["aid"]


if __name__ == "__main__":
    biliclear = BiliClear()
    while True:
        print("\n选择操作:")
        print("1. 自动获取推荐视频评论")
        print("2. 手动输入 bvid 获取视频评论")
        choice = input("选择: ")

        if choice == "1":
            # 自动获取推荐视频并处理评论
            videos = biliclear.get_videos()
            for avid in videos:
                replies = biliclear.get_replys(avid)
                for reply in replies:
                    biliclear.process_reply(reply)
        elif choice == "2":
            # 手动输入 bvid 获取视频评论
            bvid = input("请输入 bvid: ")
            avid = biliclear.bvid_to_avid(bvid)
            replies = biliclear.get_replys(avid)
            for reply in replies:
                biliclear.process_reply(reply)
        else:
            print("无效选择，请重新输入。")
