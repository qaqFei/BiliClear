# BiliClear - Bilibili 评论自动监控工具

BiliClear 是一个自动化工具，用于监控并识别 Bilibili 视频评论中的违规内容。该工具通过预定义的规则对评论进行筛选，并通过邮件和 Bilibili 举报 API 对违规评论进行举报。工具同时提供了命令行和 GUI 图形界面供用户操作。

---

## 功能列表
1. 自动获取 Bilibili 推荐视频评论，筛选并举报违规评论。
2. 手动输入 Bilibili 视频的 `bvid`，筛选并举报评论。
3. 自动调用 Bilibili 官方举报 API 进行举报（可选）。
4. 提供图形化用户界面，支持自动识别评论和手动输入 `bvid`。

---

## 系统要求
- Python 3.12
- 依赖库：
  - `smtplib`
  - `requests`
  - `PyQt6`
  - `json`
  - `re`

---

## 配置文件

工具使用 `config.json` 文件保存用户的 Bilibili 和 SMTP 相关配置，首次运行时工具将引导用户生成此配置文件。

配置文件包括以下内容：
- `sender_email`：用于发送举报邮件的邮箱。
- `sender_password`：邮箱的 SMTP 密码。
- `headers`：包含 Bilibili 的用户登录 Cookie 和 User-Agent。
- `smtp_server` 和 `smtp_port`：SMTP 服务器地址和端口。
- `csrf`：Bilibili 登录的 CSRF Token。
- `bili_report_api`：是否启用 Bilibili 举报 API（可选）。

---

## 主程序详细介绍

### BiliClear 类

`BiliClear` 类是整个程序的核心，负责处理配置加载、视频评论抓取、违规检测和举报功能。

#### 函数

1. **`__init__(self)`**：初始化 `BiliClear` 类，加载配置文件和规则文件。

2. **`load_config(self)`**：加载 `config.json` 配置文件。如果不存在，则引导用户创建新配置。

3. **`save_config(self)`**：将配置保存到 `config.json` 文件中。

4. **`load_rules(self)`**：从 `rules.txt` 中加载过滤违规评论的规则。

5. **`get_csrf(self, cookie)`**：从 Bilibili 的 Cookie 中提取 CSRF Token。

6. **`get_videos(self)`**：从 Bilibili 获取推荐视频的 `avid` 列表。

7. **`get_replys(self, avid)`**：根据视频的 `avid` 获取评论列表。

8. **`is_porn(self, text)`**：使用加载的规则检测评论内容是否违规。

9. **`req_bili_report_api(self, data)`**：调用 Bilibili 举报 API 对违规评论进行举报。

10. **`report(self, data, r)`**：通过邮件和 Bilibili API 进行举报，发送违规评论的详细信息。

11. **`process_reply(self, reply)`**：处理单条评论，调用 `is_porn()` 判断是否违规，并调用 `report()` 进行举报。

12. **`bvid_to_avid(self, bvid)`**：根据 `bvid` 获取对应的视频 `avid`。

#### 命令行教程
- 启动程序后，用户可以选择自动获取推荐视频评论或手动输入 `bvid` 来分析评论：
  - 输入 `1`：自动抓取推荐视频的评论。
  - 输入 `2`：手动输入 `bvid` 来获取并处理该视频的评论。

---

## GUI 介绍

### GUI 功能概述

图形化界面（GUI）通过 PyQt6 实现，允许用户在更友好的环境下进行操作。用户可以手动输入 `bvid` 或通过内嵌的浏览器预览视频并提取 `bvid`。

### 主界面功能

#### 左侧布局

- **当前处理的视频**：显示当前正在处理的视频的 `bvid`。
- **违规统计标签**：显示本次会话中的违规评论数量和累计检测到的违规评论总数。
- **评论表格**：展示处理过的评论内容及其状态（正常/违规）。
- **日志区域**：显示处理日志，告知用户当前执行的操作。
- **手动输入 bvid 按钮**：允许用户手动输入视频的 `bvid`，点击按钮后开始处理该视频的评论。
- **自动获取推荐视频按钮**：自动获取 Bilibili 推荐视频并分析其评论。

#### 右侧布局

- **网页预览器**：加载 Bilibili 的主页，用户可以通过该浏览器正常访问 Bilibili 网站并选择视频。
- **识别当前视频按钮**：通过提取网页 URL 中的 `bvid`，分析该视频的评论。

---

### GUI 函数详解

#### 类：`MainWindow`

1. **`__init__(self)`**：初始化窗口，设置布局，加载所有控件。
   
2. **`initUI(self)`**：初始化用户界面的布局、控件和信号连接。

3. **`start_processing(self)`**：手动输入 `bvid` 并开始处理该视频的评论。

4. **`auto_get_videos(self)`**：自动获取推荐视频并分析评论。

5. **`start_comment_processing(self, avids)`**：启动评论处理线程，分析传入的 `avid` 列表中的所有视频。

6. **`add_comment_to_table(self, reply)`**：将处理过的评论添加到表格中，并根据检测结果设置其状态（正常/违规）。

7. **`update_video_label(self, avid)`**：更新当前处理的视频标签。

8. **`update_violation_count(self, is_violation)`**：根据检测结果更新违规评论统计。

9. **`log_message(self, message)`**：在日志区域显示消息。

10. **`toggle_task(self)`**：根据当前的任务状态，提取当前视频的 `bvid` 并启动或终止评论分析任务。

11. **`extract_bvid_from_url(self, url)`**：从当前网页的 URL 中提取 `bvid`，用于分析当前视频的评论。

---

## GUI 调用教程

### 启动 GUI
1. 安装所有依赖库：`PyQt6`、`requests`、`smtplib`。
   ```bash
   pip install PyQt6 requests
