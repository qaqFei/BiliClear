import sys
import os
import re
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import queue
import json
import requests
from os.path import exists
from PyQt6.QtCore import Qt, QTimer, QTime, QUrl, QPoint
from PyQt6.QtGui import QIcon, QTextCursor, QDesktopServices, QColor, QFont
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QAbstractItemView,
                             QDialog, QFormLayout, QCheckBox, QSpinBox, QMessageBox, QComboBox, QProgressBar,
                             QMainWindow, QFrame)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import threading
from os import environ
environ["QT_gui"] = "True"

import biliclear  # 确保不更改 biliclear 的调用方式
import gpt

# 日志目录
LOG_DIR = './log'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 获取当前日期日志文件路径
log_filename = os.path.join(LOG_DIR, datetime.now().strftime("%Y-%m-%d") + ".log")

# 自定义 QTextEditLogger，将日志输出到 QTextEdit 并检查是否需要更新进度条
class QTextEditLogger(logging.Handler):
    def __init__(self, log_area, parent):
        super().__init__()
        self.log_area = log_area
        self.parent = parent

    def emit(self, record):
        log_entry = self.format(record)
        if record.levelno == logging.DEBUG:
            self.log_area.setTextColor(QColor("#AAAAAA"))
        elif record.levelno == logging.INFO:
            self.log_area.setTextColor(QColor("#00FF00"))  # 绿色文字表示 INFO
        elif record.levelno == logging.WARNING:
            self.log_area.setTextColor(QColor("yellow"))
        elif record.levelno == logging.ERROR:
            self.log_area.setTextColor(QColor("red"))
        elif record.levelno == logging.CRITICAL:
            self.log_area.setTextColor(QColor("red"))

        self.log_area.append(log_entry)
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)

        # 更新最后的日志时间
        self.parent.last_log_time = QTime.currentTime()

        # 检查日志中是否包含等待时间的提示
        wait_match = re.search(r"\*等待(\d+)s", log_entry)
        if wait_match:
            wait_time = int(wait_match.group(1))
            logging.info(f"检测到等待 {wait_time}s, 暂停自动任务重启 {wait_time} 秒...")
            self.parent.is_paused = True

            # 显示进度条并开始倒计时
            self.parent.wait_progress_bar.setVisible(True)
            self.parent.wait_progress_bar.setMaximum(wait_time)
            self.parent.wait_progress_bar.setValue(wait_time)

            # 启动进度条定时器
            self.parent.progress_timer.start(1000)
        else:
            # 如果进度条可见且日志不包含等待提示，则隐藏进度条
            if self.parent.wait_progress_bar.isVisible():
                self.parent.wait_progress_bar.setVisible(False)
                self.parent.progress_timer.stop()
                self.parent.resume_auto_restart()

def setup_logging(log_area, parent):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 日志文件处理程序
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # QTextEdit 输出处理程序，并且绑定进度条的更新
    qt_handler = QTextEditLogger(log_area, parent)
    qt_handler.setLevel(logging.DEBUG)
    qt_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    qt_handler.setFormatter(qt_formatter)
    logger.addHandler(qt_handler)

# 设置 matplotlib 全局字体和样式
plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置字体为微软雅黑，支持中文
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

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

        self.gpt_model_input = QLineEdit(self.config.get('gpt_model', 'gpt-3.5-turbo'))
        layout.addRow('GPT Model:', self.gpt_model_input)

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

        # 应用现代化样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
                border-radius: 10px;
            }
            QLabel, QLineEdit, QCheckBox, QSpinBox {
                font-size: 14px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)

    def save_settings(self):
        """保存设置并写入配置文件"""
        self.config['enable_gpt'] = self.enable_gpt_checkbox.isChecked()
        self.config['gpt_apibase'] = self.gpt_apibase_input.text()
        self.config['gpt_apikey'] = self.gpt_apikey_input.text()
        self.config['gpt_model'] = self.gpt_model_input.text()
        self.config['reply_limit'] = self.reply_limit_input.value()
        self.config['enable_check_lv2avatarat'] = self.enable_check_lv2_checkbox.isChecked()

        save_config(self.config)
        QMessageBox.information(self, '设置已保存', '配置已成功保存！')
        self.close()

