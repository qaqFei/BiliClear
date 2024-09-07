import smtplib
import json
import time
import sys
import re
import requests
import biliauth
import syscmds
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
from os import chdir
from os.path import exists, dirname, abspath
from getpass import getpass

# 修改 sys.excepthook
sys.excepthook = (
    lambda *args: [print("^C"), sys.exit()]
    if KeyboardInterrupt in args[0].mro()
    else sys.__excepthook__(*args)
)

selfdir = dirname(sys.argv[0])
if selfdir == "":
    selfdir = abspath(".")
chdir(selfdir)


def saveConfig() -> None:
    """保存当前配置到 config.json 文件。"""
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
                    "reply_limit": reply_limit,
                },
                indent=4,
                ensure_ascii=False,
            )
        )


def getCsrf(cookie: str) -> str:
    """从 Bilibili Cookie 中提取 CSRF token。"""
    try:
        return re.findall(r"bili_jct=(.*?);", cookie)[0]
    except IndexError as e:
        print("Bilibili Cookie 格式错误, 重启 BiliClear 或删除 config.json")
        raise SystemExit from e


def checkSmtpPassword() -> bool:
    """检查 SMTP 密码是否正确。"""
    try:
        smtp_con = smtplib.SMTP_SSL(smtp_server, smtp_port)
        smtp_con.login(sender_email, sender_password)
        smtp_con.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        return False


def getCookieFromUser() -> str:
    """获取用户输入的 Bilibili Cookie，如果用户选择二维码登录则调用 biliauth 模块进行登录。"""
    if "n" in input("\n是否使用二维码登录B站, 默认为是(y/n): ").lower():
        return getpass("请输入 Bilibili cookie: ")
    else:
        return biliauth.bilibiliAuth()


def checkCookie() -> bool:
    """检查 Bilibili Cookie 是否有效。"""
    result = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/cookie/info",
        headers=headers,
        data={"csrf": csrf},
    ).json()
    return result["code"] == 0 and not result.get("data", {}).get("refresh", True)


predefined_smtp_options = {
    "1": {"server": "smtp.aliyun.com", "port": 465},
    "2": {"server": "smtp.gmail.com", "port": 465},
    "3": {"server": "smtp.sina.com.cn", "port": 465},
    "4": {"server": "smtp.tom.com", "port": 465},
    "5": {"server": "smtp.163.com", "port": 465},
    "6": {"server": "smtp.126.com", "port": 465},
    "7": {"server": "smtp.mail.yahoo.com", "port": 465},
    "8": {"server": "smtp.qq.com", "port": 465},
    "9": {"server": "smtp.sohu.com", "port": 465},
    "10": {"server": "smtp.live.com", "port": 587},
    "11": {"server": "smtp.office365.com", "port": 587},
    "12": {"server": "smtp.qq.com", "port": 465},
    "13": {"server": "smtp.feishu.cn", "port": 465},
}


def get_smtp_config():
    print("\nSMTP 服务器选项:")
    for k, v in predefined_smtp_options.items():
        print(f"    {k}.SMTP 服务器 = {v['server']}, port = {v['port']}")

    choice = input("\n选择 SMTP 服务器 (输入数字，自定义SMTP服务器请输入0): ")
    if choice == "0":
        server = input("自定义 SMTP 服务器: ")
        port = int(input("自定义 SMTP 端口: "))
    elif option := predefined_smtp_options.get(choice):
        server = option["server"]
        port = option["port"]
    else:
        print("无效选项, 退出中...")
        raise SystemExit

    return server, port


if not exists("./config.json"):
    sender_email = input("举报者邮箱: ")
    sender_password = getpass("邮箱授权密码: ")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Cookie": getCookieFromUser(),
    }

    csrf = getCsrf(headers["Cookie"])

    smtp_server, smtp_port = get_smtp_config()

    bili_report_api = (
        "y" in input("是否额外使用 B 站评论举报 API 进行举报, 默认为否(y/n): ").lower()
    )
    reply_limit = 100
