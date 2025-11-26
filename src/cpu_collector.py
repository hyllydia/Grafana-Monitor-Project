from pathlib import Path
import re

from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point

class CPU_Collector(Collector):

    def __init__(self, ip, type,port, username, password, command, target,target_info,**kwargs):
        self.type = "cpu"
        self.target_info = target_info
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))
    def save_data(self):

        re_str = r"^\s+(\d+)\s+(\d{1,3})\s+\d+\s+\d+"

        core_cpu_data = []

        with open(self.text_file, "r+") as fs:
            for line in fs.readlines():
                if match := re.match(re_str, line):
                    core_cpu_data.append(match.groups())

        core_number = len(core_cpu_data)

        core_cpu_data_dict = dict(
            (f"core_{x}", int(y)) for x, y in tuple(core_cpu_data)
        )

        for key,value in core_cpu_data_dict.items():
            print_to_logfile(
                    self.target,
                    self.type,
                    f"{key}: {value}"
                )

        write_point(
            f"cpu_{core_number}cores",
            self.tags,
            core_cpu_data_dict,
        )

        print_to_logfile(
            self.target,
            self.type,
            f"{get_current_time()} CPU data saved: {self.target} success!",
        )

