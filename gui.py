import sys
import re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from biliclear import BiliClear


# 创建一个新的线程类来处理后台任务
class CommentProcessor(QThread):
    comment_processed = pyqtSignal(dict)  # 每个评论处理完成后发出信号
    log_message = pyqtSignal(str)  # 日志消息的信号
    video_changed = pyqtSignal(int)  # 当前处理的视频改变时的信号 (使用avid)
    count_violations = pyqtSignal(bool)  # 是否违规的信号，用于统计

    def __init__(self, bili_clear, avids=None):
        super().__init__()
        self.bili_clear = bili_clear
        self.avids = avids

    def run(self):
        """执行后台任务：获取并处理评论"""
        if self.avids is None:
            # 自动获取推荐视频
            self.avids = self.bili_clear.get_videos()

        for avid in self.avids:
            replies = self.bili_clear.get_replys(avid)

            # 发出当前处理视频信号 (使用avid)
            self.video_changed.emit(avid)

            for reply in replies:
                # 处理评论
                isp, rule = self.bili_clear.is_porn(reply['content']['message'])
                self.bili_clear.process_reply(reply)
                self.log_message.emit(f"处理评论: {reply['content']['message']}")
                self.comment_processed.emit(reply)

                # 如果违规，发出信号
                self.count_violations.emit(isp)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.bili_clear = BiliClear()  # 实例化主逻辑类

        # 统计数据
        self.current_session_violation_count = 0  # 本次处理的违规评论数
        self.total_violation_count = 0  # 累计的违规评论数
        self.is_task_running = False  # 记录是否有任务在运行

        self.initUI()

        self.processor_thread = None  # 保存线程对象
        self.current_bvid = None  # 保存当前处理的视频 bvid

    def initUI(self):
        # 创建左右布局
        main_layout = QHBoxLayout()

        # 使用 QSplitter 分割左边处理信息与右边网页预览框
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左边布局
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        # 当前正在处理的视频
        self.current_video_label = QLabel("当前未处理任何视频")
        self.current_video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.current_video_label)

        # 违规统计标签
        self.session_violation_label = QLabel("本次违规评论数：0")
        left_layout.addWidget(self.session_violation_label)
        self.total_violation_label = QLabel(f"累计违规评论数：{self.total_violation_count}")
        left_layout.addWidget(self.total_violation_label)

        # 手动输入 bvid
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("请输入 B 站视频的 bvid")
        left_layout.addWidget(self.input_box)

        # 表格展示评论处理情况
        self.comment_table = QTableWidget(0, 2, self)
        self.comment_table.setHorizontalHeaderLabels(["评论内容", "违规状态"])
        self.comment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.comment_table)

        # 日志区域
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        left_layout.addWidget(self.log_area)

        # 手动获取视频评论按钮
        self.start_btn = QPushButton('识别手动输入的 bvid', self)
        self.start_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_btn)

        # 自动获取推荐视频按钮
        self.auto_btn = QPushButton('自动获取推荐视频评论', self)
        self.auto_btn.clicked.connect(self.auto_get_videos)
        left_layout.addWidget(self.auto_btn)

        # 设置左边的布局到 left_widget
        left_widget.setLayout(left_layout)

        # 网页预览区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        # 网页预览器 - 默认加载B站首页，支持操作和交互
        self.web_view = QWebEngineView(self)
        self.web_view.setUrl(QUrl("https://www.bilibili.com"))
        right_layout.addWidget(self.web_view)

        # 识别视频评论按钮（右下角）
        self.process_btn = QPushButton('识别当前预览视频的评论', self)
        self.process_btn.clicked.connect(self.toggle_task)
        right_layout.addWidget(self.process_btn)

        right_widget.setLayout(right_layout)

        # 添加左右布局到 splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置 splitter 的大小自适应
        splitter.setSizes([500, 300])  # 初始左边宽度为500，右边为300

        # 将 splitter 添加到主布局
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        self.setWindowTitle('Bilibili 自动评论监控')
        self.setGeometry(300, 300, 1200, 600)  # 调整窗口大小
        self.show()

    def toggle_task(self):
        """根据当前任务状态启动或终止评论识别任务"""
        if not self.is_task_running:
            # 任务未在运行，尝试提取BVID并启动任务
            url = self.web_view.url().toString()
            bvid = self.extract_bvid_from_url(url)

            if bvid:
                avid = self.bili_clear.bvid_to_avid(bvid)  # 将BVID转换为AVID
                if avid:
                    self.log_message(f"开始识别视频：{bvid}")
                    self.start_comment_processing([avid])
                    self.process_btn.setText("终止任务")
                    self.is_task_running = True
                else:
                    self.log_message("无法获取视频的 AVID，请确认视频地址是否正确。")
            else:
                self.log_message("当前页面不是有效的视频页面。")
        else:
            # 任务正在运行，终止任务
            if self.processor_thread and self.processor_thread.isRunning():
                self.processor_thread.terminate()
                self.log_message("任务已终止。")
                self.process_btn.setText("识别当前预览视频的评论")
                self.is_task_running = False

    def extract_bvid_from_url(self, url):
        """从URL中提取BVID"""
        match = re.search(r'/video/([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        return None

    def start_processing(self):
        """手动获取视频的评论并处理"""
        # 获取用户输入的 bvid
        bvid = self.input_box.text().strip()

        # 验证输入是否为空
        if not bvid:
            self.log_message("请输入有效的视频 bvid")  # 提示用户输入有效的 bvid
            return

        try:
            # 获取 avid (从 bvid 转换)
            avid = self.bili_clear.bvid_to_avid(bvid)

            if not avid:
                self.log_message("获取 avid 失败，请检查 bvid 是否正确")
                return

            # 更新当前视频 bvid 并显示网页
            self.current_bvid = bvid
            # 在预览框中加载视频网页
            self.web_view.setUrl(QUrl(f"https://www.bilibili.com/video/{bvid}"))

            # 启动评论处理线程，传入 avid
            self.start_comment_processing([avid])

        except Exception as e:
            # 捕获任何异常并记录错误
            self.log_message(f"发生错误: {str(e)}")

    def auto_get_videos(self):
        """自动获取推荐视频的评论并处理"""
        self.start_comment_processing(None)  # 传入 None 代表自动获取视频

    def start_comment_processing(self, avids):
        """启动评论处理线程"""
        # 确保没有线程正在运行
        if self.processor_thread and self.processor_thread.isRunning():
            self.log_message("已有一个任务正在进行，请稍候...")
            return

        # 重置当前会话的违规计数
        self.current_session_violation_count = 0
        self.session_violation_label.setText("本次违规评论数：0")

        # 创建一个线程对象来处理评论
        self.processor_thread = CommentProcessor(self.bili_clear, avids)
        self.processor_thread.comment_processed.connect(self.add_comment_to_table)
        self.processor_thread.log_message.connect(self.log_message)
        self.processor_thread.video_changed.connect(self.update_video_label)
        self.processor_thread.count_violations.connect(self.update_violation_count)

        # 启动线程
        self.processor_thread.start()

    def add_comment_to_table(self, reply):
        """将处理的评论添加到表格中，并根据结果进行标记"""
        comment_text = reply['content']['message']
        isp, rule = self.bili_clear.is_porn(comment_text)

        # 添加评论到表格中
        row_position = self.comment_table.rowCount()
        self.comment_table.insertRow(row_position)

        # 创建评论和状态单元格
        comment_item = QTableWidgetItem(comment_text)
        status_item = QTableWidgetItem("违规" if isp else "正常")

        # 设置背景颜色
        if isp:
            status_item.setBackground(Qt.GlobalColor.red)
        else:
            status_item.setBackground(Qt.GlobalColor.green)

        # 设置不可编辑状态
        comment_item.setFlags(comment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # 将评论和状态添加到表格
        self.comment_table.setItem(row_position, 0, comment_item)
        self.comment_table.setItem(row_position, 1, status_item)

    def update_video_label(self, avid):
        """更新当前处理的视频标签"""
        self.current_bvid = avid
        self.current_video_label.setText(f"当前正在处理视频：av{avid}")

    def update_violation_count(self, is_violation):
        """更新违规评论统计"""
        if is_violation:
            self.current_session_violation_count += 1
            self.total_violation_count += 1

            # 更新标签显示
            self.session_violation_label.setText(f"本次违规评论数：{self.current_session_violation_count}")
            self.total_violation_label.setText(f"累计违规评论数：{self.total_violation_count}")

    def log_message(self, message):
        """显示日志消息"""
        self.log_area.append(message)


def start_gui():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    start_gui()
