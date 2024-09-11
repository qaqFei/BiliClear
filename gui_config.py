import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, \
    QCheckBox, QDialog, QLineEdit
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote_plus
import requests


def get_email_config():
    app = QApplication(sys.argv)
    dialog = EmailConfigDialog()
    dialog.exec()

    # 返回从对话框获取到的数据
    return dialog.result_data()


class EmailConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.cookie_result = None  # 保存登录后的cookie
        self.timer = None  # 定时器用于轮询扫码状态
        self.initUI()

    def initUI(self):
        self.setWindowTitle('BiliClear 初始化配置')
        self.setWindowIcon(QIcon('./res/icon.ico'))

        # 将窗口大小缩小为更适合当前选项量的尺寸
        self.setGeometry(100, 100, 600, 400)  # 窗口调整为600宽，400高

        # 表单布局
        form_layout = QVBoxLayout()

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
        self.enable_check_lv2avatarat_checkbox = QCheckBox('启用检查Lv2头像')
        self.enable_check_replyimage_checkbox = QCheckBox('启用检查回复图片')

        # 默认启用选项
        self.enable_check_lv2avatarat_checkbox.setChecked(True)
        self.enable_check_replyimage_checkbox.setChecked(True)

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
        self.qr_view.setMinimumSize(250, 250)  # 设置二维码的大小
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
            "bili_report_api": self.bili_report_api_checkbox.isChecked(),
            "reply_limit": int(self.reply_limit_input.text()),
            "enable_gpt": self.enable_gpt_checkbox.isChecked(),
            "gpt_api_key": self.gpt_api_key_input.text(),
            "gpt_model": self.gpt_model_combo.currentText(),
            "enable_check_lv2avatarat": self.enable_check_lv2avatarat_checkbox.isChecked(),
            "enable_check_replyimage": self.enable_check_replyimage_checkbox.isChecked(),
            "cookie": self.cookie_result  # 返回获取到的cookie
        }


if __name__ == '__main__':
    config = get_email_config()
    print(config)
