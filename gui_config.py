import sys
import time
from urllib.parse import quote_plus

import requests
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QComboBox, QPushButton, QCheckBox, QDialog, QHBoxLayout
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView


def getCookieFromGUI():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    result = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
        headers=headers
    ).json()

    qrcode_url = f"https://tool.oschina.net/action/qrcode/generate?data={quote_plus(result['data']['url'])}&output=image/png&error=M&type=0&margin=4&size=4"
    qrcode_key = result["data"]["qrcode_key"]

    # GUI 界面显示二维码，并等待登录
    app = QApplication(sys.argv)
    dialog = QRCodeLoginDialog(qrcode_url, qrcode_key)
    dialog.exec()

    if dialog.cookie_result:
        return dialog.cookie_result
    return None


class QRCodeLoginDialog(QDialog):
    def __init__(self, qrcode_url, qrcode_key):
        super().__init__()
        self.qrcode_url = qrcode_url
        self.qrcode_key = qrcode_key
        self.cookie_result = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("B站扫码登录")
        self.setWindowIcon(QIcon('./res/icon.ico'))
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        # 在GUI中嵌入网页来显示二维码
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(self.qrcode_url))
        layout.addWidget(self.web_view)

        # 登录按钮
        self.login_button = QPushButton("登录", self)
        self.login_button.clicked.connect(self.check_login_status)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def check_login_status(self):
        # 查询登录状态
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        params = {
            "qrcode_key": self.qrcode_key,
            "source": "main-fe-header",
        }
        result_cookie = requests.get(
            "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
            params=params,
            headers=headers
        )
        if result_cookie.json()["data"]["code"] == 0:
            cookie_dict = requests.utils.dict_from_cookiejar(result_cookie.cookies)
            self.cookie_result = "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])
            print("\n获取cookie成功")
            self.accept()  # 关闭对话框
        else:
            print("\n获取cookie失败:", result_cookie.json()["data"]["message"])
            time.sleep(0.5)


def get_email_config(smtps):
    app = QApplication(sys.argv)
    dialog = EmailConfigDialog(smtps)
    dialog.exec()

    return {
        "sender_email": dialog.sender_email_input.text(),
        "sender_password": dialog.sender_password_input.text(),
        "smtp_server": dialog.get_smtp_server(),
        "smtp_port": int(dialog.get_smtp_port()),
        "bili_report_api": dialog.bili_report_api_checkbox.isChecked(),
        "reply_limit": int(dialog.reply_limit_input.text()),
        "enable_gpt": dialog.enable_gpt_checkbox.isChecked(),
        "gpt_api_key": dialog.gpt_api_key_input.text(),
        "gpt_model": dialog.gpt_model_combo.currentText(),
        "enable_email": dialog.enable_email_checkbox.isChecked(),
        "enable_check_lv2avatarat": dialog.enable_check_lv2avatarat_checkbox.isChecked(),
        "enable_check_replyimage": dialog.enable_check_replyimage_checkbox.isChecked()
    }


