from pathlib import Path

from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point

class HA_Status_Collector(Collector):

    def __init__(self, ip, type,port, username, password, command, target,target_info,**kwargs):
        self.type = "ha_status"
        self.target_info = target_info
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))
        
    def save_data(self):

        with open(self.text_file, "r+") as fs:
            for line in fs.readlines():
                if line.startswith("Status:"):
                    _, _, after_word = line.strip().partition("Status:")
                    ha_status = after_word.strip()
            
            print_to_logfile(
                self.target,
                self.type,
                f'HA Status: {ha_status}'
            )

            write_point(
                "ha_status",
                self.tags,
                {
                    "status": ha_status,
                },
            )
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} HA status data saved: {self.target} success!"
            )

        