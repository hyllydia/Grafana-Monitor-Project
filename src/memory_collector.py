from pathlib import Path
import re
from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point

class Memory_Collector(Collector):

    def __init__(self, ip, type,port, username, password, command, target,target_info,**kwargs):
        self.type = "memory"
        self.target_info = target_info
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))

    def save_data(self):

        with open(self.text_file, "r+") as fs:
            for line in fs.readlines():
                re_str = r"\d+\sKiB$"
                if "Total system memory:" in line:
                    # print(line.strip())
                    res = re.findall(re_str, line.strip())
                    tol_data = "".join(res)
                if "Free system memory:" in line:
                    # print(line.strip())
                    res = re.findall(re_str, line.strip())
                    free_data = "".join(res)
                if "Available system memory:" in line:
                    # print(line.strip())
                    res = re.findall(re_str, line.strip())
                    ava_data = "".join(res)
                if "All Available memory:" in line:
                    # print(line.strip())
                    res = re.findall(re_str, line.strip())
                    all_data = "".join(res)
            
            data_dict = {
                    "total_system_memory": int(tol_data[0:-3]),
                    "free_system_memory": int(free_data[0:-3]),
                    "available_system_memory": int(ava_data[0:-3]),
                    "all_available_memory": int(all_data[0:-3]),
                }
            
            for key,value in data_dict.items():
                print_to_logfile(
                self.target,
                self.type,
                f'{key} : {value}'
                )

            write_point(
                "memory",
                self.tags,
                data_dict,
            )

            print_to_logfile(self.target,
                             self.type,
                f"{get_current_time()} Memory data saved: {self.target} success!"
            )

