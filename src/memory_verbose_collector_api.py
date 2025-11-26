import requests.auth
import json
import time
from pathlib import Path
import re
from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb_client import InfluxDBClient
import influxdb2
import urllib3

urllib3.disable_warnings()


class Memory_Verbose_Collector_API(Collector):

    def __init__(self, ip, type, port, username, password, command, target, target_info, **kwargs):
        self.type = "memory_verbose"
        self.target_info = target_info
        super().__init__(ip, type, port, username, password, command, target, target_info, gen=kwargs.get("gen"),
                         remark=kwargs.get("remark"))

        # API Info
        self.base_url = f"https://{self.ip}"
        self.session = requests.Session()
        self.session.verify = False
        self.token = None

        self.client = InfluxDBClient(url=influxdb2.INFLUX_URL, token=influxdb2.INFLUX_TOKEN, org=influxdb2.INFLUX_ORG)
        self.query_api = self.client.query_api()

    def ssh_connect(self, count):
        """
        重写SSH连接方法，改为API登录
        """
        try:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ***Iteration #{str(count + 1)} {self.target} : Starting API login for memory_verbose***",
            )

            # 调用API登录
            if self.api_login():
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} ***Iteration #{str(count + 1)} {self.target} : API login successfully!***",
                )
            else:
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} {self.target}: API login failed!",
                )

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} {self.target}: API login error:{e}",
            )

    def send_command(self):
        """
        重写发送命令方法，使用API发送命令
        """
        return self.api_send_command()

    def api_login(self):
        try:
            auth_url = f"{self.base_url}/api/sonicos/auth"
            body = {'override': True}
            headers = {
                'Content-Type': 'application/json',
                'Accept-Encoding': 'application/json'
            }

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Attempting API login to {self.target}"
            )

            # 使用Digest认证 - 使用self.session保持会话
            r = self.session.post(
                auth_url,
                auth=requests.auth.HTTPDigestAuth(username=self.username, password=self.password),
                data=json.dumps(body),
                headers=headers,
                verify=False
            )

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Login response status: {r.status_code}"
            )

            if r.status_code == 200:
                try:
                    response_data = r.json()
                    msg_res = response_data['status']['info'][0]['message']

                    print_to_logfile(
                        self.target,
                        self.type,
                        f"{get_current_time()} Login successful - {msg_res}"
                    )

                    print_to_logfile(
                        self.target,
                        self.type,
                        f"{get_current_time()} {self.target} : API login successfully! Session established.",
                    )
                    return True

                except (KeyError, IndexError) as e:
                    print_to_logfile(
                        self.target,
                        self.type,
                        f"{get_current_time()} {self.target}: API login failed - error parsing response: {e}, Response: {r.text}",
                    )
                    return False
            else:
                try:
                    error_data = r.json()
                    msg_res = error_data.get('status', {}).get('info', [{}])[0].get('message', 'Unknown error')
                    print_to_logfile(
                        self.target,
                        self.type,
                        f"{get_current_time()} {self.target}: API login failed with status {r.status_code} - {msg_res}",
                    )
                except:
                    print_to_logfile(
                        self.target,
                        self.type,
                        f"{get_current_time()} {self.target}: API login failed with status {r.status_code}, Response: {r.text}",
                    )
                return False

        except requests.exceptions.RequestException as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} {self.target}: API login request exception - {e}",
            )
            return False
        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} {self.target}: API login unexpected error - {e}",
            )
            return False

    def api_send_command(self):
        """
        使用API发送命令获取memory verbose数据
        """
        try:
            api_url = f"{self.base_url}/api/sonicos/direct/cli"

            command_data = "diag show memory verbose"

            headers = {
                "Content-Type": "text/plain",  # 使用纯文本格式, From Postman
            }

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} ========{self.target} {self.type.upper()} Information========",
            )

            response = self.session.post(api_url, data=command_data, headers=headers)
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Command response status: {response.status_code}"
            )

            if response.status_code == 200:
                # 直接获取响应文本
                output = response.text

                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} API command executed successfully, response length: {len(output)}",
                )

                # 记录响应预览（前500字符）
                preview = output[:500] + "..." if len(output) > 500 else output
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} Response preview: {preview}",
                )

                # 写入文件
                with open(self.text_file, "w+") as f:
                    f.write(f'{get_current_time()} RAW Data:\n')
                    f.write(output)
                    f.close()

                mode = "a+" if Path(self.history_file).exists() else "w+"
                with open(self.history_file, mode) as f:
                    f.write(f'{get_current_time()} RAW Data:\n')
                    f.write(output)
                    f.write("\n" + "=" * 50 + "\n")
                    f.close()

                self.save_data()

            else:
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} API command failed! Status: {response.status_code}, Response: {response.text}",
                )

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} send command via API failed! {e}",
            )

    def api_collect_data(self):
        """
        重写数据收集方法，使用API而不是SSH
        """
        if self.api_login():
            self.api_send_command()

    def save_data(self):
        """
        解析memory verbose数据并保存到InfluxDB
        """
        memory_verbose = {}
        try:
            with open(self.text_file, "r+") as fs:
                content = fs.read()
                lines = content.split('\n')

                for line in lines:
                    # 匹配size-开头的行，如: "size-16    311386    8469017"
                    if line.strip().startswith('size-'):
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            size_type = parts[0]  # size-16, size-32, etc.
                            bytes_allocated = parts[2]  # 第三列是Bytes Allocated
                            try:
                                memory_verbose[size_type] = int(bytes_allocated)
                            except ValueError:
                                print_to_logfile(
                                    self.target,
                                    self.type,
                                    f"{get_current_time()} Warning: Could not convert {bytes_allocated} to integer for {size_type}"
                                )
                                continue

            print_to_logfile(self.target, self.type, f"Extracted memory data: {memory_verbose}")

            # 保存到InfluxDB
            influxdb2.write_point(
                "memory_verbose",  # measurement name
                self.tags,  # influxdb tag
                memory_verbose  # value:dict value
            )

            # 执行趋势分析（保留原有逻辑）
            self.analyze_trends(memory_verbose)

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Memory verbose data saved: {self.target} success!"
            )

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Error in save_data: {e}"
            )

    def analyze_trends(self, memory_verbose):
        """
        分析内存使用趋势（原有逻辑）
        """
        try:
            # 获取所有 size 项的键
            size_keys = [key for key in memory_verbose.keys() if key.startswith("size-")]
            print_to_logfile(self.target, self.type, f"Size keys found: {size_keys}")

            # 标签名称列表
            tag_names = ["Yhou_4700", "Yhou_5700_P", "Yhou_5700_S", "Yhou_6700", "Yhou_10700", "Yhou_10700_P",
                         "Yhou_10700_S", "Yhou_NSv470_P", "Yhou_3800"]

            # 判断每个 size 项在 48 小时内是否线性增长
            is_increase = {}
            bucket = "system_db"
            measurement = "memory_verbose"
            time_range = "-48h"

            for size_key in size_keys:
                for tag_name in tag_names:
                    query = f"""
                            from(bucket: "{bucket}")
                              |> range(start: {time_range})
                              |> filter(fn: (r) => r._measurement == "{measurement}")
                              |> filter(fn: (r) => r._field == "{size_key}")
                              |> filter(fn: (r) => r.name == "{tag_name}")
                              |> aggregateWindow(every: 1h, fn: mean,createEmpty: false)
                              |> yield(name: "mean")
                            """

                    result = self.query_api.query(org=influxdb2.INFLUX_ORG, query=query)

                    data = []
                    for table in result:
                        for record in table.records:
                            value = record.get_value()
                            if value is not None:
                                data.append(value)

                    if data:
                        is_increase[size_key] = 1 if self.is_increasing(data) else 0
                    else:
                        is_increase[size_key] = None

            # 保存趋势分析结果
            influxdb2.write_point(
                "memory_verbose_increase",  # measurement name
                self.tags,  # influxdb tag
                is_increase  # value:dict value
            )

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Memory verbose increase analysis completed: {is_increase}"
            )

        except Exception as e:
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Error in analyze_trends: {e}"
            )

    def is_increasing(self, data):
        """
        判断数据是否递增
        """
        clean_data = [x for x in data if x is not None]
        if len(clean_data) < 2:
            return True
        return all(clean_data[i] < clean_data[i + 1] for i in range(len(clean_data) - 1))