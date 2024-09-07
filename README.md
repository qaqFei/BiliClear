---

# BiliClear & GPT 判别系统 🎯

BiliClear 是一个可以批量举报B站`麦片`和违规评论的程序，支持自动化处理并且整合了 OpenAI GPT 模型以辅助判断评论是否违规。支持两种运行模式：命令行模式（主程序）和图形界面模式（GUI），适合用户的不同需求。

---

## 一、使用方法 💡

### 1. 源码使用：
1. 克隆项目并安装依赖：
   ```bash
   git clone https://github.com/qaqFei/BiliClear.git
   cd BiliClear
   pip3 install -r requirements.txt
   ```

2. 运行主程序：
   ```bash
   python3 biliclear.py
   ```

### 2. 启动 GUI 程序：
1. 运行 GUI：
   ```bash
   python3 gui.py
   ```

### 3. 使用 OpenAI GPT 模型辅助判别：

为了检测评论中的违规内容，程序提供了通过 OpenAI 的 GPT 模型进行自动化分析的功能。这些分析功能被封装在 `gpt.py` 文件中。

#### 3.1 GPT 辅助判别功能：
1. **GPT 处理成人内容检测**：
   使用 `gpt_porn` 函数检测评论中是否包含成人或明确的色情内容。

   - **调用方式**：
     ```python
     from gpt import gpt_porn
     
     api_key = "your_openai_api_key"
     content = "检测的评论内容"
     
     is_porn = gpt_porn(content, api_key)
     print(is_porn)  # 返回 True 表示包含成人内容，False 表示不包含。
     ```

2. **GPT 处理广告内容检测**：
   使用 `gpt_ad` 函数检测评论中是否包含广告或推广内容。

   - **调用方式**：
     ```python
     from gpt import gpt_ad
     
     api_key = "your_openai_api_key"
     content = "检测的评论内容"
     
     # 允许检测含有 @ 字符的广告评论
     is_ad = gpt_ad(content, api_key, need_at=True)
     print(is_ad)  # 返回 True 表示包含广告内容，False 表示不包含。
     ```

   - `gpt_ad` 函数有两个可选参数：
     - `content`: 评论内容。
     - `need_at`: 是否只检查带有 `@` 的评论。

---

## 二、配置文件（`config.json`） 📝
首次运行程序时，系统会提示输入必要的配置参数，并生成 `config.json` 文件。该文件用于存储用户的配置信息，如 `SMTP` 服务器信息、B站 `cookie` 等。

#### 配置项：
- **`sender_email`**: 发送举报邮件的邮箱。
- **`sender_password`**: 邮箱的 `SMTP` 密钥。
- **`headers`**: 请求头信息，包括 B站的 `cookie`。
- **`smtp_server`**: 邮箱的 `SMTP` 服务器地址。
- **`smtp_port`**: `SMTP` 服务器端口。
- **`bili_report_api`**: 是否调用 B站的举报 API。
- **`csrf`**: 请求 API 所需的 CSRF 令牌。
- **`reply_limit`**: 单个视频最大评论数。

---

## 三、GPT 判别辅助功能详细说明 💻

### gpt.py 中的主要函数：

#### 1. `gpt_porn(content, apikey)`
- **功能**：检测文本中是否包含成人或色情内容。
- **参数**：
  - `content`: 需要检测的评论内容（文本）。
  - `apikey`: OpenAI API 的密钥，用于调用 GPT 模型。
- **返回**：`True` 表示评论包含成人内容，`False` 表示评论不包含成人内容。

#### 2. `gpt_ad(content, apikey, need_at=True)`
- **功能**：检测文本中是否包含广告或推广内容。
- **参数**：
  - `content`: 需要检测的评论内容（文本）。
  - `apikey`: OpenAI API 的密钥，用于调用 GPT 模型。
  - `need_at`: 可选参数，默认为 `True`，表示仅检测含有 `@` 字符的广告。如果设置为 `False`，则检测所有广告评论。
- **返回**：`True` 表示评论包含广告内容，`False` 表示评论不包含广告内容。

---

## 四、主程序核心功能 🛠️

### 主要函数介绍：

#### `saveConfig()`
- **功能**：保存当前配置信息至 `config.json` 文件。

#### `getCsrf(cookie: str) -> str`
- **功能**：从用户提供的 B站 `cookie` 中解析并提取 `csrf` 令牌。

#### `getVideos() -> list`
- **功能**：从 B站获取推荐视频列表。

#### `getReplys(avid: str | int) -> list`
- **功能**：根据视频 `avid` 获取对应的评论。

#### `isPorn(text: str) -> Tuple[bool, str]`
- **功能**：检测评论文本是否包含违规内容（如色情内容）。

#### `report(data: dict, rule: str)`
- **功能**：举报违规评论，并将举报信息发送到 B站和用户配置的邮箱。

---

## 五、GUI 程序功能介绍 🖥️

GUI 提供了一个直观的用户界面来管理 B站评论检测和举报。其功能与主程序高度集成，允许用户手动输入视频 ID 或自动获取推荐视频。

### 界面功能说明：
1. **输入框**：用户可以手动输入 B站视频的 `bvid`。
2. **评论表格**：展示视频的评论和其违规状态。
3. **日志区**：实时显示程序运行状态和处理记录。
4. **统计信息**：显示处理视频数量、评论数量以及违规率。
5. **预览窗口**：显示当前处理视频的 B站页面，支持在浏览器中打开。

### GUI 中的主要函数：

#### `start_processing(self)`
- **功能**：启动手动输入视频的评论处理。

#### `auto_get_videos(self)`
- **功能**：自动获取 B站推荐视频，并处理评论。

#### `add_comment_to_table(self, reply: dict)`
- **功能**：将评论添加到评论表格，并显示违规状态。

#### `update_stats_label(self)`
- **功能**：更新界面上的统计数据。

#### `log_message(self, message: str)`
- **功能**：将日志信息输出到日志区域。

---

通过整合 OpenAI GPT 模型与 BiliClear 的主程序，程序在违规评论的自动化检测、举报上达到了更高的准确度和智能化水平。通过 GUI 界面，用户可以更加直观、便捷地管理B站视频评论的检测和举报操作。
