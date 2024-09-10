import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, \
    QCheckBox, QDialog
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote_plus
import requests


def get_email_config(smtps):
    app = QApplication(sys.argv)
    dialog = EmailConfigDialog(smtps)
    dialog.exec()

    # 返回从对话框获取到的数据
    return dialog.result_data()


class EmailConfigDialog(QDialog):
    def __init__(self, smtps):
        super().__init__()
        self.smtps = smtps  # 将传入的smtps字典存储为类变量
        self.cookie_result = None  # 保存登录后的cookie
        self.timer = None  # 定时器用于轮询扫码状态
        self.initUI()

    def initUI(self):
        self.setWindowTitle('BiliClear 初始化配置')
        self.setWindowIcon(QIcon('./res/icon.ico'))
        self.setGeometry(100, 100, 800, 500)  # 窗口调整为800宽度

        # 左侧表单布局
        form_layout = QVBoxLayout()

        # 发送者邮箱
        self.sender_email_label = QLabel('发送者邮箱:')
        self.sender_email_input = QLineEdit(self)
        self.sender_email_input.setPlaceholderText("可自动识别常见SMTP服务器信息，请先输入邮箱")
        self.sender_email_input.textChanged.connect(self.auto_select_smtp_server)
        form_layout.addWidget(self.sender_email_label)
        form_layout.addWidget(self.sender_email_input)

        # 发送者密码
        self.sender_password_label = QLabel('发送者密码:')
        self.sender_password_input = QLineEdit(self)
        self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.sender_password_label)
        form_layout.addWidget(self.sender_password_input)

        # SMTP服务器（下拉框）
        self.smtp_server_label = QLabel('SMTP服务器:')
        self.smtp_server_combo = QComboBox(self)
        self.smtp_server_combo.addItem("可自动识别")  # 当未识别时，显示这个
        self.smtp_server_combo.addItem("其他")  # 允许自定义
        self.smtp_server_combo.addItems(list(self.smtps.keys()))  # 加载所有预设服务器
        self.smtp_server_combo.currentIndexChanged.connect(self.update_smtp_port)
        form_layout.addWidget(self.smtp_server_label)
        form_layout.addWidget(self.smtp_server_combo)

        # SMTP端口（下拉框）
        self.smtp_port_label = QLabel('SMTP端口:')
        self.smtp_port_combo = QComboBox(self)
        self.smtp_port_combo.addItem("可自动识别")  # 当未识别时显示
        self.smtp_port_combo.addItem("其他")  # 允许自定义
        self.smtp_port_combo.currentIndexChanged.connect(self.handle_custom_port_selection)
        form_layout.addWidget(self.smtp_port_label)
        form_layout.addWidget(self.smtp_port_combo)

        # 额外输入框，当选择“其他”时出现
        self.custom_smtp_server_input = QLineEdit(self)
        self.custom_smtp_server_input.setPlaceholderText("请输入自定义SMTP服务器")
        self.custom_smtp_server_input.setVisible(False)  # 默认隐藏

        self.custom_smtp_port_input = QLineEdit(self)
        self.custom_smtp_port_input.setPlaceholderText("请输入自定义端口")
        self.custom_smtp_port_input.setVisible(False)  # 默认隐藏

        form_layout.addWidget(self.custom_smtp_server_input)
        form_layout.addWidget(self.custom_smtp_port_input)

        # B站举报API 使用
        self.bili_report_api_label = QLabel('是否使用B站评论举报API进行举报:')
        self.bili_report_api_checkbox = QCheckBox('启用B站举报API')
        self.bili_report_api_checkbox.setChecked(True)
        form_layout.addWidget(self.bili_report_api_label)
        form_layout.addWidget(self.bili_report_api_checkbox)

        # 回复限制数
        self.reply_limit_label = QLabel('回复限制数 (默认100):')
        self.reply_limit_input = QLineEdit(self)
        self.reply_limit_input.setText("100")  # 默认值设置为100
        form_layout.addWidget(self.reply_limit_label)
        form_layout.addWidget(self.reply_limit_input)

        # GPT相关配置（下拉框）
        self.enable_gpt_checkbox = QCheckBox('启用GPT')
        self.gpt_model_label = QLabel('选择GPT模型:')
        self.gpt_model_combo = QComboBox(self)
        gpt_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo", "gpt-4"]
        self.gpt_model_combo.addItems(gpt_models)
        self.gpt_api_key_label = QLabel('GPT API Key:')
        self.gpt_api_key_input = QLineEdit(self)

        form_layout.addWidget(self.enable_gpt_checkbox)
        form_layout.addWidget(self.gpt_model_label)
        form_layout.addWidget(self.gpt_model_combo)
        form_layout.addWidget(self.gpt_api_key_label)
        form_layout.addWidget(self.gpt_api_key_input)

        # 其他配置
        self.enable_email_checkbox = QCheckBox('启用邮件报告（图一乐，目前B站取消了邮箱举报功能）')
        self.enable_check_lv2avatarat_checkbox = QCheckBox('启用检查Lv2头像')
        self.enable_check_replyimage_checkbox = QCheckBox('启用检查回复图片')

        # 默认启用选项
        self.enable_check_lv2avatarat_checkbox.setChecked(True)
        self.enable_check_replyimage_checkbox.setChecked(True)

        form_layout.addWidget(self.enable_email_checkbox)
        form_layout.addWidget(self.enable_check_lv2avatarat_checkbox)
        form_layout.addWidget(self.enable_check_replyimage_checkbox)

        # 提交按钮（初始为灰色）
        self.submit_button = QPushButton('提交', self)
        self.submit_button.setEnabled(False)  # 初始为不可用
        self.submit_button.clicked.connect(self.submit_form)  # 绑定提交按钮的事件
        form_layout.addWidget(self.submit_button)

        # 右侧二维码布局
        qr_layout = QVBoxLayout()
        self.qr_label = QLabel('请使用哔哩哔哩扫码获取cookie', self)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中显示
        qr_layout.addWidget(self.qr_label)

        self.qr_view = QWebEngineView(self)
        self.qr_view.setMinimumSize(300, 300)  # 设置二维码的大小
        qr_layout.addWidget(self.qr_view)

        self.cookie_status_label = QLabel('Cookie未获取', self)
        self.cookie_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中显示
        qr_layout.addWidget(self.cookie_status_label)

        # 获取二维码链接并加载
        self.load_qr_code()

        # 主布局
        main_layout = QHBoxLayout()  # 左右布局
        main_layout.addLayout(form_layout)  # 左侧为表单
        main_layout.addLayout(qr_layout)  # 右侧为二维码

        self.setLayout(main_layout)

        # 启动定时器，每2秒检查一次扫码状态
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_login_status)
        self.timer.start(2000)  # 每2000毫秒（2秒）检查一次状态

    def load_qr_code(self):
        # 获取B站二维码登录的链接并加载二维码
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        result = requests.get("https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
                              headers=headers).json()

        if result["code"] == 0:
            qrcode_url = f"https://tool.oschina.net/action/qrcode/generate?data={quote_plus(result['data']['url'])}&output=image/png&error=M&type=0&margin=4&size=4"
            self.qr_view.setUrl(QUrl(qrcode_url))
            self.qrcode_key = result["data"]["qrcode_key"]
        else:
            print("二维码生成失败")

    def check_login_status(self):
        # 查询登录状态
        headers = {
            "User-Agent": "Mozilla/5.0"
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

        result_data = result_cookie.json()["data"]

        if result_data["code"] == 0:
            cookie_dict = requests.utils.dict_from_cookiejar(result_cookie.cookies)
            self.cookie_result = "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])
            self.cookie_status_label.setText("Cookie获取成功")
            self.submit_button.setEnabled(True)  # Cookie成功获取后，激活提交按钮
            print("\n获取cookie成功")
            self.timer.stop()  # 成功后停止定时器
        elif result_data["code"] == 86038:  # 当二维码失效时
            self.cookie_status_label.setText("二维码已失效，正在重新获取...")
            self.load_qr_code()  # 自动重新获取二维码
        else:
            self.cookie_status_label.setText("Cookie未获取，请继续扫码")
            print("\n获取cookie失败:", result_data["message"])

    def submit_form(self):
        """处理提交事件并关闭窗口"""
        # 在这里可以收集所有的表单数据并返回
        self.accept()  # 关闭窗口

    def result_data(self):
        """返回提交时收集到的所有表单数据"""
        return {
            "sender_email": self.sender_email_input.text(),
            "sender_password": self.sender_password_input.text(),
            "smtp_server": self.get_smtp_server(),
            "smtp_port": int(self.get_smtp_port()),
            "bili_report_api": self.bili_report_api_checkbox.isChecked(),
            "reply_limit": int(self.reply_limit_input.text()),
            "enable_gpt": self.enable_gpt_checkbox.isChecked(),
            "gpt_api_key": self.gpt_api_key_input.text(),
            "gpt_model": self.gpt_model_combo.currentText(),
            "enable_email": self.enable_email_checkbox.isChecked(),
            "enable_check_lv2avatarat": self.enable_check_lv2avatarat_checkbox.isChecked(),
            "enable_check_replyimage": self.enable_check_replyimage_checkbox.isChecked(),
            "cookie": self.cookie_result  # 返回获取到的cookie
        }

    def auto_select_smtp_server(self):
        # 自动根据邮箱识别服务器
        email = self.sender_email_input.text()
        if email and "@" in email:
            domain = email.split('@')[1]
            domain_key = f"@{domain}"
            if domain_key in self.smtps:
                # 自动设置服务器和端口
                self.smtp_server_combo.setCurrentText(domain_key)
                smtp_info = self.smtps[domain_key]
                self.smtp_port_combo.setCurrentText(str(smtp_info['port']))
            else:
                # 如果未识别到，重置为可自动识别
                self.smtp_server_combo.setCurrentText("可自动识别")
                self.smtp_port_combo.setCurrentText("可自动识别")

    def update_smtp_port(self):
        # 根据服务器选择更新端口，允许自定义
        selected_server = self.smtp_server_combo.currentText()

        if selected_server == "其他":
            # 显示自定义服务器和端口输入框
            self.custom_smtp_server_input.setVisible(True)
            self.custom_smtp_port_input.setVisible(True)
            self.smtp_port_combo.clear()  # 清空端口下拉框
            self.smtp_port_combo.addItem("其他")
        elif selected_server in self.smtps:
            # 隐藏自定义输入框
            self.custom_smtp_server_input.setVisible(False)
            self.custom_smtp_port_input.setVisible(False)
            # 根据选择的服务器自动填充端口
            smtp_info = self.smtps.get(selected_server, {"port": ""})
            self.smtp_port_combo.clear()
            if smtp_info["port"]:
                self.smtp_port_combo.addItem(str(smtp_info["port"]))
            self.smtp_port_combo.addItem("其他")
        else:
            # 未选择识别的服务器
            self.smtp_port_combo.setCurrentText("可自动识别")

    def handle_custom_port_selection(self):
        # 选择自定义端口时，显示输入框
        if self.smtp_port_combo.currentText() == "其他":
            self.custom_smtp_port_input.setVisible(True)
        else:
            self.custom_smtp_port_input.setVisible(False)

    def get_smtp_server(self):
        # 返回自定义服务器或选择的服务器
        if self.smtp_server_combo.currentText() == "其他":
            return self.custom_smtp_server_input.text()
        return self.smtp_server_combo.currentText()

    def get_smtp_port(self):
        # 返回自定义端口或选择的端口
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
        "@qq.com": {"server": "smtp.qq.com", "port": 465}
    }

    # 调用get_email_config并传递smtps参数
    config = get_email_config(smtps)
    print(config)
