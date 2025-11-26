from pathlib import Path

from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point
#from influxdb2 import read_saved_coredump


class Coredump_Status_Collector(Collector):

    def __init__(self, ip,type,port, username, password, command, target,target_info,**kwargs):
        self.type = "coredump_status"
        self.target_info = target_info
        self.interval = 10
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))

    def save_data(self):

        with open(self.text_file, "r+") as fs:
            lines = fs.readlines()
            coredump_files = []
            for index, line in enumerate(lines):
                if "export core-dump" in line:
                    for i in range(1, len(lines) - index):
                        new_line = lines[index + i].strip()

                        if ("export core-dump" in new_line):
                            break

                        if "core.zst" in new_line:
                            coredump_files.append(new_line)
                    break

            number_of_coredump_files = len(coredump_files)
            if number_of_coredump_files > 0:
                print_to_logfile(
                    self.target,
                    self.type,
                    f'Number of Coredump Files: {number_of_coredump_files}'
                )
                for file in coredump_files:
                    print_to_logfile(
                        self.target,
                        self.type,
                        f'File Name : {file}'
                    )

                # coredump_files_string = ",".join(str(file) for file in coredump_files)
                recent_coredump_file = str(coredump_files[-1])

                print_to_logfile(
                    self.target,
                    self.type,
                    f"{get_current_time()} Coredump status data saved: {recent_coredump_file}"
                )

                write_point(
                    "coredump_status",
                    self.tags,
                    {
                        "number_of_files": number_of_coredump_files,
                        "coredump_files": recent_coredump_file,
                    },
                )
            else:
                write_point(
                    "coredump_status",
                    self.tags,
                    {
                        "number_of_files": number_of_coredump_files,
                        "coredump_files": 'None',
                    },
                )

            print_to_logfile(
                self.target,
                self.type,
                f"{get_current_time()} Coredump status data saved: {self.target} success!"
            )