class CommentProcessorThread(threading.Thread):
    """后台线程，用于处理评论"""

    def __init__(self, avids=None, result_queue=None, bvid=None, parent=None):
        super().__init__()
        self.avids = avids
        self.result_queue = result_queue
        self.bvid = bvid
        self.parent = parent
        self._stop_event = threading.Event()

    def stop(self):
        """设置停止标志位，通知线程安全退出"""
        self._stop_event.set()

    def process_reply(self, reply):
        """处理单条评论"""
        if self._stop_event.is_set():
            return

        isp, rule = biliclear.processReply(reply)
        self.result_queue.put((reply, isp, rule))
        logging.info(f"处理评论: {reply['content']['message']}")

    def process_video(self, avid):
        """处理单个视频的评论"""
        if self._stop_event.is_set():
            return

        replies = biliclear.getReplys(avid)
        bvid = self.bvid if self.bvid else f"av{avid}"
        logging.info(f"开始处理视频: {bvid}")

        biliclear.videoCount += 1
        self.parent.update_current_avid(avid)

        for reply in replies:
            if self._stop_event.is_set():
                return
            try:
                self.process_reply(reply)
            except Exception as e:
                logging.error(f"评论处理时发生错误: {reply['content']['message']} - 错误: {e}")

    def run(self):
        """线程执行函数"""
        if self.avids is None:
            self.avids = biliclear.getVideos()

        for avid in self.avids:
            if self._stop_event.is_set():
                return
            self.process_video(avid)

        logging.info("所有视频处理完毕")

    def join(self, timeout=None):
        """等待线程安全退出"""
        self.stop()
        super().join(timeout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 加载配置
        self.config = load_config()
        if not self.config:
            QMessageBox.critical(self, '错误', '未找到配置文件，程序将退出。')
            sys.exit(1)

        # 创建线程安全队列用于传递数据
        self.result_queue = queue.Queue()

        self.last_log_time = QTime.currentTime()
        self.violation_reasons = {}  # 违规原因统计字典
        self.is_paused = False
        self.current_bvid = None

        self.processor_thread = None

        # 初始化进度条
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress_bar)

        self.initUI()

        # 初始化日志系统
        setup_logging(self.log_area, self)

        # 定时器，每 100ms 检查一次队列的更新，更新 UI 和日志
        self.timer = self.startTimer(100)

        # 定时器检查 15 秒内无日志输出时启动新任务
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.check_for_timeout)
        self.timeout_timer.start(1000)

        # 定时器每5秒刷新一次饼图
        self.pie_timer = QTimer()
        self.pie_timer.timeout.connect(self.update_pie_chart)
        self.pie_timer.start(5000)

        # 初始化 GPT Token 使用情况
        self.token_usage_timer = QTimer()
        self.token_usage_timer.timeout.connect(self.update_token_usage)
        self.token_usage_timer.start(5000)

    def initUI(self):
        self.setWindowTitle('BiliClear QTGUI')
        self.setGeometry(300, 300, 1200, 700)
        self.setWindowIcon(QIcon('./res/icon.ico'))

        # 使用自定义窗口框架
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # 主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 标题栏
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        self.title_label = QLabel('BiliClear QTGUI')
        self.title_label.setStyleSheet("color: #ffffff; font-size: 16px;")
        self.title_bar_layout = QHBoxLayout()
        self.title_bar_layout.setContentsMargins(10, 0, 0, 0)
        self.title_bar_layout.addWidget(self.title_label)
        self.title_bar_layout.addStretch()
        # 最小化、最大化、关闭按钮
        self.minimize_button = QPushButton('-')
        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button = QPushButton('□')
        self.maximize_button.clicked.connect(self.toggle_maximize)
        self.close_button = QPushButton('×')
        self.close_button.clicked.connect(self.close)
        for btn in [self.minimize_button, self.maximize_button, self.close_button]:
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
            """)
        self.title_bar_layout.addWidget(self.minimize_button)
        self.title_bar_layout.addWidget(self.maximize_button)
        self.title_bar_layout.addWidget(self.close_button)
        self.title_bar.setLayout(self.title_bar_layout)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.title_bar)

        # 等待进度条
        self.wait_progress_bar = QProgressBar()
        self.wait_progress_bar.setVisible(False)
        self.wait_progress_bar.setFixedHeight(5)
        self.wait_progress_bar.setTextVisible(False)
        self.wait_progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #3a3a3a;
            }
        """)
        main_layout.addWidget(self.wait_progress_bar)

        # 内容布局
        content_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧布局 - 评论和日志
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)

        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("请输入 B 站视频的 bvid")
        self.input_box.setFixedHeight(40)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding-left: 10px;
            }
        """)
        left_layout.addWidget(self.input_box)

        self.comment_table = QTableWidget(0, 2, self)
        self.comment_table.setHorizontalHeaderLabels(["评论内容", "违规状态"])
        self.comment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.comment_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.comment_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 4px;
                border: none;
            }
            QTableWidget::item {
                border: none;
                padding: 4px;
            }
        """)
        left_layout.addWidget(self.comment_table)

        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #00FF00;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 14px;  /* 增大字体 */
            }
        """)
        left_layout.addWidget(self.log_area)

        # 按钮
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton('获取视频评论', self)
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet(self.button_style())
        button_layout.addWidget(self.start_btn)

        self.auto_btn = QPushButton('自动获取推荐视频评论', self)
        self.auto_btn.clicked.connect(self.auto_get_videos)
        self.auto_btn.setFixedHeight(40)
        self.auto_btn.setStyleSheet(self.button_style())
        button_layout.addWidget(self.auto_btn)

        self.settings_btn = QPushButton('设置', self)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        self.settings_btn.setFixedHeight(40)
        self.settings_btn.setStyleSheet(self.button_style())
        button_layout.addWidget(self.settings_btn)

        left_layout.addLayout(button_layout)

        left_widget.setLayout(left_layout)

        # 右侧布局 - 数据统计和设置
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)

        self.stats_label = QLabel(self.get_stats_text())
        self.stats_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        right_layout.addWidget(self.stats_label)

        # 当前 Avid 显示
        self.current_avid_label = QLabel("当前视频 Avid: 无")
        self.current_avid_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.current_avid_label.mousePressEvent = self.copy_avid_to_clipboard
        self.current_avid_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        right_layout.addWidget(self.current_avid_label)

        # GPT Token 显示
        self.token_label = QLabel("今日已花费 GPT Tokens: 0")
        self.token_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        right_layout.addWidget(self.token_label)

        # 饼图类型选择
        self.pie_chart_type_combo = QComboBox(self)
        self.pie_chart_type_combo.addItems(["违规原因占比"])
        self.pie_chart_type_combo.currentIndexChanged.connect(self.update_pie_chart)
        self.pie_chart_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding-left: 10px;
                height: 30px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        right_layout.addWidget(self.pie_chart_type_combo)

        # 饼图显示
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        # 违规评论列表
        self.violation_table = QTableWidget(0, 1, self)
        self.violation_table.setHorizontalHeaderLabels(["违规评论"])
        self.violation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.violation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.violation_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 4px;
                border: none;
            }
            QTableWidget::item {
                border: none;
                padding: 4px;
            }
        """)
        right_layout.addWidget(self.violation_table)

        # 按钮
        link_button_layout = QHBoxLayout()

        github_btn = QPushButton('本项目Github主页', self)
        github_btn.clicked.connect(self.open_github)
        github_btn.setFixedHeight(40)
        github_btn.setStyleSheet(self.button_style())
        link_button_layout.addWidget(github_btn)

        contributors_btn = QPushButton('本项目贡献者', self)
        contributors_btn.clicked.connect(self.open_contributors)
        contributors_btn.setFixedHeight(40)
        contributors_btn.setStyleSheet(self.button_style())
        link_button_layout.addWidget(contributors_btn)

        api_btn = QPushButton('ChatGPT API管理页面', self)
        api_btn.clicked.connect(self.open_api_keys)
        api_btn.setFixedHeight(40)
        api_btn.setStyleSheet(self.button_style())
        link_button_layout.addWidget(api_btn)

        right_layout.addLayout(link_button_layout)

        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 500])

        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)

        main_widget.setLayout(main_layout)

        # 应用自定义样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                border-radius: 10px;
            }
        """)

        # 添加窗口图标
        self.setWindowIcon(QIcon('./res/icon.ico'))

        # 显示窗口
        self.show()

    def button_style(self):
        return """
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def get_stats_text(self):
        """生成统计文本"""
        violation_rate = 0
        if biliclear.replyCount > 0:
            violation_rate = (biliclear.violationsReplyCount / biliclear.replyCount) * 100

        return (f"BiliClear 数据统计\n"
                f"已检查视频: {biliclear.videoCount}\n"
                f"已检查评论: {biliclear.replyCount}\n"
                f"违规评论: {biliclear.violationsReplyCount}\n"
                f"评论违规率: {violation_rate:.5f}%\n"
                f"B站API风控中: {biliclear.waitingRiskControl}")

    def update_stats_label(self):
        """更新统计显示"""
        self.stats_label.setText(self.get_stats_text())

    def start_processing(self):
        """手动获取视频的评论并处理"""
        bvid = self.input_box.text().strip()

        if not bvid:
            logging.info("请输入有效的视频 bvid")
            return

        if not bvid.startswith("BV") or len(bvid) < 6:
            logging.info("请输入有效的 Bilibili 视频 bvid (例如：BVxxxxxxxx)")
            return

        try:
            avid = self.get_avid_from_bvid(bvid)

            if not avid:
                logging.info("获取 avid 失败，请检查 bvid 是否正确")
                return

            self.current_bvid = bvid
            self.start_comment_processing([avid])

        except Exception as e:
            logging.error(f"发生错误: {str(e)}")

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
                logging.error(f"API 请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"获取 avid 失败: {str(e)}")
            return None

    def auto_get_videos(self):
        """自动获取推荐视频的评论并处理"""
        self.start_comment_processing(None)

    def start_comment_processing(self, avids):
        """启动后台线程获取评论"""
        if self.processor_thread and self.processor_thread.is_alive():
            logging.info("已有一个任务正在进行，请稍候...")
            return

        self.processor_thread = CommentProcessorThread(avids, self.result_queue, self.current_bvid, parent=self)
        self.processor_thread.start()

    def update_current_avid(self, avid):
        """更新当前处理的 Avid 显示"""
        self.current_avid_label.setText(f"当前视频 Avid: {avid}")

    def copy_avid_to_clipboard(self, event):
        """将当前 Avid 复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_avid_label.text().split(": ")[1])
        logging.info("Avid 已复制到剪贴板")

    def add_comment_to_table(self, reply, isp, rule):
        comment_text = reply['content']['message']
        row_position = self.comment_table.rowCount()
        self.comment_table.insertRow(row_position)

        comment_item = QTableWidgetItem(comment_text)
        status_item = QTableWidgetItem("违规" if isp else "正常")

        if isp:
            status_item.setBackground(QColor("#FF6F61"))  # 柔和的红色背景表示违规
        else:
            status_item.setBackground(QColor("#6B8E23"))  # 柔和的绿色背景表示正常

        comment_item.setFlags(comment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        self.comment_table.setItem(row_position, 0, comment_item)
        self.comment_table.setItem(row_position, 1, status_item)

        if isp:
            # 添加到违规评论列表
            violation_row = self.violation_table.rowCount()
            self.violation_table.insertRow(violation_row)
            violation_item = QTableWidgetItem(comment_text)
            violation_item.setFlags(violation_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.violation_table.setItem(violation_row, 0, violation_item)

            # 统计违规原因
            if rule not in self.violation_reasons:
                self.violation_reasons[rule] = 0
            self.violation_reasons[rule] += 1

        if self.comment_table.verticalScrollBar().value() == self.comment_table.verticalScrollBar().maximum():
            self.comment_table.scrollToBottom()

        # 更新统计数据展示
        self.update_stats_label()

    def timerEvent(self, event):
        """定时器事件，用于检查队列并更新 UI"""
        try:
            while True:
                reply, isp, rule = self.result_queue.get_nowait()
                self.add_comment_to_table(reply, isp, rule)
        except queue.Empty:
            pass

    def check_for_timeout(self):
        """检查是否在 15 秒内无日志输出，超时则自动开始新任务"""
        if self.is_paused:
            return

        # 检查是否超过 15 秒无日志更新
        if self.last_log_time and self.last_log_time.secsTo(QTime.currentTime()) > 15:
            logging.info("超时 15 秒，自动启动新任务...")
            self.auto_get_videos()

    def update_progress_bar(self):
        """每秒更新一次进度条"""
        value = self.wait_progress_bar.value() - 1
        if value >= 0:
            self.wait_progress_bar.setValue(value)
        else:
            # 倒计时结束，隐藏进度条并恢复任务
            self.wait_progress_bar.setVisible(False)
            self.progress_timer.stop()
            self.resume_auto_restart()

    def resume_auto_restart(self):
        """恢复自动任务重启"""
        self.is_paused = False
        logging.info("等待结束，恢复自动任务重启。")

    def update_token_usage(self):
        """更新GPT Token使用情况"""
        try:
            token_count = gpt.get_today_gpt_usage()
            self.token_label.setText(f"今日已花费 GPT Tokens: {token_count}")
        except Exception as e:
            logging.error(f"更新GPT Token失败: {str(e)}")

    def update_pie_chart(self):
        """更新饼图，显示违规原因占比"""
        self.ax.clear()

        # 检查违规原因是否为空
        if not self.violation_reasons:
            logging.debug("无违规原因数据，无法更新饼图")
            self.canvas.draw()
            return

        if self.pie_chart_type_combo.currentText() == "违规原因占比":
            labels = list(self.violation_reasons.keys())
            data = list(self.violation_reasons.values())
            logging.debug(f"更新饼图数据: {labels}, {data}")

            # 优化饼图配色
            colors = plt.cm.Pastel1.colors[:len(labels)]
            self.ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)

        self.ax.axis('equal')
        self.canvas.draw()

    def open_github(self):
        """打开Github页面"""
        QDesktopServices.openUrl(QUrl("https://github.com/qaqFei/BiliClear"))

    def open_contributors(self):
        """打开贡献者页面"""
        QDesktopServices.openUrl(QUrl("https://github.com/qaqFei/BiliClear/graphs/contributors"))

    def open_api_keys(self):
        """打开ChatGPT API页面"""
        QDesktopServices.openUrl(QUrl("https://platform.openai.com/api-keys"))

    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        dialog.exec()

    def closeEvent(self, event):
        """关闭事件处理，自动强制退出所有子线程"""
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.stop()
            self.processor_thread.join(timeout=1)

        event.accept()

    # 实现鼠标事件以移动窗口
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    main_window = MainWindow()

    ret_code = app.exec()
    sys.exit(ret_code)
