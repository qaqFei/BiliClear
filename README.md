# BiliClear
- 这是一个可以批量举报B站`麦片`的程序
- 需python版本>=`3.12`

## 使用
- 程序第一次启动时需输入的参数:
    - `report sender email: ` 发送举报邮件的邮箱 (必须为163邮箱)
    - `report sender password: ` 发送举报邮件邮箱的`STMP`密钥, 不是密码!!!  (输入无回显)
    - `bilibili cookie: ` 是`bilibli cookie`  需定期修改`config.json`更新 (输入无回显)
- 程序运行出现异常 (与`config.json`相关的):
    - 修改`config.json`, 更新`bilibili cookie`, 修改邮箱`STMP`密钥
    - 删除`config.json`, 重新输入参数
- `bilibili cookie`过期导致的现象
    - 获取评论为空, 不会打印` not porn ......`