import argparse
import json
import logging
import os.path
import re
import smtplib
import subprocess
import sys
from email.mime.text import MIMEText

from platformdirs import user_config_dir


def init_logger(logger_level=logging.INFO):
    """
    初始化日志记录器

    :param logger_level: 日志打印等级
    :return: logger实例
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logger_level)

    # 日志输出到控制台
    handler = logging.StreamHandler()
    handler.setLevel(logger_level)

    # 日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    _logger.addHandler(handler)
    if logger_level == logging.DEBUG:
        _logger.debug("已启动DEBUG模式")
    return _logger


def get_default_config() -> (str, dict):
    """
    获取默认的配置文件路径

    :return: 配置文件路径, 默认配置信息
    """
    config_folder = user_config_dir()
    default_config_file_path = os.path.join(config_folder, "process_reminder.json")
    default_config_dict = {
        "sender_smtp_host": "",
        "sender_smtp_port": 25,
        "sender_user": "",
        "sender_pass": "",
        "to_address": ""
    }
    return default_config_file_path, default_config_dict


def get_config() -> (str, dict):
    """
    config 初始化

    :return: (配置文件路径，配置字典对象)
    """
    default_config_file_path, _ = get_default_config()
    if not os.path.exists(default_config_file_path):
        logger.error("程序未初始化，请先执行初始化操作，操作命令：remind init")
        sys.exit(0)
    else:
        with open(default_config_file_path, "r") as f:
            _config_dict = json.load(f)
    return default_config_file_path, _config_dict


def check_config(cfg_path: str, cfg_dict: dict) -> None:
    """
    检查配置文件是否有空值

    :param cfg_path: 配置文件路径
    :param cfg_dict: 配置文件字典
    :return:
    """
    empty_keys = [key for key, value in cfg_dict.items() if not value]
    if empty_keys:
        logger.warning(f"检测到配置文件 {cfg_path} 中，以下配置项为空, 请补充完整配置文件后再运行")
        logger.warning(', '.join(empty_keys))
        sys.exit(0)


def execute_command(command: str, cfg_path: str, cfg_dict: dict) -> None:
    """
    执行 shell 命令

    :param command: shell 命令
    :param cfg_path: 配置文件路径
    :param cfg_dict: 配置文件字典
    :return: None
    """
    # 检查配置文件
    check_config(cfg_path, cfg_dict)
    # 匹配python脚本命令的正则表达式
    py_script_pattern = r'^python\s+\w+\.py.*$'
    # python 脚本命令添加 -u 参数 强制不缓冲标准输出和标准错误流 程序可以实时输出对应内容
    if re.match(py_script_pattern, command):
        command = command.replace("python ", "python -u ")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               bufsize=1,
                               universal_newlines=True)
    logger.info("命令 [{}] 开始执行，您可以使用 CTRL + C 来终止命令执行，下方是该命令的输出内容".format(command))
    process_output = []
    try:
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
            process_output.append(line)
    except KeyboardInterrupt:
        process.kill()

    process.wait()

    # 检查进程是否成功结束
    remind = False
    process_status = ''
    process_output = '=' * 10 + '程序标准输出信息' + '=' * 10 + '\n' + ''.join(process_output)
    if process.returncode == 0:
        process_status = "命令 [{}] 正常运行结束".format(command)
        logger.info(process_status)
    elif process.returncode == -9:
        remind = False
        logger.info("命令 [{}] 已停止".format(command))
    else:
        process_status = "命令 [{}] 异常运行结束，return code：{}".format(command, process.returncode)
        logger.error(process_status)
        error_log = '=' * 10 + '程序异常输出信息' + '=' * 10 + '\n' + ''.join(process.stderr.readlines())
        logger.error(error_log)
        process_output += error_log
    if remind:
        send_result_mail(process_status, cfg_dict, process_output)


def send_result_mail(process_status: str, cfg_dict: dict, process_output: str) -> None:
    """
    发送进程运行结束提醒邮件

    :param process_status: 进程最终状态
    :param cfg_dict: 配置字典
    :param process_output: 进程输出内容
    :return: None
    """
    user = cfg_dict['sender_user']
    password = cfg_dict['sender_pass']
    msg = MIMEText(process_output, 'plain', _charset="utf-8")
    msg["Subject"] = process_status
    to_address = cfg_dict['to_address']
    try:
        with smtplib.SMTP(host=cfg_dict['sender_smtp_host'], port=cfg_dict['sender_smtp_port']) as smtp:
            smtp.login(user=user, password=password)
            smtp.sendmail(from_addr=user, to_addrs=to_address.split(','), msg=msg.as_string())
            logger.info("提醒邮件发送成功！目标邮箱：{}".format(to_address))
    except smtplib.SMTPException as ex:
        logger.error("发送邮件异常，目标邮箱：{}  异常信息：{}".format(to_address, ex))


def program_init() -> None:
    """
    程序初始化

    :return: None
    """
    default_config_file_path, default_config_dict = get_default_config()
    if not os.path.exists(default_config_file_path):
        with open(default_config_file_path, "w") as f:
            json.dump(default_config_dict, f, indent=4)
        logger.info(f"程序初始化完成，已创建配置文件 {default_config_file_path}")
        logger.info("请您先进行配置提醒邮件相关参数再使用此程序")
    else:
        logger.info(f"程序已完成初始化，无需进行重复初始化操作，配置文件路径：{default_config_file_path}")


if __name__ == '__main__':
    # 参数封装解析
    parser = argparse.ArgumentParser()
    parser.add_argument('type', help='操作类型', choices=['init', 'run'])
    parser.add_argument('-command', '-c', help='想要执行的 shell 命令')
    parser.add_argument('-debug', action='store_true', help='启用DEBUG日志')
    args = parser.parse_args()
    opt_type = args.type
    enable_debug = args.debug
    # 参数校验
    # 根据操作类型检查 -c 参数
    if args.type == 'run' and not args.command:
        parser.error('请使用 -command 或 -c 参数来传入想要执行的 shell 命令')
        sys.exit(0)

    # 日志记录器初始化
    logger = init_logger(logging.DEBUG if enable_debug else logging.INFO)
    if opt_type == "init":
        program_init()
    elif opt_type == "run":
        config_file_path, config_dict = get_config()
        execute_command(args.command, config_file_path, config_dict)
