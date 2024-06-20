import json
import time
import urllib3

from util import load_config, read_config, update_config, request_get, request_post, play_music_toast, decodeQrCode

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def getWasherList():
    import os
    washerList = []
    for root, _, Figs in os.walk('./washerQrCode_Figs'):
        for fig in Figs:
            if fig == ".gitkeep":
                continue
            # Join the root directory with the file name to get the full path
            fig_path = os.path.join(root, fig)
            qrcode = decodeQrCode(fig_path)
            washerList.append({
                'name': os.path.splitext(fig)[0],
                'QrCode': qrcode,
                'deviceId': ""
            })
    update_config('washerList', washerList)
    return 'ok'


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
    else:
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
        token = read_config('token')
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
    update_config('token', token)
    return 'ok'


def checkWasherRunning(qrCode):
    url = f"https://phoenix.ujing.online:443/api/v1/devices/scanWasherCode"
    res = request_post(url, get_headers('reserve'), {'qrCode': qrCode})
    res_decode = res.content.decode('utf-8')
    res_json = json.loads(res_decode)
    if res_json['code'] == 0:
        deviceId = res_json['data']['result']['deviceId']
        createOrderEnabled = res_json['data']['result']['createOrderEnabled']
        return createOrderEnabled
    elif res_json['code'] == 401:
        print(f"token过期! 请重新登录.", res_json)
        login()
        return checkWasherRunning(qrCode)
    else:
        ValueError("获取设备信息失败", res_json)


def getStoreId(deviceId):
    url = f"/api/v1/app/washer/devices/program/info?deviceId={deviceId}"
    res = request_get(url, get_headers('reserve'))
    res_decode = res.content.decode('utf-8')
    res_json = json.loads(res_decode)
    if res_json['code'] == 0:
        storeId = res_json['data']['storeId']
        return storeId
    else:
        ValueError("获取设备详情失败", res_json)


def startCheckWasherStatus(washerList, sleep=60):
    times = 1
    while True:
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f'第 {times} 次监听: {now_time}')
        freeWasherList = []
        for washer in washerList:
            washerName = washer['name']
            qrcode = washer['QrCode']
            createOrderEnabled = checkWasherRunning(qrcode)
            if createOrderEnabled:
                print(f"已检测到洗衣机{washerName}空闲中!")
                freeWasherList.append(washerName)
            else:
                print(f"洗衣机{washerName}正在运行中...")
        if len(freeWasherList) > 0:
            play_music_toast(f"已检测到洗衣机{freeWasherList}空闲中!")
            return True
        print(f'{sleep}s后重试.')
        print('---------------')
        time.sleep(sleep)
        times += 1


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


def start_reserve(washModel, storeId, deviceList, sleep=90):
    url = "https://phoenix.ujing.online/api/v1/orders/create"
    times = 1
    while True:
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f'第 {times} 次预约: {now_time}')
        for device in deviceList:
            washerName = device['name']
            data = getJSONData(washModel, storeId=storeId, deviceId=device['id'])
            res = request_post(url, get_headers('reserve'), data)
            res_decode = res.content.decode('utf-8')
            res_json = json.loads(res_decode)
            if res_json['code'] == 0:
                print(f"预约 洗衣机{washerName} 成功!")
                order_id = res_json['data']['orderId']
                cancel_order(order_id)
                return 200
            if res_json['code'] == 401:
                print(f"预约 洗衣机{washerName} 失败! token过期! 请重新登录.", res_json)
                login()
                continue
            print(f'预约 洗衣机{washerName} 失败!', res_json)
        print(f'{sleep}s后重试.')
        print('---------------')
        time.sleep(sleep)
        times += 1


def cancel_order(order_id):
    url = f"https://phoenix.ujing.online/api/v1/orders/{order_id}/cancel"
    res = request_post(url, get_headers('reserve'), {'orderId': order_id})
    res_decode = res.content.decode('utf-8')
    res_json = json.loads(res_decode)
    if res_json['code'] == 0:
        print('取消订单成功')
        return 'ok'
    else:
        ValueError("取消订单失败", res_json)


if __name__ == '__main__':

    washerList = read_config('washerList')  # 设备列表
    if len(washerList) == 0:
        getWasherList()
        washerList = read_config('washerList')

    token = read_config('token')
    if token == "":
        print("首次使用, 请先登录.")
        login()

    try:
        startCheckWasherStatus(washerList, 60)
    except Exception as e:
        play_music_toast("监听脚本出错了")
