import requests
import base64
import json
import time
import hashlib
import Tkinter as tk
from tkMessageBox import *
from tkFileDialog import *
import ttk
from pyaudio import *
import wave
import commands

def save_wave_file(filename,data):   #保存录制的音频数据为WAV
    chunk = 256   #数据块大小
    rate = 16000  #采样率
    NUM_SAMPLES = 256   #帧大小
    channels = 1   #声道
    sampwidth = 2  #数据位数2B=16bit

    '''save the date to the wavfile'''
    wf=wave.open(filename,'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(rate)
    wf.writeframes(b"".join(data))
    wf.close()

class my_record(threading.Thread):       #录音

    def __init__(self,*args, **kwargs):
        super(my_record,self).__init__(*args,**kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()
        self.__running = threading.Event()
        self.__running.clear()
        print("线程初始化")
        
        self.chunk = 256   #数据块大小
        self.rate = 16000  #采样率
        self.NUM_SAMPLES = 256   #帧大小
        self.channels = 1   #声道
        self.sampwidth = 2  #数据位数2B=16bit

    def run(self):
        print("线程运行")
        count = 0
        while 1:
            while self.__running.isSet(): #停止
                if count == 0:
                    try: 
                        pa=PyAudio()
                    except:
                        pa=PyAudio()
                    print("线程创建流")
                    stream=pa.open(format = paInt16,channels=self.channels,
                    rate=self.rate,input=True,
                    frames_per_buffer=self.NUM_SAMPLES)
                    
                    my_buf=[]
                    count = 1
                self.__flag.wait()  #暂停
                print("线程录音")
                string_audio_data = stream.read(self.NUM_SAMPLES)
                my_buf.append(string_audio_data)
            
            time.sleep(1)
            if count != 0:
                print("线程保存文件")
                save_wave_file('voice.wav',my_buf)
                stream.close()
                count = 0
                my_buf = []
            else:pass

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__running.set()
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        self.__running.clear()



class my_play(threading.Thread):       #播放

    def __init__(self,*args, **kwargs):
        super(my_play,self).__init__(*args,**kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()
        self.__running = threading.Event()
        self.__running.clear()
        print("线程初始化")
        
    def run(self):
        print("线程运行")
        count = 0
        while 1:
            while self.__running.isSet(): #停止
                if count == 0:
                    try: 
                        pa=PyAudio()
                    except:
                        pa=PyAudio()
                    print("线程创建流")
                    filepath = self.filepath
                    f = wave.open(filepath,'rb')
                    pns = f.getparams()
                    nchannels, sampwidth, framerate, nframes = pns[:4]
                    stream=pa.open(format = pa.get_format_from_width(sampwidth),channels=nchannels,
                    rate=framerate,output=True)
                    count = 1
                self.__flag.wait()  #暂停
                print("线程播放")
                data = f.readframes(1024)
                stream.write(data)
                if data == '':
                    self.__running.clear()
            
            time.sleep(1)
            if count != 0:
                print("停止播放")
                stream.close()
                count = 0
            else:pass

    def pause(self):
        self.__flag.clear()

    def resume(self,filepath):
        self.filepath = filepath
        self.__running.set()
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        self.__running.clear()

class Qbh_Gui():
    def __init__(self):
        path1 = commands.getoutput("rospack find castle_voice_system")
        path2 = '/scripts/detect/'
        self.path = path1 + path2
        self.file_ = 'music.wav'
        self.my_record = my_record()
        self.my_record.setDaemon(True)
        self.my_record.start()

        self.my_play = my_play()
        self.my_play.setDaemon(True)
        self.my_play.start()

        self.root_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def root_window(self):
        self.root = tk.Tk()
        self.root.title("歌曲识别")
        self.root.geometry("470x800")
        #self.root.resizable(width=False,height=False)



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