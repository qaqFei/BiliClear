![BiliClear](https://socialify.git.ci/qaqFei/BiliClear/image?description=1&descriptionEditable=Report%20violating%20Bilibili%20users%20in%20batches.&font=Jost&forks=1&issues=1&language=1&name=1&owner=1&pattern=Charlie%20Brown&pulls=1&stargazers=1&theme=Auto)

# BiliClear 🎯

- BiliClear 是一个可以**批量举报B站“麦片评论”**的程序 🚨
- 该程序基于 **Python 3.12 及以上版本** 🐍

---

## 界面演示 👁️

- **QT GUI**
  
  ![QT GUI 演示](https://github.com/qaqFei/BiliClear/blob/main/README%20res/QT_GUI%E6%BC%94%E7%A4%BA.png)
  
- **WebUI**
  
  ![WebUI 演示](https://github.com/qaqFei/BiliClear/blob/main/README%20res/WebUI%E6%BC%94%E7%A4%BA.png)
  
- **GUI 初始化（适用于 WebUI 和 QT GUI）**
  
  ![GUI 初始化演示](https://github.com/qaqFei/BiliClear/blob/main/README%20res/GUI%E5%88%9D%E5%A7%8B%E5%8C%96%E6%BC%94%E7%A4%BA.png)

  *（注意：实际使用可能不是深色模式，演示截图为修改过窗口框架的 Windows 11 系统）*

---

## 使用方法 💡

### 0. 自动安装版本

- 直接下载并运行 `release-0.3` 中提供的 `installer.exe` 安装程序（适合完全不懂技术的小白）。
- 对于其他操作系统用户，请使用源码手动安装。

### 1. 源码安装

- 克隆项目并安装依赖：
  
  ```bash
  git clone https://github.com/qaqFei/BiliClear.git
  cd BiliClear
  pip3 install -r ./requirements.txt
  ```
  
  如果您使用多 Python 环境，建议使用以下命令：
  
  ```bash
  pip install -r ./requirements.txt
  ```

### 2. 启动程序

- **WebUI 仅限 Windows 使用**，您可以通过以下命令启动对应版本的 BiliClear：

  ```bash
  # 启动 QT GUI（功能更完善，支持控制台日志重定向）
  python ./biliclear_gui_qt.py

  # 启动 WebUI（适配性更强）
  python ./biliclear_gui_webui.py

  # 启动命令行版本（性能最好，直接运行举报逻辑）
  python ./biliclear.py
  ```

- **首次启动程序时**，需提供以下参数：
  - `Report sender email`: 📧 发送举报邮件的邮箱地址
  - `Report sender password`: 🔑 邮箱的 SMTP 密钥（注意不是邮箱密码！）
  - `Bilibili cookie`: 🍪 Bilibili 的 Cookie，需定期更新
  - `SMTP server`: ✉️ SMTP 服务器地址，常见邮箱服务器会列出选项
  - `SMTP port`: 🚪 SMTP 服务器端口

### 3. 处理异常

- **与 `config.json` 相关的异常**：
  - 更新 `config.json` 内的 Bilibili Cookie 或邮箱 SMTP 密钥
  - 如果问题无法解决，可以删除 `config.json` 文件，重新输入参数
  - 更新版本时建议删除旧的 `config.json` 文件，以防止 `KeyError` 错误

- **QT GUI 相关错误**：
  - 如果使用 QT GUI 时程序报错，请报告错误信息。两个常见错误及处理方式：
    1. **错误代码：-1073740940 (0xC0000374)**：问题可能与内存堆损坏有关。
    2. **错误代码：-1073741819 (0xC0000005)**：问题可能与跨线程内存访问被拒绝有关。

    若遇到上述问题，您可以尝试重新运行程序。目前尚无具体的复现或解决方案，欢迎有能力的开发者帮助解决 QT GUI 相关问题！

### 4. Cookie 过期提醒

- 如果 `Bilibili cookie` 过期，可能导致获取评论为空，程序不会输出任何内容。请及时更新 Cookie。

### 5. SMTP 服务器选择

- 程序启动时，会提供常见邮箱的 SMTP 服务器选项，请选择对应的邮箱服务并提供相关端口。

---

## 项目职责分工 👥

- **qaqFei** 负责：
  - **WebUI** 的编写
  - 项目的主要逻辑判断
  - 主程序的开发与维护
  - 其他代码的的开发与维护
  - 项目拥有者

- **Felix3322** 负责：
  - **QT GUI** 的开发与维护
  - **GUI 配置（guiconfig）**
  - **安装程序（installer）**
  - **GPT 功能的实现**

---

## `config.json` 配置文件 📝

`config.json` 文件用于存储程序所需的基本配置参数：

- `sender_email`: 📧 发送举报邮件的邮箱
- `sender_password`: 🔑 邮箱的 SMTP 密钥
- `headers`: Bilibili API 请求头，包含以下信息：
  - `User-Agent`: 浏览器标识
  - `Cookie`: Bilibili 的 Cookie
- `smtp_server`: ✉️ SMTP 服务器地址
- `smtp_port`: 🚪 SMTP 服务器端口
- `bili_report_api`: 📡 是否调用 Bilibili 的举报 API
- `csrf`: 🔐 Bilibili API 请求体中的 CSRF 令牌
- `reply_limit`: 🔒 获取评论的最大数量，建议不超过 100，以防被风控
- `enable_gpt`: 🤖 是否启用 GPT 进行评论过滤
- `gpt_apibase`: GPT 的 API 地址
- `gpt_proxy`: GPT 代理地址
- `gpt_apikey`: GPT API 密钥
- `gpt_model`: GPT 模型名称
- `enable_email`: 📧 是否启用邮件发送功能
- `enable_check_lv2avatarat`: 📷 是否启用评论检查，过滤带有头像的评论

---

## 开发贡献 🤝

- **过滤规则**：
  - 过滤规则存储在 `./res/rules.yaml` 文件中，您可以根据需要自行调整。

---

## 声明 ⚠️

使用 `BiliClear` 造成的任何后果由用户自行承担，开发者不对此负责。请谨慎使用该工具。

---

## License 📄

BiliClear 使用 [MIT License](LICENSE)。

---

该版本只针对 QT GUI 的问题做了详细说明，其他部分保持不变。