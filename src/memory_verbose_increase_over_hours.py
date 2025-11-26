# -*- coding: utf-8 -*-
# @Time    : 2024/8/13 23:53
# @Author  : Yuling Hou
# @File    : memory_verbose_increase_over_hours.py
# @Software: PyCharm
import pandas as pd
import configparser
import influxdb_client
from influxdb_client.client import query_api
from influxdb_client.domain import bucket

from pathlib import Path
import re
from common import print_to_logfile, get_current_time
from base_collector_bak02 import Collector
from influxdb2 import write_point
import influxdb2



class Memory_Verbose_Increase_Collector(Collector):

    def __init__(self, ip, type, port, username, password, command, target, target_info,**kwargs):
        self.type = "memory_verbose_increase"
        self.target_info = target_info
        super().__init__(ip, type,port, username, password, command, target,target_info,gen=kwargs.get("gen"),remark=kwargs.get("remark"))

    def is_increasing(self):
        measurement = "memory_verbose"
        field = self
        time_range = "-48h"
        # 定义查询语句
        query = f"""
        from(bucket: "{bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "{measurement}")
          |> filter(fn: (r) => r._field == "{field}")
          |> aggregateWindow(every: 1h, fn: mean)
          |> yield(name: "mean")
        """
        # 执行查询
        result = query_api.query(org=influxdb2.INFLUX_ORG, query=query)

        # 将查询结果转换为 DataFrame
        data = []
        for table in result:
            for record in table.records:
                data.append({
                    'time': record.get_time(),
                    'mean': record.get_value()
                })

        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        df.sort_index(inplace=True)

        # 检查内存值是否在时间上单调递增
        def increase_result(df):
            return df['mean'].is_monotonic_increasing

        # 判断 48 小时内内存值是否一直上涨
        result = increase_result(df)
        #return result
        #print("内存值在过去 48 小时内是否一直上涨:", result)

