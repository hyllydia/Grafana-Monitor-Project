from pathlib import Path

from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point
import re

class DPI_SSL_Collector(Collector):

    def __init__(self, ip, type,port, username, password, command, target,target_info,**kwargs):
        self.type = "dpi_ssl_connections"
        self.target_info = target_info
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))
        
    def save_data(self):
        with open(self.text_file, "r+") as fs:
            for line in fs.readlines():
                if "SSL proxied connection count" in line:
                    re_dpi_ssl = r'\d+\/\d+\/\d+'
                    re_dpi_ssl_cur  = r'^\d+'
                    matches = re.findall(re_dpi_ssl, line.strip())
                    dpi_ssl_connections = matches[0]
                    dpi_ssl_cur_connections = re.search(re_dpi_ssl_cur,dpi_ssl_connections)
                    dpi_ssl_cur_connections = int(dpi_ssl_cur_connections.group(0))
                    #print(type(dpi_ssl_connections))
                    #print(dpi_ssl_connections)

            data_dict = {
                "DPI_SSL_Connections": dpi_ssl_connections,
                "DPI_SSL_Cur_Connections": dpi_ssl_cur_connections,
            }
            for key, value in data_dict.items():
                print_to_logfile(
                    self.target,
                    self.type,
                    f'{key}: {value}'
                )

                write_point(
                    "dpi_ssl_connections",
                    self.tags,
                    data_dict
                )
                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} DPI_SSL connections data saved: {self.target} success!"
                )

        