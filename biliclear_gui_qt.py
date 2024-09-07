import sys
import threading
import queue
import webbrowser
import json
import requests
from os.path import exists
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QAbstractItemView,
                             QDialog, QFormLayout, QCheckBox, QSpinBox, QMessageBox)

import biliclear  # 引入主程序中的功能

CONFIG_FILE = './config.json'


def load_config():
    """加载配置文件"""
    if exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return None


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


class SettingsDialog(QDialog):
    """配置对话框，允许用户设置 GPT 和其他配置"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('配置设置')

        layout = QFormLayout()

        # GPT 设置
        self.enable_gpt_checkbox = QCheckBox('启用 GPT')
        self.enable_gpt_checkbox.setChecked(self.config.get('enable_gpt', False))
        layout.addRow('启用 GPT:', self.enable_gpt_checkbox)

        self.gpt_apibase_input = QLineEdit(self.config.get('gpt_apibase', 'https://api.openai.com/v1'))
        layout.addRow('GPT API Base:', self.gpt_apibase_input)

        self.gpt_apikey_input = QLineEdit(self.config.get('gpt_apikey', ''))
        layout.addRow('GPT API Key:', self.gpt_apikey_input)

        self.gpt_model_input = QLineEdit(self.config.get('gpt_model', 'gpt-4o-mini'))
        layout.addRow('GPT Model:', self.gpt_model_input)

        # Email 设置
        self.enable_email_checkbox = QCheckBox('启用 Email 报告')
        self.enable_email_checkbox.setChecked(self.config.get('enable_email', True))
        layout.addRow('启用 Email 报告:', self.enable_email_checkbox)

        self.sender_email_input = QLineEdit(self.config.get('sender_email', ''))
        layout.addRow('发送者 Email:', self.sender_email_input)

        self.sender_password_input = QLineEdit(self.config.get('sender_password', ''))
        self.sender_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow('Email 密码:', self.sender_password_input)

        # 其他设置
        self.reply_limit_input = QSpinBox()
        self.reply_limit_input.setMinimum(10)
        self.reply_limit_input.setMaximum(1000)
        self.reply_limit_input.setValue(self.config.get('reply_limit', 40))
        layout.addRow('评论获取上限:', self.reply_limit_input)

        self.enable_check_lv2_checkbox = QCheckBox('启用 Lv2 头像检测')
        self.enable_check_lv2_checkbox.setChecked(self.config.get('enable_check_lv2avatarat', False))
        layout.addRow('启用 Lv2 头像检测:', self.enable_check_lv2_checkbox)

        # 保存按钮
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def save_settings(self):
        """保存设置并写入配置文件"""
        self.config['enable_gpt'] = self.enable_gpt_checkbox.isChecked()
        self.config['gpt_apibase'] = self.gpt_apibase_input.text()
        self.config['gpt_apikey'] = self.gpt_apikey_input.text()
        self.config['gpt_model'] = self.gpt_model_input.text()
        self.config['enable_email'] = self.enable_email_checkbox.isChecked()
        self.config['sender_email'] = self.sender_email_input.text()
        self.config['sender_password'] = self.sender_password_input.text()
        self.config['reply_limit'] = self.reply_limit_input.value()
        self.config['enable_check_lv2avatarat'] = self.enable_check_lv2_checkbox.isChecked()

        save_config(self.config)
        QMessageBox.information(self, '设置已保存', '配置已成功保存！')
        self.close()


class CommentProcessorThread(threading.Thread):
    """后台线程，用于处理评论"""
    def __init__(self, avids=None, result_queue=None, log_queue=None, bvid=None, enable_gpt=False):
        super().__init__()
        self.avids = avids
        self.result_queue = result_queue
        self.log_queue = log_queue
        self.bvid = bvid
        self.enable_gpt = enable_gpt

    def run(self):
        if self.avids is None:
            self.avids = biliclear.getVideos()

        for avid in self.avids:
            replies = biliclear.getReplys(avid)
            bvid = self.bvid if self.bvid else f"av{avid}"
            self.log_queue.put(f"开始处理视频: {bvid}")
            biliclear.videoCount += 1  # 更新视频计数

            for reply in replies:
                isp, rule = biliclear.processReply(reply)  # 处理评论
                biliclear.replyCount += 1  # 更新评论计数
                if isp:
                    biliclear.pornReplyCount += 1  # 如果评论违规，更新违规计数
                self.result_queue.put((reply, isp, rule))  # 将评论和检测结果发送到主线程
                self.log_queue.put(f"处理评论: {reply['content']['message']}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 加载配置
        self.config = load_config()
        if not self.config:
            QMessageBox.critical(self, '错误', '未找到配置文件，程序将退出。')
            sys.exit(1)

        # 创建线程安全队列用于传递数据
        self.result_queue = queue.Queue()
        self.log_queue = queue.Queue()

        self.initUI()

        # 定时器，每隔 100ms 检查一次队列的更新，更新 UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)

        self.current_bvid = None
        self.processor_thread = None

    def initUI(self):
        self.setWindowTitle('Bilibili 自动评论监控')
        self.setGeometry(300, 300, 1200, 600)
        self.setWindowIcon(QIcon('icon.ico'))  # 设置窗口图标为根目录下的 icon.ico

        main_layout = QVBoxLayout()

        # 统计部分显示
        self.stats_label = QLabel(self.get_stats_text())  # 显示统计信息
        main_layout.addWidget(self.stats_label)

        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("请输入 B 站视频的 bvid")
        main_layout.addWidget(self.input_box)

        self.comment_table = QTableWidget(0, 2, self)
        self.comment_table.setHorizontalHeaderLabels(["评论内容", "违规状态"])
        self.comment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.comment_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.comment_table)

        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        self.start_btn = QPushButton('获取视频评论', self)
        self.start_btn.clicked.connect(self.start_processing)
        main_layout.addWidget(self.start_btn)

        self.auto_btn = QPushButton('自动获取推荐视频评论', self)
        self.auto_btn.clicked.connect(self.auto_get_videos)
        main_layout.addWidget(self.auto_btn)

        self.settings_btn = QPushButton('配置设置', self)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        main_layout.addWidget(self.settings_btn)

        self.setLayout(main_layout)
        self.show()

    def get_stats_text(self):
        """生成统计文本"""
        violation_rate = 0
        if biliclear.replyCount > 0:
            violation_rate = (biliclear.pornReplyCount / biliclear.replyCount) * 100

        return (f"BiliClear 数据统计\n"
                f"已检查视频: {biliclear.videoCount}\n"
                f"已检查评论: {biliclear.replyCount}\n"
                f"违规评论: {biliclear.pornReplyCount}\n"
                f"评论违规率: {violation_rate:.5f}%\n"
                f"B站API风控中: {biliclear.waitingRiskControl}")

    def update_stats_label(self):
        """更新统计显示"""
        self.stats_label.setText(self.get_stats_text())

    def start_processing(self):
        """手动获取视频的评论并处理"""
        bvid = self.input_box.text().strip()

        if not bvid:
            self.log_message("请输入有效的视频 bvid")
            return

        if not bvid.startswith("BV") or len(bvid) < 6:
            self.log_message("请输入有效的 Bilibili 视频 bvid (例如：BVxxxxxxxx)")
            return

        try:
            avid = self.get_avid_from_bvid(bvid)

            if not avid:
                self.log_message("获取 avid 失败，请检查 bvid 是否正确")
                return

            self.current_bvid = bvid
            self.start_comment_processing([avid])

        except Exception as e:
            self.log_message(f"发生错误: {str(e)}")

    def get_avid_from_bvid(self, bvid):
        """通过 Bilibili API 将 bvid 转换为 avid"""
        try:
            url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                avid = data['data']['aid']
                return avid
            else:
                self.log_message(f"API 请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            self.log_message(f"获取 avid 失败: {str(e)}")
            return None

    def auto_get_videos(self):
        """自动获取推荐视频的评论并处理"""
        self.start_comment_processing(None)

    def start_comment_processing(self, avids):
        """启动后台线程获取评论"""
        if self.processor_thread and self.processor_thread.is_alive():
            self.log_message("已有一个任务正在进行，请稍候...")
            return

        self.processor_thread = CommentProcessorThread(avids, self.result_queue, self.log_queue, self.current_bvid)
        self.processor_thread.start()

    def add_comment_to_table(self, reply, isp):
        comment_text = reply['content']['message']
        row_position = self.comment_table.rowCount()
        self.comment_table.insertRow(row_position)

        comment_item = QTableWidgetItem(comment_text)
        status_item = QTableWidgetItem("违规" if isp else "正常")

        if isp:
            status_item.setBackground(Qt.GlobalColor.red)
        else:
            status_item.setBackground(Qt.GlobalColor.green)

        comment_item.setFlags(comment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.comment_table.setItem(row_position, 0, comment_item)
        self.comment_table.setItem(row_position, 1, status_item)

        if self.comment_table.verticalScrollBar().value() == self.comment_table.verticalScrollBar().maximum():
            self.comment_table.scrollToBottom()

        # 更新统计数据展示
        self.update_stats_label()

    def log_message(self, message):
        """日志显示"""
        self.log_area.append(message)
        if self.log_area.verticalScrollBar().value() == self.log_area.verticalScrollBar().maximum():
            self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def check_queue(self):
        """定期检查队列并更新 UI"""
        try:
            while True:
                reply, isp, rule = self.result_queue.get_nowait()
                self.add_comment_to_table(reply, isp)
        except queue.Empty:
            pass

        try:
            while True:
                log_msg = self.log_queue.get_nowait()
                self.log_message(log_msg)
        except queue.Empty:
            pass

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        dialog.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())