else:
    with open("./config.json", encoding="utf-8") as f:
        try:
            config = json.load(f)
            sender_email = config["sender_email"]
            sender_password = config["sender_password"]
            headers = config["headers"]
            smtp_server = config["smtp_server"]
            smtp_port = config["smtp_port"]
            bili_report_api = config.get("bili_report_api", False)
            csrf = config.get("csrf", getCsrf(headers["Cookie"]))
            reply_limit = config.get("reply_limit", 100)
        except Exception as e:
            print("加载 config.json 失败, 请删除或修改 config.json, 错误:", repr(e))
            print("如果你之前更新过 BiliClear, 请删除 config.json 并重新运行")
            print("请按回车键退出...")
            syscmds.pause()
            raise SystemExit from e


if not checkCookie():
    print("Bilibili cookie 已过期或失效, 请重新登录")
    headers["Cookie"] = getCookieFromUser()
    csrf = getCsrf(headers["Cookie"])

try:
    saveConfig()
except Exception:
    print("警告: 保存 config.json 失败")

if not checkSmtpPassword():
    print("警告: SMTP 密钥不正确, 请检查 SMTP 密钥")


# 定义规则检查器类
class RuleChecker:
    def __init__(self, rules: list):
        self.rules = rules

    def _parse_rule(self, rule: str) -> str | None:
        """解析规则字符串，将其转换为条件表达式。"""
        # 转换规则字符串为可以执行的表达式
        try:
            # 替换一些特殊字符，确保规则的安全性
            rule = rule.replace(" and ", " and ").replace(" or ", " or ")
            # 验证规则是否符合预期的表达式格式
            if re.match(r'^[\w\s"\'!=<>().]+$', rule):
                return rule
        except Exception:
            return None

    def is_porn(self, text: str) -> tuple[bool, str | None]:
        """检查文本是否符合色情内容规则。"""
        for rule in self.rules:
            parsed_rule = self._parse_rule(rule)
            if parsed_rule is not None:
                # 使用局部上下文执行规则检查
                local_context = {"text": text}
                try:
                    if eval(
                        parsed_rule, {}, local_context
                    ):  # 使用 eval 安全执行解析后的表达式
                        return True, rule
                except Exception as e:
                    print(f"规则解析错误: {rule}, 错误: {e}")
        return False, None


def load_rules(file_path: str) -> list:
    "从规则文件中加载规则"
    with open(file_path, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and "eval" not in line and "exec" not in line
        ]


# 实例化规则检查器
rules = load_rules("./rules.txt")
rule_checker = RuleChecker(rules)


print("加载完成, BiliClear 将在 2.0s 后开始运行")
time.sleep(2.0)
syscmds.clearScreen()


def getVideos() -> list[str]:
    """获取推荐视频的 AVID 列表。"""
    return [
        i["param"]
        for i in requests.get(
            "https://app.bilibili.com/x/v2/feed/index", headers=headers
        ).json()["data"]["items"]
        if i.get("can_play", 0)
    ]


def getReplys(avid: str | int) -> list[dict]:
    """获取指定视频的评论列表。"""
    maxNum = reply_limit
    page = 1
    replies = []
    while page * 20 <= maxNum:
        time.sleep(0.4)
        result = requests.get(
            f"https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&nohot=1&pn={page}&ps=20",
            headers=headers,
        ).json()
        try:
            if not result["data"]["replies"]:
                break
            replies += result["data"]["replies"]
        except Exception:
            break
        page += 1
    return replies


def req_bili_report_api(data: dict[str, str | int]) -> None:
    """调用 Bilibili 举报 API 进行举报。"""
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
        print("B站举报API调用失败, 返回体：", result)
    elif result_code == 0:
        print("Bilibili 举报 API 调用成功")
    elif result_code == 12019:
        print("举报过于频繁, 等待 60s")
        time.sleep(60)
        return req_bili_report_api(data)


def report(data: dict, r: str) -> None:
    """生成并发送举报邮件。"""
    report_text = f"""
违规用户UID：{data["mid"]}
违规类型：色情
违规信息发布形式：评论, (动态)
问题描述：该评论疑似发布色情信息，破坏了 B 站和互联网的和谐环境
诉求：移除违规内容，封禁账号

评论数据内容(B站API返回, x/v2/reply):
`
{json.dumps(data, ensure_ascii=False, indent=4)}
`

(此举报信息自动生成, 可能会存在误报)
评论内容匹配到的规则: {r}
"""
    print("\n违规评论:", repr(data["content"]["message"]))
    print("规则:", r)

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


