from pathlib import Path
import re
from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb_client import InfluxDBClient
#from influxdb2 import write_point
import influxdb2
#from memory_verbose_increase_over_hours import is_increasing

class Memory_Verbose_Collector(Collector):

    def __init__(self, ip, type,port, username, password, command, target,target_info,**kwargs):
        self.type = "memory_verbose"
        self.target_info = target_info
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))

        self.client = InfluxDBClient(url=influxdb2.INFLUX_URL, token=influxdb2.INFLUX_TOKEN, org=influxdb2.INFLUX_ORG)
        #self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def save_data(self):

        memory_verbose = {}

        with open(self.text_file, "r+") as fs:
            for line in fs.readlines():
                re_ver = r"^size-\w+\s+\d+"
                res = re.findall(re_ver, line.strip())
                if res:
                    re_key = r"^size-\w+"
                    re_value = r"\d+\d$"
                    key = re.findall(re_key, "".join(res))
                    value = re.findall(re_value, "".join(res))
                    # tips: dict values type ---int not str
                    memory_verbose["".join(key)] = int("".join(value))

        print_to_logfile(self.target,self.type,memory_verbose)
        influxdb2.write_point(
            "memory_verbose",  #measurement name
            self.tags,         # influxdb tag
            memory_verbose    #value:dict value
        )

        # 获取所有 size 项的键
        size_keys = [key for key in memory_verbose.keys() if key.startswith("size-")]
        print("size_keys:",size_keys)

        # 标签名称列表，可以根据实际需要进行调整
        tag_names = ["Yhou_4700", "Yhou_5700_P", "Yhou_5700_S","Yhou_6700","Yhou_10700","Yhou_10700_P","Yhou_10700_S","Yhou_NSv470_P","Yhou_NSv470_P","Yhou_3800"]

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
                print(f"Executing query for {size_key}:")
                print(query)

                result = self.query_api.query(org=influxdb2.INFLUX_ORG, query=query)
                print(f"***{size_key} for {tag_name}***")
                print("query result:", result)

                data = []
                for table in result:
                    for record in table.records:
                        value = record.get_value()
                        if value is not None:
                            data.append(value)
                print("data:", data)

                if data:
                    is_increase[size_key] = 1 if self.is_increasing(data) else 0
                else:
                    is_increase[size_key] = None

        print("is_increase is a dict:", is_increase)




        influxdb2.write_point(
            "memory_verbose_increase",  # measurement name
            self.tags,  # influxdb tag
            is_increase  # value:dict value
        )

        print_to_logfile(self.target,
                         self.type,
            f"{get_current_time()} Memory verbose increase data saved: {self.target} success!"
        )

    def is_increasing(self,data):
        # 确保 data 不包含 None 值
        clean_data = [x for x in data if x is not None]
        if len(clean_data) < 2:
            return True  # 如果数据点少于 2 个，视为递增
        return all(clean_data[i] < clean_data[i + 1] for i in range(len(clean_data) - 1))

