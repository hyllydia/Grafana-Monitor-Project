# -*- coding: utf-8 -*-
# @Time    : 2024/8/15 0:19
# @Author  : Yuling Hou
# @File    : memory_verbose_increase_test.py
# @Software: PyCharm
from influxdb_client import InfluxDBClient
import influxdb2

# 配置
bucket = "system_db"
measurement = "memory_verbose"
time_range = "-3h"
tags = {
    "testbed": "Greatwall",
    "name": "Yhou_4700"
}

# 创建 InfluxDB 客户端
client = InfluxDBClient(url=influxdb2.INFLUX_URL, token=influxdb2.INFLUX_TOKEN, org=influxdb2.INFLUX_ORG)
query_api = client.query_api()

def process_query_result(result):
    values = []
    for table in result:
        for record in table.records:
            values.append(record.get_value())
    return values

# 构造查询语句
# query = f"""
# from(bucket: "{bucket}")
#   |> range(start: {time_range})
#   |> filter(fn: (r) => r._measurement == "{measurement}")
#   |> filter(fn: (r) => r.testbed == "{tags['testbed']}")
#   |> filter(fn: (r) => r.name == "{tags['name']}")
#   |> filter(fn: (r) => r._field == "size-16")
#   |> aggregateWindow(every: 1h, fn: mean)
#   |> yield(name: "mean")
# """
query = f"""
from(bucket: "system_db")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "memory_verbose")
  |> filter(fn: (r) => r._field == "size-16")
  |> filter(fn: (r) => r.name == "Yhou_4700")
  |> aggregateWindow(every: 20m, fn: mean, createEmpty: false)
  |> yield(name: "mean")
"""

# 执行查询
result = query_api.query(org=influxdb2.INFLUX_ORG, query=query)


# 处理并打印结果
values = process_query_result(result)
print(values)
print(f"Queried values: {values}")

