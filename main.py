import json
import time

import urllib3
from playsound import playsound
from win11toast import toast
from threading import Thread
from util import read_ini, write_ini_token, request_get, request_post

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_headers(type='reserve'):
    if type == 'phoneCode':
        headers = {
            "Host": "phoenix.ujing.online:443",
            "x-user-geo": "-180.000000,-180.000000",
            "x-mobile-brand": "apple",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-Hans-CN;q=1, en-CN;q=0.9, zh-Hant-TW;q=0.8",
            "Accept": "*/*",
            "x-app-code": "ZI",
            "User-Agent": "U jing/2.4.3 (iPhone; iOS 17.3; Scale/3.00)",
            "Connection": "keep-alive",
            "x-app-version": "2.4.3",
            "x-mobile-model": "iPhone14,5"
        }
    elif type == 'login':
        headers = {
            "Host": "phoenix.ujing.online:443",
            "Accept": "*/*",
            "x-user-geo": "-180.000000,-180.000000",
            "x-mobile-brand": "apple",
            "Accept-Language": "zh-Hans-CN;q=1, en-CN;q=0.9, zh-Hant-TW;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "x-app-code": "ZI",
            "User-Agent": "U jing/2.4.3 (iPhone; iOS 17.3; Scale/3.00)",
            "x-app-version": "2.4.3",
            "Connection": "keep-alive",
            "x-mobile-model": "iPhone14,5"
        }
    elif type == 'reserve':
        headers = {
            "x-user-geo": "-180.000000,-180.000000",
            "Accept": "*/*",
            "weex-version": "1.1.30",
            "x-mobile-brand": "apple",
            "Accept-Language": "zh-Hans-CN;q=1, en-CN;q=0.9, zh-Hant-TW;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "x-app-code": "BI",
            "User-Agent": "U jing/2.4.2 (iPhone; iOS 17.0.1; Scale/3.00)",
            "x-app-version": "2.4.2",
            "Connection": "keep-alive",
            "x-mobile-model": "iPhone14,5",
        }
        token = read_ini('token')
        headers['Authorization'] = f'Bearer {token}'
    return headers


def login():
    phone_number = input("手机号：")
    url = f"https://phoenix.ujing.online:443/api/v1/captcha?mobile={phone_number}&sessionId=AFS_SWITCH_OFF&sig=AFS_SWITCH_OFF&token=AFS_SWITCH_OFF&type=1"
    res = request_get(url, headers=get_headers(type='phoneCode'))
    res_decode = res.content.decode('utf-8')
    res_json = json.loads(res_decode)
    if res_json['code'] != 0:
        raise ValueError("验证码发送失败!", res_json)
    captcha = input("验证码发送成功！\n 请输入验证码：")

    retry_num = 3
    while retry_num > 0:
        url = f"https://phoenix.ujing.online:443/api/v1/login"
        data = {
            "captcha": captcha,
            "mobile": phone_number
        }
        res = request_post(url, headers=get_headers(type='login'), data=data)
        res_decode = res.content.decode('utf-8')
        res_json = json.loads(res_decode)
        if res_json['code'] == 0:
            break
        else:
            print("登录失败!", res_json)
            captcha = input("验证码有误！\n 请重新输入验证码：")
            retry_num -= 1
            if retry_num == 0:
                ValueError("登录失败!", res_json)

    print("登录成功!")

    token = res_json['data']['token']
    write_ini_token(token_value=token)


def play_music():
    playsound('爱你.mp3')


def play_music_toast():
    t_music = Thread(target=play_music)
    t_music.start()

    toast("小脚本通知您", "已为您预约洗衣机成功！",
          image='https://4.bp.blogspot.com/-u-uyq3FEqeY/UkJLl773BHI/AAAAAAAAYPQ/7bY05EeF1oI/s800/cooking_toaster.png',
          duration='long')  # toast自带的音乐时长播放太短


def getJSONData(washModel=2, storeId='', deviceTypeId=2, temperature=1, wp_detergentGearId=None,
                wp_disinfectantGearId=None, deviceId=None):
    """
    洗衣机楼栋   "storeId": ""
    洗衣机机号   "deviceId":  ""
    机型        "deviceTypeId":   2 - 滚筒,  10 - 烘干机
    清洗模式     "deviceWashModelId":    1 - 普通洗,  2 - 小件洗, 3 - 超强洗,  4 - 单脱水
    温度        "washTemperatureId"：1 - 常温(实际30度高温),  2 - 30度, 3 - 40度, 4 - 60度
    洗衣液      "wp_detergentGearId": 1 - 标准量,  3 - 大量
    除菌液      "wp_disinfectantGearId":  4 - 标准量, 6 - 大量
    """

    data = {
        "type": 1,

        # "deviceId": "",  # deviceId不传则由服务端自动匹配机子
        "deviceTypeId": deviceTypeId,
        "storeId": storeId,
        "deviceWashModelId": washModel,
        "washTemperatureId": temperature
    }

    if deviceId is not None:
        data['deviceId'] = deviceId

    if wp_detergentGearId is not None:
        data['wp_detergentGearId'] = wp_detergentGearId

    if wp_disinfectantGearId is not None:
        data['wp_disinfectantGearId'] = wp_disinfectantGearId

    return data


# 开始预定
def start_reserve(dataList, sleep=90):
    url = "https://phoenix.ujing.online/api/v1/orders/create"

    times = 1
    while True:
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f'第 {times} 次预约: {now_time}')
        for index, data in enumerate(dataList):
            res = request_post(url, get_headers('reserve'), data)
            res_decode = res.content.decode('utf-8')
            res_json = json.loads(res_decode)
            if res_json['code'] == 0:
                print(f"预约 洗衣机{index + 1} 成功!")
                play_music_toast()
                return
            if res_json['code'] == 401:
                print(f"预约 洗衣机{index + 1} 失败! token过期! 请重新登录.", res_json)
                login()
                continue
            print(f'预约 洗衣机{index + 1} 失败!', res_json)
        print(f'{sleep}s后重试.')
        print('---------------')
        time.sleep(sleep)
        times += 1


if __name__ == '__main__':
    print('清洗模式     "washModel":   1 - 普通洗,  2 - 小件洗,  3 - 超强洗,  4 - 单脱水')
    washModel = int(input('washModel: '))
    storeId = read_ini('storeId')  # 楼栋id
    deviceId1 = read_ini('deviceId1')  # 设备id
    deviceId2 = read_ini('deviceId2')
    dataList = [getJSONData(washModel, storeId=storeId, deviceId=deviceId1),
                getJSONData(washModel, storeId=storeId, deviceId=deviceId2)]

    start_reserve(dataList)
