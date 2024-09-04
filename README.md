# BiliClear
- 这是一个可以批量举报B站`麦片`的程序
- 需python版本>=`3.12`

## 使用
- 程序第一次启动时需输入的参数:
    - `report sender email: ` 发送举报邮件的邮箱
    - `report sender password: ` 发送举报邮件邮箱的`SMTP`密钥, 不是密码!!!  (输入无回显)
    - `bilibili cookie: ` 是`bilibli cookie`  需定期修改`config.json`更新 (输入无回显)
    - `smtp server: ` 邮箱的`smtp`服务器地址, 会列出常用的
    - `smtp port: ` 邮箱的`smtp`服务器端口, 会列出常用的

- 程序运行出现异常 (与`config.json`相关的):
    - 修改`config.json`, 更新`bilibili cookie`, 修改邮箱`SMTP`密钥
    - 删除`config.json`, 重新输入参数
    - 在版本更新时建议删除`config.json`, 重新生成, 特别是出现`KeyError`时

- `bilibili cookie`过期导致的现象
    - 获取评论为空, 不会打印` not porn ......`

- `smtp`服务器选择
    - 选择所使用的邮件的`smtp`服务器, 会列出常用的
    - 如果出现ssl错误, 可尝试更改端口到465或587

## 开发贡献
- 过滤规则
    - 规则在`rules.txt`中, 只要有任何一个匹配, 就会判定为违规
    - `rules.txt`每一行为一个`python`表达式
    - 变量: `text`, 评论的语句, 类型: `str`
    - 在表达式中不允许使用`eval`和`exec`等函数
    - 可使用正则表达式, 调用`re`模块即可 (默认自动导入)
## 青龙面板使用
- 配置环境
    - 在`配置环境`-`config.sh`中增加拉取文件后缀txt和json
    ```
    ## ql repo命令拉取脚本时需要拉取的文件后缀，直接写文件后缀名即可
    RepoFileExtensions="js py json txt"
    ```
    - 增加SMTP服务相关信息(脚本从这个位置获取邮件信息，若不填写，后续运行脚本需手动填写邮箱信息)
    ```
    ## 14. SMTP
    ## 邮箱服务名称，比如126、163、Gmail、QQ等，支持列表 https://github.com/nodemailer/nodemailer/blob/master/lib/well-known/services.json
    export SMTP_SERVICE=""
    ## smtp_email 填写 SMTP 收发件邮箱，通知将会由自己发给自己
    export SMTP_EMAIL=""
    ## smtp_password 填写 SMTP 登录密码，也可能为特殊口令，视具体邮件服务商说明而定
    export SMTP_PASSWORD=""
    ## smtp_name 填写 SMTP 收发件人姓名，可随意填写
    export SMTP_NAME="青龙"
    ```
- 开始使用
    - `订阅管理`-`创建订阅`。按以下格式填写
    ```
    名称：bili自动举报
    类型：公开仓库
    链接：https://github.com/qaqFei/BiliClear.git
    定时类型：crontab
    定时规则：2 2 28 * *
    ```
    其他都不用填写
    完成创建后点击运行，拉取仓库
    - 回到`定时任务`页面，页面中会有一些多余任务，只保留`bilibili举报违规`
    - 先运行一次`bilibili举报违规`让他获取配置。之后可无人值守自动运行
- 注意事项
    - 脚本默认每天7点21运行，`无结束时间`，需要手动停止！




