import argparse
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

from common import get_target_info, get_current_time, print_to_logfile
import commands

from cpu_collector import CPU_Collector
from status_collector import General_Status_Collector
from memory_collector import Memory_Collector
from memory_verbose_collector import Memory_Verbose_Collector
from memory_verbose_collector_api import Memory_Verbose_Collector_API
from ha_status_collector import HA_Status_Collector
from dpi_ssl_collector import DPI_SSL_Collector
from coredump_status_collector import Coredump_Status_Collector

def collect(target):
    try:
        target_info = get_target_info(target, os.path.basename(__file__))
        ip = target_info["ip"]
        port = target_info["port"]
        username = target_info["username"]
        password = target_info["password"]

        # 创建所有收集器的实例
        collector1 = General_Status_Collector(
            ip=ip,
            type="general_status",
            port=port,
            username=username,
            password=password,
            command=commands.command_general_status,
            target=target,
            target_info=target_info,
        )
        collector2 = CPU_Collector(
            ip=ip,
            type="cpu",
            port=port,
            username=username,
            password=password,
            command=commands.command_cpu,
            target=target,
            target_info=target_info,
        )
        collector3 = Memory_Collector(
            ip=ip,
            type="memory",
            port=port,
            username=username,
            password=password,
            command=commands.command_memory,
            target=target,
            target_info=target_info,
        )
        # collector4 = Memory_Verbose_Collector(
        #     ip=ip,
        #     type="memory_verbose",
        #     port=port,
        #     username=username,
        #     password=password,
        #     command=commands.command_memory_verbose,
        #     target=target,
        #     target_info=target_info,
        # )
        collector4 = Memory_Verbose_Collector_API(
            ip=ip,
            type="memory_verbose",
            port=port,
            username=username,
            password=password,
            command=commands.command_memory_verbose,
            target=target,
            target_info=target_info,
        )
        collector5 = HA_Status_Collector(
            ip=ip,
            type="ha_status",
            port=port,
            username=username,
            password=password,
            command=commands.command_ha_status,
            target=target,
            target_info=target_info,
        )
        collector6 = DPI_SSL_Collector(
            ip=ip,
            type="dpi_ssl_connections",
            port=port,
            username=username,
            password=password,
            command=commands.command_dpi_ssl_connections,
            target=target,
            target_info=target_info,
        )
        collector7 = Coredump_Status_Collector(
            ip=ip,
            type="coredump_status",
            port=port,
            username=username,
            password=password,
            command=commands.command_coredump_status,
            target=target,
            target_info=target_info,
        )
        # collector8 = Memory_Verbose_Increase_Collector(
        #     ip=ip,
        #     type="memory_verbose_increase",
        #     port=port,
        #     username=username,
        #     password=password,
        #     command=commands.command_memory_verbose,
        #     target=target,
        #     target_info=target_info,
        # )
        collectors = [collector1, collector2, collector3, collector4, collector5, collector6,collector7]
        #collectors = [collector4]
        # 设置最大线程数为7，即允许同时执行的最大任务数为7
        max_workers = 7

        # 使用线程池并行执行所有收集器
        with ThreadPoolExecutor(max_workers) as executor:
            # futures = [
            #     executor.submit(collector.ssh_connect, 0) for collector in [collector1, collector2, collector3, collector4, collector5]
            # ]
            # for future in futures:
            #     future.result()  # 等待任务完成
            #
            count = 0
            while True:
                for collector in collectors:
                    collector.ssh_connect(count)
                    collector.send_command()
                time.sleep(30)
                count += 1
    except Exception as e:
        print_to_logfile(target, "", f"{get_current_time()} Task {target} ... : {e}")


# 定义每个collector的函数
def connect_and_send(collector, count):
    collector.send_command() # 在已建立的SSH连接上发送命令
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="python3 collect_yhou.py --target")
    parser.add_argument(
        "--target", type=list, required=True, nargs="+", help="target name"
    )
    args = parser.parse_args()
    targets = args.target
    target_list = ["".join(t) for t in targets]

    print(target_list)

    with ThreadPoolExecutor(len(target_list)) as pool:
        futures = [pool.submit(collect, target) for target in target_list]

        for future in as_completed(futures):
            future.result()
