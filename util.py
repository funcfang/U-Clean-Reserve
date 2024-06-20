import configparser
import requests
import json
from playsound import playsound
from win11toast import toast
from threading import Thread
import os
FILE_PATH = 'config.json'


def load_config(file_path=FILE_PATH):
    with open(file_path, 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    return config


def read_config(key):
    config = load_config()
    return config[key]


def update_config(key, value):
    config = load_config()
    config[key] = value
    with open(FILE_PATH, 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file)


def send_bark(title='no title', message='no message'):
    bark_url = read_config('bark_url')
    if bark_url == '':
        return

    url = bark_url + f'{title}/{message}'
    group = 'washer'
    icon = 'https://oss.funcfang.cn/images/bark/washer.jpg'
    response = requests.get(url, params={'group': group, 'icon': icon})
    if response.status_code != 200:
        print('bark请求失败:', response)


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


def play_music():
    playsound('./resources/爱你.mp3')


def play_music_toast(content):
    t_music = Thread(target=play_music)
    t_music.start()

    send_bark('洗衣机监听小脚本', content)
    img_path = os.path.split(os.path.realpath(__file__))[0] + '\\resources\\washer.jpg'
    toast("洗衣机监听小脚本", f"{content}", duration='long', image=img_path)  # toast自带的音乐时长播放太短


def decodeQrCode(img_path):
    from pyzbar.pyzbar import decode
    from PIL import Image
    decocdeQR = decode(Image.open(img_path))
    return decocdeQR[0].data.decode('ascii')
