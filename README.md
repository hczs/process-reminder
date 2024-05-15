# 进程结束提醒工具（Process Reminder）
## 简介
包装耗时的 shell 命令，并在此命令结束后，发送邮件提醒，并附带此命令的所有输出信息（包括正常输出信息和报错信息）

## 安装
1. 克隆项目到本地，并进入项目目录
2. 配置命令全局使用
   - Linux 平台
     ```shell
     sudo cp dist/remind /usr/bin
     ```
   - Windows 平台，需要以管理员身份运行终端窗口
     ```shell
     xcopy dist/remind.exe "C:\Windows\System32\remind.exe" /I
     ```

## 使用
1. 先进行初始化：
   ```shell
    $ remind init
    2024-05-15 15:27:34,548 - INFO - 程序初始化完成，已创建配置文件 /home/xxx/.config/process_reminder.json
    2024-05-15 15:27:34,548 - INFO - 请您先进行配置提醒邮件相关参数再使用此程序
   ```
   
2. 编辑上方初始化后的配置文件，这个 json 文件共有以下配置项，都是必填项
   
   | 配置项 | 说明 | 例子 |
   | ---- | ---- | ---- |
   | sender_smtp_host |邮件发送方 smtp 地址|smtp.163.com|
   | sender_smtp_port |邮件发送方 smtp 端口|25|
   | sender_user |邮件发送方邮箱地址|xxx@163.com|
   | sender_pass |邮件发送方授权码|ABCDEFG|
   | to_address |进程结束提醒接收方邮件地址|aaa@163.com|
   
3. 使用 remind 包装 shell 命令：`remind run -c "python test.py"` 

   ```shell
   $ remind run -c "python test.py"
   2024-05-15 15:37:42,911 - INFO - 命令 [python -u test.py] 开始执行，您可以使用 CTRL + C 来终止命令执行，下方是该命令的输出内容
   current count is 0
   current count is 1
   current count is 2
   2024-05-15 15:37:45,935 - ERROR - 命令 [python -u test.py] 异常运行结束，return code：1
   2024-05-15 15:37:45,936 - ERROR - ==========程序异常输出信息==========
   Traceback (most recent call last):
     File "test.py", line 29, in <module>
       raise "error info"
   TypeError: exceptions must derive from BaseException
   ```

4. 查看帮助：`remind -h`

   ```shell
   $ remind -h
   usage: remind [-h] [-command COMMAND] [-debug] {init,run}
   
   positional arguments:
     {init,run}            操作类型
   
   optional arguments:
     -h, --help            show this help message and exit
     -command COMMAND, -c COMMAND
                           想要执行的 shell 命令
     -debug                启用DEBUG日志
   ```

## 开发

1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 构建：`pyinstaller -F remind.py`
