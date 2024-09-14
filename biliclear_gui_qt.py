#这段代码不由qaq_fei维护，问题请联系Felix3322
import os
from datetime import datetime

print("""
     ██████╗ ████████╗██╗   ██╗██╗    ██████╗ ██╗   ██╗   
    ██╔═══██╗╚══██╔══╝██║   ██║██║    ██╔══██╗╚██╗ ██╔╝   
    ██║   ██║   ██║   ██║   ██║██║    ██████╔╝ ╚████╔╝    
    ██║▄▄ ██║   ██║   ██║   ██║██║    ██╔══██╗  ╚██╔╝     
    ╚██████╔╝   ██║   ╚██████╔╝██║    ██████╔╝   ██║      
     ╚══▀▀═╝    ╚═╝    ╚═════╝ ╚═╝    ╚═════╝    ╚═╝      

 ██████╗ ██████╗         ██████╗ ██╗   ██╗███████╗███████╗
██╔═══██╗██╔══██╗        ██╔══██╗██║   ██║██╔════╝██╔════╝
██║   ██║██████╔╝        ██████╔╝██║   ██║█████╗  █████╗  
██║   ██║██╔══██╗        ██╔══██╗██║   ██║██╔══╝  ██╔══╝  
╚██████╔╝██████╔╝███████╗██████╔╝╚██████╔╝██║     ██║     
 ╚═════╝ ╚═════╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝     ╚═╝     

正在导入库，请稍等。。。""")
import re
import sys
import threading
import queue
import json
import requests
from os.path import exists
from PyQt6.QtCore import Qt, QTimer, QTime, QUrl
from PyQt6.QtGui import QIcon, QTextCursor, QDesktopServices, QColor
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QAbstractItemView,
                             QDialog, QFormLayout, QCheckBox, QSpinBox, QMessageBox, QComboBox, QProgressBar)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from os import environ
import threading
import concurrent.futures
environ["gui"] = "enable"
print("正在读取设置，初始化。。。")
import biliclear
import gpt