def processReply(reply: dict) -> None:
    """处理回复，检查是否包含色情内容并进行举报。"""
    global replyCount, pornReplyCount, checkedReplies

    replyCount += 1
    isp, r = rule_checker.is_porn(reply["content"]["message"])
    if isp and r is not None:
        pornReplyCount += 1
        report(reply, r)
    checkedReplies.insert(0, (reply["rpid"], reply["content"]["message"], time.time()))
    checkedReplies = checkedReplies[:1500]


def setMethod() -> None:
    """设置方法选择。"""
    global method
    method = None
    method_choices = {"1": "自动获取推荐视频评论", "2": "获取指定视频评论"}

    while method not in method_choices.keys():
        if method is not None:
            print("输入错误")

        print("tip: 请定期检查 bilibili cookie 是否过期 (BiliClear 启动时会自动检查)\n")
        for k, v in method_choices.items():
            print(f"{k}. {v}")
        method = input("选择: ")
        syscmds.clearScreen()


def bvid2avid(bvid: str) -> str:
    """将 BV 号转换为 AV 号。"""
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=headers
    ).json()
    return result["data"]["aid"]


videoCount = 0
replyCount = 0
pornReplyCount = 0
waitRiskControl_TimeRemaining = float("nan")
waitingRiskControl = False
checkedVideos: list[tuple[str, float]] = []
checkedReplies: list[tuple[str, str, float]] = []


def _checkVideo(avid: str | int) -> None:
    """检查指定视频的评论。"""
    for reply in getReplys(avid):
        processReply(reply)


def checkNewVideos() -> None:
    """检查新一轮推荐视频的评论。"""
    global videoCount, replyCount, pornReplyCount, checkedVideos

    print(("\n" if videoCount != 0 else "") + "开始检查新一轮推荐视频...")
    print(f"已检查视频: {videoCount}")
    print(f"已检查评论: {replyCount}")
    print(
        f"已举报评论: {pornReplyCount} 评论违规率: {((pornReplyCount / replyCount * 100) if replyCount != 0 else 0.0):.5f}%"
    )
    print()  # next line

    for avid in getVideos():
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] 正在检查视频: av{avid}")
        _checkVideo(avid)
        videoCount += 1
        checkedVideos.insert(0, (avid, time.time()))
        checkedVideos = checkedVideos[:1500]

    time.sleep(1.25)


def checkVideo(bvid: str) -> None:
    """检查指定 BV 号的视频评论。"""
    global videoCount, checkedVideos

    avid = bvid2avid(bvid)
    _checkVideo(avid)
    videoCount += 1
    checkedVideos.insert(0, (avid, time.time()))
    checkedVideos = checkedVideos[:1500]
    time.sleep(1.25)


def waitRiskControl(output: bool = True) -> None:
    """等待风控解除。"""
    global waitRiskControl_TimeRemaining, waitingRiskControl

    stopSt = time.time()
    stopMinute = 10
    waitRiskControl_TimeRemaining = 60 * stopMinute
    waitingRiskControl = True
    print(f"警告!!! B站API返回了非JSON格式数据, 大概率被风控, 暂停{stopMinute}分钟...")
    while time.time() - stopSt < 60 * stopMinute:
        waitRiskControl_TimeRemaining = 60 * stopMinute - (time.time() - stopSt)
        if output:
            print(
                f"由于可能被风控, BiliClear 暂停 {stopMinute} 分钟, 还剩余: {waitRiskControl_TimeRemaining:.2f}s"
            )
            time.sleep(1.5)
        else:
            time.sleep(0.005)
    waitingRiskControl = False


if __name__ == "__main__":
    setMethod()
    while True:
        try:
            match method:
                case "1":
                    checkNewVideos()
                case "2":
                    checkVideo(input("\n输入视频 bvid: "))
                case _:
                    print("链接格式错误")
        except Exception as e:
            print("错误", repr(e))
            if isinstance(e, json.JSONDecodeError):
                waitRiskControl()
