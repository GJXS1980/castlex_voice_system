import requests
import base64
import json
import time
import hashlib


def music_iat():
    url = "http://webqbh.xfyun.cn/v1/service/v1/qbh"
    appid = "551d49a3"
    apikey = "f21fabd340ae92bc84ef964fe371ccdf"
    curtime = str(int(time.time()))
    print(curtime)

	# 使用audio_url传输音频数据时，http request body须为空。
	# 直接把音频二进制数据写入到Http Request Body时，不需要设置audio_url参数
    param = {
        'engine_type':"afs",
        'aue': "raw",
        "sample_rate":"16000"
    }
    base64_param = base64.urlsafe_b64encode(json.dumps(param).encode('utf-8'))
    tt = str(base64_param,'utf-8')
    m2 = hashlib.md5()
    m2.update((apikey+ curtime+ tt).encode('utf-8'))
    checksum = m2.hexdigest()
    header = {
        "X-CurTime": curtime,
        "X-Param": base64_param,
        "X-Appid": appid,
        "X-CheckSum":checksum,
    }

    f = open('music.wav','rb')
    data = f.read()

    res = requests.post(url,headers= header,data = json.dumps(data) )
    result = res.content
    print(result)


if __name__ == "__main__":
    music_iat()