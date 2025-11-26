import configparser
import influxdb_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

config = configparser.ConfigParser()
config.read('config.ini')

INFLUX_URL = config.get('APP', 'INFLUX_URL')
INFLUX_TOKEN = config.get('APP', 'INFLUX_TOKEN')
INFLUX_ORG = config.get('APP', 'INFLUX_ORG')
INFLUX_BUCKET = config.get('APP', 'INFLUX_BUCKET')

client = influxdb_client.InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

# Write script
write_api = client.write_api(write_options=SYNCHRONOUS)


def write_point(measurement, tags, fields):
    record = {
        "measurement": measurement,
        "tags": tags,
        "fields": fields,
    },

    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=record)


# def read_saved_coredump(ip):
#     query = '''
#         from(bucket: "system_db")
#         |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
#         |> filter(fn: (r) => r["_measurement"] == "coredump_status")
#         |> filter(fn: (r) => r["_field"] == "coredump_files")
#         |> filter(fn: (r) => r["ip"] == "{ip}")
#         |> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)
#         |> yield(name: "last")
#         |> map(fn: (r) => ({_value: r._value}))
#
#         '''
#     query_api = client.query_api()
#     try:
#         result = query_api.query_data_frame(org=INFLUX_ORG, query=query)
#         coredump_files = result['coredump_files'].tolist()
#         print(coredump_files)
#         print(type(coredump_files))
#         return coredump_files
#     except Exception as e:
#         print(f"Error querying InfluxDB: {e}")
#         return None
