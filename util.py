import configparser
import requests
import os


def request_get(url, headers):
    try:
        res = requests.get(url=url, headers=headers, verify=False)
        res.close()
        return res
    except Exception as e:
        raise ValueError("远程强迫关闭!", e)


def request_post(url, headers, data):
    try:
        res = requests.post(url=url, headers=headers, json=data, verify=False)
        res.close()
        return res
    except Exception as e:
        raise ValueError("远程强迫关闭!", e)


def read_ini(option='token', file_path='./config.ini', section='Credentials'):
    config = configparser.ConfigParser()
    config.read(file_path)
    value = config.get(section, option=option)
    if value == "" and option != 'token':
        raise ValueError("config值不能为空，请确认.")
    return value


def write_ini_token(file_path='./config.ini', section='Credentials', token_value='your_new_token_value'):
    config = configparser.ConfigParser()

    # 读取现有配置文件内容
    config.read(file_path)

    # 设置或创建指定部分（section）和键值对
    if section not in config:
        config.add_section(section)
    config.set(section, 'token', token_value)

    # 写入配置文件
    with open(file_path, 'w') as config_file:
        config.write(config_file)