class EmailConfigDialog(QDialog):
    def __init__(self, smtps):
        super().__init__()
        self.smtps = smtps  # 将传入的smtps字典存储为类变量
        self.initUI()

    def initUI(self):
        self.setWindowTitle('BiliClear 初始化配置')
        self.setWindowIcon(QIcon('./res/icon.ico'))
        self.setGeometry(100, 100, 400, 500)

        layout = QVBoxLayout()

        # 发送者邮箱
        self.sender_email_label = QLabel('发送者邮箱:')
        self.sender_email_input = QLineEdit(self)
        self.sender_email_input.textChanged.connect(self.auto_select_smtp_server)
        layout.addWidget(self.sender_email_label)
        layout.addWidget(self.sender_email_input)

        # 发送者密码
        self.sender_password_label = QLabel('发送者密码:')
        self.sender_password_input = QLineEdit(self)
        self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.sender_password_label)
        layout.addWidget(self.sender_password_input)

        # SMTP服务器（下拉框）
        self.smtp_server_label = QLabel('SMTP服务器:')
        self.smtp_server_combo = QComboBox(self)
        self.smtp_server_combo.addItems(list(self.smtps.keys()))
        self.smtp_server_combo.currentIndexChanged.connect(self.update_smtp_port)
        layout.addWidget(self.smtp_server_label)
        layout.addWidget(self.smtp_server_combo)

        # SMTP端口（下拉框）
        self.smtp_port_label = QLabel('SMTP端口:')
        self.smtp_port_combo = QComboBox(self)
        self.smtp_port_combo.currentIndexChanged.connect(self.handle_custom_port_selection)
        layout.addWidget(self.smtp_port_label)
        layout.addWidget(self.smtp_port_combo)

        # 额外输入框，当选择“其他”时出现
        self.custom_smtp_server_input = QLineEdit(self)
        self.custom_smtp_server_input.setPlaceholderText("请输入自定义SMTP服务器")
        self.custom_smtp_server_input.setVisible(False)  # 默认隐藏

        self.custom_smtp_port_input = QLineEdit(self)
        self.custom_smtp_port_input.setPlaceholderText("请输入自定义端口")
        self.custom_smtp_port_input.setVisible(False)  # 默认隐藏

        layout.addWidget(self.custom_smtp_server_input)
        layout.addWidget(self.custom_smtp_port_input)

        # B站举报API 使用
        self.bili_report_api_label = QLabel('是否额外使用B站评论举报API进行举报 (y/n):')
        self.bili_report_api_checkbox = QCheckBox('启用B站举报API')
        layout.addWidget(self.bili_report_api_label)
        layout.addWidget(self.bili_report_api_checkbox)

        # 回复限制数
        self.reply_limit_label = QLabel('回复限制数 (默认100):')
        self.reply_limit_input = QLineEdit(self)
        self.reply_limit_input.setText("100")  # 默认值设置为100
        layout.addWidget(self.reply_limit_label)
        layout.addWidget(self.reply_limit_input)

        # GPT相关配置（下拉框）
        self.enable_gpt_checkbox = QCheckBox('启用GPT')
        self.gpt_model_label = QLabel('选择GPT模型:')
        self.gpt_model_combo = QComboBox(self)
        gpt_models = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        self.gpt_model_combo.addItems(gpt_models)
        self.gpt_api_key_label = QLabel('GPT API Key:')
        self.gpt_api_key_input = QLineEdit(self)

        layout.addWidget(self.enable_gpt_checkbox)
        layout.addWidget(self.gpt_model_label)
        layout.addWidget(self.gpt_model_combo)
        layout.addWidget(self.gpt_api_key_label)
        layout.addWidget(self.gpt_api_key_input)

        # 其他配置
        self.enable_email_checkbox = QCheckBox('启用邮件报告')
        self.enable_check_lv2avatarat_checkbox = QCheckBox('启用检查Lv2头像')
        self.enable_check_replyimage_checkbox = QCheckBox('启用检查回复图片')

        layout.addWidget(self.enable_email_checkbox)
        layout.addWidget(self.enable_check_lv2avatarat_checkbox)
        layout.addWidget(self.enable_check_replyimage_checkbox)

        # 提交按钮
        self.submit_button = QPushButton('提交', self)
        self.submit_button.clicked.connect(self.accept)  # 点击后关闭对话框
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

        # 初始设置SMTP端口
        self.update_smtp_port()

    def auto_select_smtp_server(self):
        # 根据邮箱自动选择服务器
        email = self.sender_email_input.text()
        for domain in self.smtps:
            if domain in email:
                self.smtp_server_combo.setCurrentText(domain)
                break
        self.update_smtp_port()

    def update_smtp_port(self):
        # 获取选中的服务器
        selected_domain = self.smtp_server_combo.currentText()

        # 如果选择的是“其他”，显示自定义输入框
        if selected_domain == "其他":
            self.custom_smtp_server_input.setVisible(True)
            self.custom_smtp_port_input.setVisible(True)
            self.smtp_port_combo.clear()  # 清空端口下拉框
        else:
            self.custom_smtp_server_input.setVisible(False)
            self.custom_smtp_port_input.setVisible(False)
            smtp_info = self.smtps[selected_domain]
            self.smtp_port_combo.clear()
            self.smtp_port_combo.addItem(f"{smtp_info['port']}")  # 自动选择端口
            self.smtp_port_combo.addItem("其他")

    def handle_custom_port_selection(self):
        # 如果选择“其他”端口，显示自定义端口输入框
        if self.smtp_port_combo.currentText() == "其他":
            self.custom_smtp_port_input.setVisible(True)
        else:
            self.custom_smtp_port_input.setVisible(False)

    def get_smtp_server(self):
        if self.smtp_server_combo.currentText() == "其他":
            return self.custom_smtp_server_input.text()
        return self.smtp_server_combo.currentText()

    def get_smtp_port(self):
        if self.smtp_port_combo.currentText() == "其他":
            return self.custom_smtp_port_input.text()
        return self.smtp_port_combo.currentText()


if __name__ == '__main__':
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
        "其他": {"server": "", "port": 0}
    }

    # 获取登录的Cookie
    cookie = getCookieFromGUI()
    if cookie:
        print("Cookie:", cookie)

    # 调用get_email_config并传递smtps参数
    config = get_email_config(smtps)
    print(config)
