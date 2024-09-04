# BiliClear
- 这是一个可以批量举报B站`麦片`的程序
- 需python版本>=`3.12`

## 使用
- 程序第一次启动时需输入的参数:
    - `Report sender email: ` 发送举报邮件的邮箱
    - `Report sender password: ` 发送举报邮件邮箱的`SMTP`密钥, 不是密码!!!  (输入无回显)
    - `Bilibili cookie: ` 是`bilibli cookie`  需定期修改`config.json`更新 (输入无回显)
    - `SMTP server: ` 邮箱的`smtp`服务器地址, 会列出常用的
    - `SMTP port: ` 邮箱的`smtp`服务器端口, 会列出常用的

- 程序运行出现异常 (与`config.json`相关的):
    - 修改`config.json`, 更新`bilibili cookie`, 修改邮箱`SMTP`密钥
    - 删除`config.json`, 重新输入参数
    - 在版本更新时建议删除`config.json`, 重新生成, 特别是出现`KeyError`时

- `bilibili cookie`过期导致的现象
    - 获取评论为空, 不会输出

- `smtp`服务器选择
    - 选择所使用的邮件的`smtp`服务器, 会列出常用的

## 开发贡献
- 过滤规则
    - 规则在`rules.txt`中, 只要有任何一个匹配, 就会判定为违规
    - `rules.txt`每一行为一个`python`表达式
    - 变量: `text`, 评论的语句, 类型: `str`
    - 在表达式中不允许使用`eval`和`exec`等函数
    - 可使用正则表达式, 调用`re`模块即可 (默认自动导入)
