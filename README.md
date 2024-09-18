![BiliClear](https://socialify.git.ci/qaqFei/BiliClear/image?description=1&descriptionEditable=Report%20violating%20Bilibili%20users%20in%20batches.&font=Jost&forks=1&issues=1&language=1&name=1&owner=1&pattern=Charlie%20Brown&pulls=1&stargazers=1&theme=Auto)

# BiliClear 🎯
- `BiliClear` 是一个可以批量举报B站不良信息的程序 🚨
- `BiliClear`需使用 **Python 3.12 及以上版本** 🐍

---

## 使用方法 💡

### 1. 源码安装
- 克隆项目并安装依赖：
  ```bash
  git clone https://github.com/qaqFei/BiliClear.git
  cd BiliClear
  pip install -r ./requirements.txt
  ```

### 2. 启动程序
- **WebUI 仅限 Windows 使用**, 您可以通过以下命令启动对应版本的 BiliClear：
  ```bash
  # 启动 WebUI
  python ./biliclear_gui_webui.py

  # 启动命令行版本
  python ./biliclear.py
  ```

### 3. 处理异常
- **与 `config.json` 相关的异常**：
  - 如果问题无法解决, 可以删除 `config.json` 文件

### 4. 规则的更新
- 规则文件更新源存放在 `./RULE_SOURCE` 文件中, 包含规则文件的链接, 您可以自行更改规则文件更新源

---

## `config.json` 配置文件 📝
- `headers`: 📨 B站api的请求头
    - `User-Agent`: 🔍 浏览器标识
    - `Cookie`: 🍪 B站api的请求头中的 `Cookie`
- `bili_report_api`: 📡 是否调用B站api的举报接口
- `reply_limit`: 🔒 单条视频获取评论的最大数量 尽量不要大于100 可能会被风控
- `enable_gpt`: 🤖 是否启用GPT进行评论过滤
- `gpt_apibase`: 🔗 GPT的API地址
- `gpt_proxy`: 🔗 GPT的代理地址
- `gpt_apikey`: 🔑 GPT的API密钥
- `gpt_model`: 🧠 GPT的模型名称
- `enable_check_lv2avatarat`: 📷 启用检查评论是否包含头像 (前置: lv.2, 包含@)
- `enable_check_replyimage`: 📷 启用识别评论图像 

---

## 开发贡献 🤝
- **过滤规则**：
  - 过滤规则存储在 `./res/rules.yaml` 文件中
  - 结构
    - `rules_exact` 为一个列表 type: `list[list[str] | str]`
       - `list[str]` 为一个字符串列表, 每个字符串代表一个关键词, 在前面添加`$-not `即可对结果取反, 如: `["http", "$-not https", "$-not bilibili", "$-not 163cn.tv"]`
       - `str` 正则表达式
    - `rules_elastic` 模糊匹配的规则 type: `list[str]`

---

## 声明 ⚠️
使用 `BiliClear` 造成的任何后果由用户自行承担, 开发者不对此负责, 请谨慎使用该工具

---

## License 📄
BiliClear 使用 [MIT License](LICENSE)