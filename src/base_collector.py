# -*- coding: utf-8 -*-
# @Time    : 2025/11/19 22:22
# @Author  : Yuling Hou
# @File    : base_collector.py
# @Software: PyCharm
from socket import socket
import paramiko
import time
from pathlib import Path
from common import get_current_time, get_target_info, print_to_logfile


class Collector:
    def __init__(self, ip, type, port, username, password, command, target, target_info, gen, remark):
        self.ip = ip
        self.type = type
        self.port = port
        self.gen = gen
        self.remark = remark
        self.username = username
        self.password = password
        self.command = command
        self.target = target
        self.target_info = target_info

        self.tags = {
            "testbed": target_info["testbed"],
            "name": target_info["name"],
            "type": target_info["type"],
            "model": target_info["model"],
            "ip": target_info["ip"],
            "syslog": target_info["log_ip"],
            "gen": target_info["gen"],
            "remark": target_info["remark"]
        }

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 添加传输层优化
        self.ssh.get_transport() if self.ssh.get_transport() else None

        Path(f"{Path.cwd().parent}/logs/{self.type}/raw_data").mkdir(
            parents=True, exist_ok=True
        )
        Path(f"{Path.cwd().parent}/logs/{self.type}/history").mkdir(
            parents=True, exist_ok=True
        )

        self.text_file = f"{Path.cwd().parent}/logs/{self.type}/raw_data/{self.target}_{self.type}.txt"
        self.history_file = f"{Path.cwd().parent}/logs/{self.type}/history/{self.target}_{self.type}_history.txt"

    def robust_ssh_connect(self, max_retries=3, retry_delay=5):
        """增强的SSH连接方法，包含重试机制"""
        for attempt in range(max_retries):
            try:
                self.ssh.connect(
                    hostname=self.ip,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    look_for_keys=False,
                    allow_agent=False,
                    banner_timeout=60,
                    timeout=60,
                    auth_timeout=60
                )
                return True
            except (paramiko.SSHException, socket.error, EOFError) as e:
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} SSH连接尝试 {attempt + 1}/{max_retries} 失败: {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    # 重新创建SSH客户端
                    self.ssh.close()
                    self.ssh = paramiko.SSHClient()
                    self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                else:
                    return False
        return False

    def wait_for_prompt(self, channel, expect_bytes, timeout=30):
        """增强的等待提示符方法"""
        output = b""
        start = time.time()
        while time.time() - start < timeout:
            if channel.recv_ready():
                chunk = channel.recv(4096)  # 增加缓冲区大小
                output += chunk
                if expect_bytes in output:
                    return output
            time.sleep(0.5)

        # 超时但返回已有输出，而不是直接抛出异常
        return output

    def ssh_connect(self, count):
        """优化的SSH连接方法"""
        self.channel = None
        try:
            # 使用增强的连接方法
            if not self.robust_ssh_connect(max_retries=3, retry_delay=10):
                raise Exception("SSH连接失败，已重试3次")

            self.channel = self.ssh.invoke_shell(term='vt100', width=200, height=50)
            time.sleep(3)

            # 设置通道超时
            self.channel.settimeout(30)

            # 读取初始输出
            initial_output = self.wait_for_prompt(self.channel, b'>', timeout=15)
            output_str = initial_output.decode('utf-8', errors='ignore')

            print_to_logfile(
                self.target,
                self.type,
                f"[Initial Output]\n{output_str}",
            )

            # 检查是否需要输入密码
            if 'Password' in output_str or 'password' in output_str.lower():
                self.channel.send(self.password + "\r\n")
                time.sleep(3)

                # 等待命令提示符
                auth_output = self.wait_for_prompt(self.channel, b'>', timeout=15)
                auth_str = auth_output.decode('utf-8', errors='ignore')
                print_to_logfile(
                    self.target,
                    self.type,
                    f"[After Password]\n{auth_str}",
                )

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ***Iteration #{str(count + 1)} {self.target} : SSH连接成功!***",
            )
            return True

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} {self.target}: SSH连接错误: {e}",
            )
            self.ssh_close()
            return False

    def send_command(self):
        """增强的命令发送方法"""
        if not self.channel:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} 错误: SSH通道未建立"
            )
            return

        try:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ========{self.target} {self.type.upper()} 信息收集开始========",
            )

            # 发送命令
            self.channel.send(self.command + "\r\n")
            time.sleep(2)  # 等待命令被处理

            # 收集输出 - 使用更稳健的方法
            output = b""
            start_time = time.time()
            max_wait_time = 60  # 最大等待时间

            while time.time() - start_time < max_wait_time:
                if self.channel.recv_ready():
                    chunk = self.channel.recv(4096)
                    output += chunk
                    # 如果输出中包含常见的结束标记，可以提前退出
                    if b'>' in chunk or b'#' in chunk:
                        # 再等待一小段时间看是否还有更多输出
                        time.sleep(2)
                        if not self.channel.recv_ready():
                            break
                else:
                    time.sleep(1)

            # 解码输出
            try:
                ans = output.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                ans = output.decode('gbk', errors='replace')

            # 发送 Ctrl+C 确保回到命令提示符
            self.channel.send('\x03')
            time.sleep(2)

            # 保存数据
            self._save_data(ans)

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} 命令执行完成，共收集 {len(output)} 字节数据",
            )

        except socket.error as e:
            if '10054' in str(e):
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} 连接被重置 (10054)，尝试恢复连接",
                )
                # 这里可以添加重连逻辑
            else:
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} 发送命令时发生socket错误: {e}",
                )
        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} 发送命令失败: {e}",
            )
        finally:
            self.ssh_close()

    def _save_data(self, data):
        """保存数据到文件"""
        try:
            # 保存原始数据
            with open(self.text_file, "w", encoding='utf-8') as f:
                f.write(f'{get_current_time()} RAW Data:\n')
                f.write(data)
                f.write('\n' + '=' * 50 + '\n')

            # 保存到历史文件
            mode = "a" if Path(self.history_file).exists() else "w"
            with open(self.history_file, mode, encoding='utf-8') as f:
                f.write(f'{get_current_time()} RAW Data:\n')
                f.write(data)
                f.write('\n' + '=' * 50 + '\n')

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} 保存数据失败: {e}",
            )

    def ssh_close(self):
        """安全的SSH关闭方法"""
        try:
            if self.channel:
                self.channel.close()
            if self.ssh:
                self.ssh.close()
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} SSH连接已关闭"
            )
        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} SSH关闭时发生错误: {e}"
            )

    def print_f(self):
        print("self.target_info:", self.target_info)