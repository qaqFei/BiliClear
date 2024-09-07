# BiliClear 🎯
- 这是一个可以批量举报B站`麦片`的程序 🚨
- **需要 Python 版本 >= `3.12`** 🐍

## 使用方法 💡
1. **源码使用：**
   运行以下命令进行使用前的初始化：

   ```bash
   git clone https://github.com/qaqFei/BiliClear.git
   cd BiliClear
   pip3 install -r requirements.txt
   python3 biliclear.py
   ```

2. **启动程序：**
   - **GUI仅限Windows可用**

   - 程序第一次启动时，需输入以下参数：
      - `Report sender email`: 📧 发送举报邮件的邮箱
      - `Report sender password`: 🔑 邮箱的 `SMTP` 密钥，不是密码！（输入无回显）
      - `Bilibili cookie`: 🍪 需定期更新 `config.json` 内的 `Bilibili cookie`（输入无回显）
      - `SMTP server`: ✉️ 邮箱的 `SMTP` 服务器地址，会列出常用的选项
      - `SMTP port`: 🚪 `SMTP` 服务器端口

3. **处理异常：**
   若与 `config.json` 相关的异常出现，处理方式如下：
   - 修改 `config.json`，更新 `bilibili cookie` 或修改邮箱 `SMTP` 密钥
   - 删除 `config.json`，重新输入参数
   - 版本更新时建议删除 `config.json`，避免出现 `KeyError`

4. **Cookie 过期提示：**
   - 如果 `bilibili cookie` 过期，可能导致获取评论为空，程序不会输出任何内容。

5. **SMTP 服务器选择：**
   - 请选择对应的邮箱服务的 `SMTP` 服务器，会列出常见的服务器选项。

## `config.json` 配置文件 📝
- `sender_email`: 📧 发送举报邮件的邮箱
- `sender_password`: 🔑 邮箱的 `SMTP` 密钥
- `headers`: 📨 B站api的请求头
- `smtp_server`: ✉️ 邮箱的 `SMTP` 服务器地址
- `smtp_port`: 🚪 `SMTP` 服务器端口
- `bili_report_api`: 📡 是否调用B站api的举报接口
- `csrf`: 🔐 B站api请求体中的 `csrf`
- `reply_limit`: 🔒 单条视频获取评论的最大数量 尽量不要大于100 可能会被风控

## 开发贡献 🤝
- **过滤规则：**
  过滤规则在 `rules.txt` 文件中，每一行为一个 Python 表达式，只要有任何一个匹配即判定为违规。
  - 变量：`text`，评论内容，类型为 `str`
  - 表达式中禁止使用 `eval`、`exec` 等函数
  - 可使用正则表达式，默认导入 `re` 模块

## 声明 ⚠️
使用 `BiliClear` 造成的任何不良后果由使用者自行承担，开发者不承担任何责任。请谨慎使用。

---

**License:** MIT 📄
