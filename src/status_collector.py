from pathlib import Path

from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point
import re


class General_Status_Collector(Collector):

    def __init__(self, ip,type,port, username, password, command, target,target_info):
        self.type = "general_status"
        self.name = target_info["name"]
        super().__init__(
            ip=ip,
            type=self.type,
            port=port,
            username=username,
            password=password,
            command=command,
            target=target,
            target_info=target_info,
            gen =target_info.get("gen") ,
            remark = target_info.get("remark")
        )
    
    def save_data(self):
        with open(self.text_file, "r+") as fs:
            for line in fs.readlines():
                if "Model:" in line:
                    _, _, after_word = line.strip().partition("Model:")
                    model = after_word.strip()
                elif "Serial Number:" in line:
                    _, _, after_word = line.strip().partition("Serial Number:")
                    serial_mumber = after_word.strip()
                elif "Firewall Name:" in line:
                    _, _, after_word = line.strip().partition("Firewall Name:")
                    firewall_name = after_word.strip()
                elif "Firmware Version:" in line:
                    _, _, after_word = line.strip().partition("Firmware Version:")
                    firmware_version = after_word.strip().split(" ")[-1]
                elif "ROM Version:" in line:
                    _, _, after_word = line.strip().partition("ROM Version:")
                    rom_version = after_word.strip()
                elif "Up Time:" in line:
                    _, _, after_word = line.strip().partition("Up Time:")
                    up_time = after_word.strip()
                elif "Current Connections:" in line:
                    _, _, after_word = line.strip().partition("Current Connections:")
                    current_connections = after_word.strip()
                    current_connections =  re.findall(r'\d+', current_connections)
                    current_connections = int(current_connections[0])
            
            data_dict = {
                    "Model": model,
                    "Serial_Number": serial_mumber,
                    #"Firewall_Name": firewall_name,
                    "Firewall_Name": self.name,
                    "Firmware_Version": firmware_version,
                    "ROM_Version": rom_version,
                    "UP_Time": up_time,
                    "GEN": self.gen,
                    "Remark" : self.remark,
                    "Current_Connections": current_connections
                }

            for key,value in data_dict.items():
                print_to_logfile(
                    self.target,
                    self.type,
                    f'{key}: {value}'
                )

            write_point(
                "status",
                self.tags,
                data_dict
            )
            
            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Status data saved: {self.target} success!",
            )
