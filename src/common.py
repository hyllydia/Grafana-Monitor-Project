import datetime
from pathlib import Path
from configparser import ConfigParser
import json
import re

# 定义配置文件路径
config_file = Path('firewall_info.cfg')

# 创建ConfigParser对象并读取配置文件
config = ConfigParser()
config.read(config_file)

def get_current_time():
    return datetime.datetime.now()


def print_to_logfile(target, type, log):
    file = f"{Path.cwd().parent}/logs/{type}/{target}.log"

    mode = "a+" if Path(file).exists() else "w+"
    with open(file, mode) as f:
        print(log, file=f)


def get_owner_value(file_name):
    # 定义正则表达式模式，匹配'collect_'后面的任意字符（非贪婪匹配）
    pattern = r'collect_(.*?)\.py'
    name = re.search(pattern, file_name).group(1)
    return name

#思路：正则匹配出来collect_yhou中的yhou, 然后根据owner_value:yhou 去获取testbed的名字
def get_section_for_option(option_value):
    for section in config.sections():
        if config.get(section, 'owner') == option_value:
            target_section = section
            return target_section

def get_target_info(target,file_name):
    # 根据owner-value获取testbed , 然后获取testbed下的设备信息
    option_value = get_owner_value(file_name)
    #print("Owner:",option_value)
    target_section = get_section_for_option(option_value)
    #print("TestBed:", target_section)
    target_info = json.loads(config[target_section][target])
    print(target)
    target_info.update({"testbed":target_section})
    print("========Target Info:=========")
    print("Target:",target)
    print("TestBed:",target_section)
    print(target_info)
    return target_info