# 方式3：通过设置 rcParams 全局替换 sans-serif 字体，解决中文显示问题
plt.style.use('dark_background')
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
print("正在加载函数，请稍等。。。")
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

    def __init__(self, avids=None, result_queue=None, log_queue=None, bvid=None, enable_gpt=False, parent=None):
        super().__init__()
        self.avids = avids
        self.result_queue = result_queue
        self.log_queue = log_queue
        self.bvid = bvid
        self.enable_gpt = enable_gpt
        self.video_counter = 0
        self.parent = parent
        self._stop_event = threading.Event()  # 停止标志位
        self.max_workers = os.cpu_count() / 3  # 动态设置为 CPU 核心数的两倍，处理尽可能多的评论

    def stop(self):
        """设置停止标志位，通知线程安全退出"""
        self._stop_event.set()

    def process_reply(self, reply):
        """处理单条评论"""
        if self._stop_event.is_set():  # 检查停止标志位
            return  # 安全退出

        isp, rule = biliclear.processReply(reply)  # 处理评论
        self.result_queue.put((reply, isp, rule))  # 将评论和检测结果发送到主线程
        self.log_queue.put(f"处理评论: {reply['content']['message']}")

    def process_video(self, avid):
        """处理单个视频的评论"""
        if self._stop_event.is_set():  # 检查停止标志位
            return  # 安全退出

        if self.video_counter >= 10:
            self.log_queue.put("检查了 10 个视频，自动启动新的任务...")
            self.parent.auto_get_videos()  # 调用主窗口的自动获取方法
            return  # 结束当前线程，启动新的任务

        replies = biliclear.getReplys(avid)
        bvid = self.bvid if self.bvid else f"av{avid}"
        self.log_queue.put(f"开始处理视频: {bvid}")
        self.video_counter += 1  # 增加计数
        biliclear.videoCount += 1
        self.parent.update_current_avid(avid)  # 更新当前 avid 显示

        # 使用线程池并发处理该视频的评论，最大并发量取决于 CPU 核心数
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_reply, reply): reply for reply in replies}

            # 等待所有评论处理完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # 获取处理结果，若有异常将会抛出
                except Exception as e:
                    reply = futures[future]
                    self.log_queue.put(f"评论处理时发生错误: {reply['content']['message']} - 错误: {e}")

    def run(self):
        """线程执行函数"""
        if self.avids is None:
            self.avids = biliclear.getVideos()

        for avid in self.avids:
            if self._stop_event.is_set():
                return  # 安全退出
            self.process_video(avid)

        self.log_queue.put("所有视频处理完毕")

    def join(self, timeout=None):
        """等待线程安全退出"""
        self.stop()  # 停止线程执行
        super().join(timeout)  # 等待线程结束


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

        self.last_log_time = QTime.currentTime()
        self.violation_reasons = {}  # 违规原因统计字典
        self.is_paused = False  # 用于暂停自动任务重启的标志
        self.current_bvid = None

        self.processor_thread = None

        # 添加进度条
        self.progress_bar = None  # 初始化进度条为空
        self.progress_timer = None  # 定时器

        self.initUI()

        # 将标准输出和错误输出重定向到日志窗口
        sys.stdout = Stream(self.log_area)
        sys.stderr = Stream(self.log_area)

        # 定时器，每 100ms 检查一次队列的更新，更新 UI 和日志
        self.timer = self.startTimer(100)

        # 定时器检查 15 秒内无日志输出时启动新任务
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.check_for_timeout)
        self.timeout_timer.start(1000)  # 每秒检查一次是否超时

        # 定时器每5秒刷新一次饼图
        self.pie_timer = QTimer()
        self.pie_timer.timeout.connect(self.update_token_usage)
        self.pie_timer.start(5000)  # 每隔5秒自动刷新一次

    def initUI(self):
        self.setWindowTitle('BiliClear QTGUI')
        self.setGeometry(300, 300, 1200, 600)
        self.setWindowIcon(QIcon('./res/icon.ico'))  # 设置窗口图标为根目录下的 res/icon.ico

        # 使用样式表设置深色主题和主色调
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1f22;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #00aeec;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #fb7299;
            }
            QLabel, QLineEdit, QComboBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QTextEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
            QTableWidget {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
            }
            QTableWidget QHeaderView::section {
                background-color: #555555;
                color: white;
                border: 1px solid #3C3C3C;
            }
            QProgressBar {
                background-color: #3C3C3C;
                border: 1px solid #555555;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #00aeec;
            }
        """)

        # 创建主布局
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧布局 - 评论和日志
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("请输入 B 站视频的 bvid")
        left_layout.addWidget(self.input_box)

        self.comment_table = QTableWidget(0, 2, self)
        self.comment_table.setHorizontalHeaderLabels(["评论内容", "违规状态"])
        self.comment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.comment_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.comment_table)

        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        left_layout.addWidget(self.log_area)

        # 按钮
        self.start_btn = QPushButton('获取视频评论', self)
        self.start_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_btn)

        self.auto_btn = QPushButton('自动获取推荐视频评论', self)
        self.auto_btn.clicked.connect(self.auto_get_videos)
        left_layout.addWidget(self.auto_btn)

        self.settings_btn = QPushButton('设置', self)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        left_layout.addWidget(self.settings_btn)

        # 创建并添加进度条到左下角按钮上方
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)  # 初始隐藏
        left_layout.addWidget(self.progress_bar)

        left_widget.setLayout(left_layout)

        # 右侧布局 - 数据统计和设置
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        self.stats_label = QLabel(self.get_stats_text())  # 显示统计信息
        right_layout.addWidget(self.stats_label)

        # 当前 Avid 显示
        self.current_avid_label = QLabel("当前视频 Avid: 无")
        self.current_avid_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.current_avid_label.mousePressEvent = self.copy_avid_to_clipboard
        right_layout.addWidget(self.current_avid_label)

        # GPT Token 显示
        self.token_label = QLabel("今日已花费 GPT Tokens: 0")
        right_layout.addWidget(self.token_label)

        # 饼图类型选择
        self.pie_chart_type_combo = QComboBox(self)
        self.pie_chart_type_combo.addItems(["违规原因占比"])
        self.pie_chart_type_combo.currentIndexChanged.connect(self.update_pie_chart)
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
        right_layout.addWidget(self.violation_table)

        github_btn = QPushButton('本项目Github主页', self)
        github_btn.clicked.connect(self.open_github)
        right_layout.addWidget(github_btn)

        contributors_btn = QPushButton('本项目贡献者', self)
        contributors_btn.clicked.connect(self.open_contributors)
        right_layout.addWidget(contributors_btn)

        api_btn = QPushButton('ChatGPT API管理页面', self)
        api_btn.clicked.connect(self.open_api_keys)
        right_layout.addWidget(api_btn)

        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 300])

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        self.show()

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

        self.processor_thread = CommentProcessorThread(avids, self.result_queue, self.log_queue, self.current_bvid,
                                                       parent=self)
        self.processor_thread.start()

    def update_current_avid(self, avid):
        """更新当前处理的 Avid 显示"""
        self.current_avid_label.setText(f"当前视频 Avid: {avid}")

    def copy_avid_to_clipboard(self, event):
        """将当前 Avid 复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.current_avid_label.text().split(": ")[1])
        self.log_message("Avid 已复制到剪贴板")

    def add_comment_to_table(self, reply, isp, rule):
        comment_text = reply['content']['message']
        row_position = self.comment_table.rowCount()
        self.comment_table.insertRow(row_position)

        comment_item = QTableWidgetItem(comment_text)
        status_item = QTableWidgetItem("违规" if isp else "正常")

        # 设置黑色文字
        status_item.setForeground(Qt.GlobalColor.black)

        if isp:
            status_item.setBackground(QColor("#fb7299"))
        else:
            status_item.setBackground(QColor("#00aeec"))

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

        # 自动刷新饼图
        self.update_pie_chart()

    def log_message(self, message):
        """日志显示，带时间戳和日志级别，并根据级别高亮显示"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 获取当前时间
        log_entry = f"[{current_time}] [GUI Log] {message}"  # 格式化日志内容

        self.log_area.append(log_entry)  # 添加日志内容到日志窗口
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)
    def timerEvent(self, event):
        """定时器事件，用于检查队列并更新 UI"""
        try:
            while True:
                reply, isp, rule = self.result_queue.get_nowait()
                self.add_comment_to_table(reply, isp, rule)
        except queue.Empty:
            pass

        try:
            while True:
                log_msg = self.log_queue.get_nowait()
                self.log_message(log_msg)
        except queue.Empty:
            pass

    def check_for_timeout(self):
        """检查是否在 15 秒内无日志输出，超时则自动开始新任务"""
        if self.is_paused:
            return  # 如果当前任务暂停，不执行自动重启逻辑

        # 检查日志中是否有 "*等待..s" 模式的内容
        log_text = self.log_area.toPlainText()
        wait_match = re.search(r"\*等待(\d+)s", log_text)

        if wait_match:
            wait_time = int(wait_match.group(1))  # 提取等待的秒数
            self.log_message(f"检测到等待 {wait_time}s, 暂停自动任务重启 {wait_time} 秒...")
            self.is_paused = True

            # 显示进度条并开始倒计时
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(wait_time)
            self.progress_bar.setValue(wait_time)

            # 使用定时器更新进度条
            self.progress_timer = QTimer(self)
            self.progress_timer.timeout.connect(self.update_progress_bar)
            self.progress_timer.start(1000)  # 每秒更新一次

        elif self.last_log_time.secsTo(QTime.currentTime()) > 15:
            self.log_message("超时 15 秒，自动启动新任务...")
            self.auto_get_videos()

    def update_progress_bar(self):
        """每秒更新一次进度条"""
        value = self.progress_bar.value() - 1
        if value >= 0:
            self.progress_bar.setValue(value)
        else:
            # 倒计时结束，隐藏进度条并恢复任务
            self.progress_bar.setVisible(False)
            self.progress_timer.stop()
            self.resume_auto_restart()
    def resume_auto_restart(self):
        """恢复自动任务重启"""
        self.is_paused = False
        self.log_message("等待结束，恢复自动任务重启。")

    def update_token_usage(self):
        """更新GPT Token使用情况"""
        try:
            token_count = gpt.get_today_gpt_usage()
            self.token_label.setText(f"今日已花费 GPT Tokens: {token_count}")
        except Exception as e:
            self.log_message(f"更新GPT Token失败: {str(e)}")

    def update_pie_chart(self):
        """更新饼图，显示违规原因占比"""
        self.ax.clear()


        if self.pie_chart_type_combo.currentText() == "违规原因占比":
            labels = list(self.violation_reasons.keys())
            data = list(self.violation_reasons.values())
            self.ax.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)

        self.ax.axis('equal')  # 保证饼图是圆形的
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
            self.processor_thread.stop()  # 停止线程
            self.processor_thread.join(timeout=1)  # 等待子线程结束

        event.accept()  # 允许窗口关闭


class Stream:
    def __init__(self, log_area):
        self.log_area = log_area

    def write(self, message):
        """将输出消息格式化并显示在日志窗口"""
        if message.strip():
            # 获取当前时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 格式化日志信息，添加时间戳
            formatted_message = f"[{current_time}] [Main Log] {message.strip()}"
            # 将格式化后的日志显示在日志窗口
            self.log_area.append(formatted_message)
            self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def flush(self):
        """flush 是必须实现的空方法"""
        pass


print("正在启动GUI，请稍等。。。")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())
