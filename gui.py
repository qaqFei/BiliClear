import sys
import webbrowser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QLineEdit, QAbstractItemView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QTextCursor
from PyQt6.QtWebEngineWidgets import QWebEngineView  # 确保使用 QWebEngineView 支持 HTML5
import requests
import biliclear  # 调用主程序中的函数

class CommentProcessor(QThread):
    comment_processed = pyqtSignal(dict)
    log_message = pyqtSignal(str)
    video_changed = pyqtSignal(str)
    count_violations = pyqtSignal(bool)
    update_stats = pyqtSignal(int, int)  # 新增信号，用于更新检查视频数和检查评论数

    def __init__(self, avids=None):
        super().__init__()
        self.avids = avids

    def run(self):
        if self.avids is None:
            self.avids = biliclear.getVideos()

        for avid in self.avids:
            replies = biliclear.getReplys(avid)
            bvid = f"av{avid}"
            self.video_changed.emit(bvid)
            self.update_stats.emit(1, len(replies))  # 更新视频数和评论数

            for reply in replies:
                isp, rule = biliclear.isPorn(reply['content']['message'])
                biliclear.processReply(reply)
                self.log_message.emit(f"处理评论: {reply['content']['message']}")
                self.comment_processed.emit(reply)
                self.count_violations.emit(isp)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 统计数据
        self.total_video_count = 0
        self.total_comment_count = 0
        self.total_violation_count = 0
        self.current_session_violation_count = 0

        self.api_risk_control = False  # 默认 API 风控状态为 False

        self.initUI()

        self.processor_thread = None
        self.current_bvid = None

    def initUI(self):
        self.setWindowTitle('Bilibili 自动评论监控')
        self.setGeometry(300, 300, 1200, 600)
        self.setWindowIcon(QIcon('icon.ico'))  # 设置窗口图标为根目录下的 icon.ico

        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧布局
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        self.current_video_label = QLabel("当前未处理任何视频")
        self.current_video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.current_video_label)

        # 统计部分显示
        self.stats_label = QLabel(self.get_stats_text())  # 显示统计信息
        left_layout.addWidget(self.stats_label)

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

        self.start_btn = QPushButton('获取视频评论', self)
        self.start_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_btn)

        self.auto_btn = QPushButton('自动获取推荐视频评论', self)
        self.auto_btn.clicked.connect(self.auto_get_videos)
        left_layout.addWidget(self.auto_btn)

        left_widget.setLayout(left_layout)

        # 右侧布局 - 使用 QWebEngineView 显示网页
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        self.video_preview = QWebEngineView(self)  # 使用 QWebEngineView 加载 Bilibili 网页
        right_layout.addWidget(self.video_preview)

        self.browser_button = QPushButton("在浏览器中访问")
        self.browser_button.clicked.connect(self.open_in_browser)
        right_layout.addWidget(self.browser_button)

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
        if self.total_comment_count > 0:
            violation_rate = (self.total_violation_count / self.total_comment_count) * 100

        return (f"BiliClear 数据统计\n"
                f"已检查视频: {self.total_video_count}\n"
                f"已检查评论: {self.total_comment_count}\n"
                f"违规评论: {self.total_violation_count}\n"
                f"评论违规率: {violation_rate:.5f}%\n"
                f"B站API风控中: {self.api_risk_control}")

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
            avid = biliclear.bvid2avid(bvid)

            if not avid:
                self.log_message("获取 avid 失败，请检查 bvid 是否正确")
                return

            self.current_bvid = bvid
            self.update_video_preview(bvid)

            self.start_comment_processing([avid])

        except Exception as e:
            self.log_message(f"发生错误: {str(e)}")

    def update_video_preview(self, bvid):
        """通过 bvid 加载 Bilibili 视频页面"""
        try:
            url = f"https://www.bilibili.com/video/{bvid}"
            self.video_preview.setUrl(QUrl(url))  # 加载完整视频页面

        except Exception as e:
            self.video_preview.setHtml(f"<h2>视频加载失败: {str(e)}</h2>")

    def auto_get_videos(self):
        """自动获取推荐视频的评论并处理"""
        self.start_comment_processing(None)

    def start_comment_processing(self, avids):
        if self.processor_thread and self.processor_thread.isRunning():
            self.log_message("已有一个任务正在进行，请稍候...")
            return

        self.processor_thread = CommentProcessor(avids)
        self.processor_thread.comment_processed.connect(self.add_comment_to_table)
        self.processor_thread.log_message.connect(self.log_message)
        self.processor_thread.video_changed.connect(self.update_video_label)
        self.processor_thread.count_violations.connect(self.update_violation_count)
        self.processor_thread.update_stats.connect(self.update_check_counts)  # 连接统计更新信号
        self.processor_thread.start()

    def add_comment_to_table(self, reply):
        comment_text = reply['content']['message']
        isp, rule = biliclear.isPorn(comment_text)

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

        # 如果滚动条在底部，自动滚动到最新评论
        if self.comment_table.verticalScrollBar().value() == self.comment_table.verticalScrollBar().maximum():
            self.comment_table.scrollToBottom()

    def update_violation_count(self, isp):
        """更新违规评论计数"""
        if isp:
            self.total_violation_count += 1
        self.update_stats_label()

    def update_check_counts(self, video_count, comment_count):
        """更新视频和评论的统计计数"""
        self.total_video_count += video_count
        self.total_comment_count += comment_count
        self.update_stats_label()

    def log_message(self, message):
        """日志显示"""
        self.log_area.append(message)
        # 检测日志滚动条是否在底部，自动滚动
        if self.log_area.verticalScrollBar().value() == self.log_area.verticalScrollBar().maximum():
            self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def update_video_label(self, bvid):
        """更新当前视频的显示"""
        self.current_bvid = bvid
        self.current_video_label.setText(f"当前视频: {bvid}")
        self.update_video_preview(bvid)

    def open_in_browser(self):
        """在默认浏览器中打开 Bilibili 视频页面"""
        if self.current_bvid:
            url = f"https://www.bilibili.com/video/{self.current_bvid}"
            webbrowser.open(url)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())
