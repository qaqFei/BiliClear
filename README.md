![BiliClear](https://socialify.git.ci/qaqFei/BiliClear/image?description=1&descriptionEditable=Report%20violating%20Bilibili%20users%20in%20batches.&font=Jost&forks=1&issues=1&language=1&name=1&owner=1&pattern=Charlie%20Brown&pulls=1&stargazers=1&theme=Auto)
# BiliClear 🎯
- 这是一个可以批量举报B站`麦片评论`的程序 🚨
- **需要 Python 版本 >= `3.12`** 🐍

## 使用方法 💡
1. **源码使用：**
   运行以下命令进行使用前的初始化：

   ```bash
   git clone https://github.com/qaqFei/BiliClear.git
   cd BiliClear
   pip3 install -r ./requirements.txt
   ```
   如果是多Python环境，请运行以下命令进行使用前的初始化：
   ```bash
   git clone https://github.com/qaqFei/BiliClear.git
   cd BiliClear
   pip install -r ./requirements.txt
   ```

2. **启动程序：**
   - **WebUI仅限Windows可用**
   - 使用以下命令启动BiliClear
   ```bash
   #启动 QT GUI (功能更完善，现已支持重定向控制台日志)
   python ./biliclear_gui_qt.py
   #启动 WebUI (适配更及时)
   python ./biliclear_gui_webui.py
   #启动命令行 (直接运行逻辑, 性能最好)
   python ./biliclear.py
   ```
   - 程序第一次启动时，需输入以下参数：
    - `Report sender email`: 📧 发送举报邮件的邮箱
    - `Report sender password`: 🔑 邮箱的 `SMTP` 密钥，不是密码！（输入无回显）
    - `Bilibili cookie`: 🍪 需定期更新 `config.json` 内的 `Bilibili cookie`（输入无回显）
    - `SMTP server`: ✉️ 邮箱的 `SMTP` 服务器地址，会列出常用的选项
    - `SMTP port`: 🚪 `SMTP` 服务器端口

3. **处理异常：**
   - 若与 `config.json` 相关的异常出现，处理方式如下：
      - 修改 `config.json`，更新 `bilibili cookie` 或修改邮箱 `SMTP` 密钥
      - 删除 `config.json`，重新输入参数
      - 版本更新时建议删除 `config.json`，避免出现 `KeyError`
   - 若与 QT GUI 有关：
      - 请报告错误
      - 目前有一个完全没有头绪的BUG：`进程已结束，退出代码为 -1073740940 (0xC0000374)` 似乎和`堆已损坏`有关，若有大佬能解决，十分感谢！
      - 目前还有一个完全没有头绪的BUG：`进程已结束，退出代码为 -1073741819 (0xC0000005)` 似乎和`跨线程内存访问被拒绝`有关，若有大佬能解决，十分感谢！（目前找到的最相关的信息[stackoverflow](https://stackoverflow.com/questions/71966027/how-to-catch-pyqt5-exception-process-finished-with-exit-code)）
      - 若出现这两个退出代码直接重新运行程序即可，目前没有确切的复现方法

4. **Cookie 过期提示：**
   - 如果 `bilibili cookie` 过期，可能导致获取评论为空，程序不会输出任何内容。

5. **SMTP 服务器选择：**
   - 请选择对应的邮箱服务的 `SMTP` 服务器，会列出常见的服务器选项。

## `config.json` 配置文件 📝
- `sender_email`: 📧 发送举报邮件的邮箱
- `sender_password`: 🔑 邮箱的 `SMTP` 密钥
- `headers`: 📨 B站api的请求头
    - `User-Agent`: 🔍 浏览器标识
    - `Cookie`: 🍪 B站api的请求头中的 `Cookie`
- `smtp_server`: ✉️ 邮箱的 `SMTP` 服务器地址
- `smtp_port`: 🚪 `SMTP` 服务器端口
- `bili_report_api`: 📡 是否调用B站api的举报接口
- `csrf`: 🔐 B站api请求体中的 `csrf`
- `reply_limit`: 🔒 单条视频获取评论的最大数量 尽量不要大于100 可能会被风控
- `enable_gpt`: 🤖 是否启用GPT进行评论过滤
- `gpt_apibase`: 🔗 GPT的API地址
- `gpt_proxy`: 🔗 GPT的代理地址
- `gpt_apikey`: 🔑 GPT的API密钥
- `gpt_model`: 🧠 GPT的模型名称
- `enable_email`: 📧 是否启用邮件发送
- `enable_check_lv2avatarat`: 📷 是否启用检查评论是否包含头像 (前置: lv.2, 包含@)

## 开发贡献 🤝
- **过滤规则：**
    - 过滤规则在 `./res/rules.yaml` 文件中
    - 这个实现了, 还没有写文档...

## 声明 ⚠️
使用 `BiliClear` 造成的任何不良后果由使用者自行承担，开发者不承担任何责任。请谨慎使用。

---

**License:** MIT 📄
