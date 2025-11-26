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
            # "testbed": self.target.split('.')[0],
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
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)

        Path(f"{Path.cwd().parent}/logs/{self.type}/raw_data").mkdir(
            parents=True, exist_ok=True
        )
        Path(f"{Path.cwd().parent}/logs/{self.type}/history").mkdir(
            parents=True, exist_ok=True
        )

        self.text_file = f"{Path.cwd().parent}/logs/{self.type}/raw_data/{self.target}_{self.type}.txt"
        self.history_file = f"{Path.cwd().parent}/logs/{self.type}/history/{self.target}_{self.type}_history.txt"

    def ssh_connect(self, count):
        try:
            self.ssh.connect(
                hostname=self.ip,
                port=self.port,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False,
                banner_timeout=200,
                timeout=200,
                auth_timeout=200
            )
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ***Iteration #{str(count + 1)} {self.target} : SSH connect successfully!***",
            )

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} {self.target}: ssh connect error:{e}",
            )

    def send_command(self):
        """
        send command to Firewall and write the content to file
        :return:
        """

        try:
            con_firewall = self.ssh.invoke_shell()

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ========{self.target} {self.type.upper()} Information========",
            )

            con_firewall.send(self.command)
            time.sleep(10)
            output = con_firewall.recv(65535)
            ans = output.decode(encoding="utf-8", errors="strict")

            # 发送 Ctrl+C
            con_firewall.send('\x03' + '\n')
            time.sleep(10)  # 等待一段时间确保 Ctrl+C 发送完成

            # Write the console output to raw data file
            with open(self.text_file, "w+") as f:
                f.write(f'{get_current_time()} RAW Data:')
                f.write(ans)
                time.sleep(10)
                f.close()

            # Write the console output to history file
            mode = "a+" if Path(self.history_file).exists() else "w+"
            with open(self.history_file, mode) as f:
                f.write(f'{get_current_time()} RAW Data:')
                f.write(ans)
                time.sleep(10)
                f.close()
            self.save_data()
            con_firewall.send('exit\n')
        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} send command failed!{e}",
            )
        finally:
            self.ssh_close()
            time.sleep(10)

    def ssh_close(self):
        try:
            self.ssh.close()
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ssh close successfully!"
            )
        except Exception as e:
            print_to_logfile(self.target,
                             self.type,
                             f"{get_current_time()} ssh close failed!{e}")

    def print_f(self):
        print("self.target_info:", self.target_info)

