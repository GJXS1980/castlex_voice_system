#!/usr/bin/python
# -*- coding: UTF-8 -*-

import commands
import threading
import Tkinter as tk
from tkMessageBox import *
from tkFileDialog import *
import ttk
from pyaudio import *
import wave
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import thread

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

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

class Igr_Gui():
    def __init__(self):
        path1 = commands.getoutput("rospack find castle_voice_system")
        path2 = '/scripts/speaker_detect/'
                
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
        self.root.title("性别年龄识别")
        self.root.geometry("470x400")
        self.root.resizable(width=False,height=False)

        ##############     加载图片    ###################
        self.recimg = tk.PhotoImage(file=self.path + 'images/rec.png')
        self.recingimg = tk.PhotoImage(file=self.path + 'images/recing.png')
        self.loadimg = tk.PhotoImage(file=self.path + 'images/load.png')
        self.canimg = tk.PhotoImage(file=self.path + 'images/del.png')
        self.playimg = tk.PhotoImage(file=self.path + 'images/play.png')
        self.pauseimg = tk.PhotoImage(file=self.path + 'images/pause.png')

        ##############     TOP    ###################
        self.top_frame = tk.Frame(self.root)
        self.title_lab = tk.Label(self.top_frame,text="性别年龄识别",font=("Arial",20),padx=10,pady=10)
        self.title_lab.grid(padx=10,pady=10,row=0,column=1,columnspan=4)
        self.top_frame.grid(padx=10,pady=10,row=0,column=1,columnspan=4)

        ##############     按钮    ###################
        self.recBtn = tk.Button(self.root,image=self.recimg,command=self.record)
        self.recBtn.grid(padx=10,pady=10,row=1,column=1)

        self.loadBtn = tk.Button(self.root,image=self.loadimg,command=self.load)
        self.loadBtn.grid(padx=10,pady=10,row=1,column=2)

        self.run_Btn = tk.Button(self.root,text='开始检测',command=self.run)
        self.run_Btn.grid(padx=10,pady=10,row=1,column=4)

        self.playBtn = tk.Button(self.root,image=self.playimg,command=self.play)
        self.canBtn= tk.Button(self.root,image=self.canimg,command=self.cancel)
        self.finishBtn = tk.Button(self.root, image=self.recingimg,command=self.finish)
        self.pauseBtn = tk.Button(self.root, image=self.pauseimg,command=self.pause)

        ########################  文本框和滚动条  ################################
        self.subject_frame = tk.Frame(self.root)
        self.scroll_bar_sub = tk.Scrollbar(self.subject_frame,orient=tk.VERTICAL)
        self.context_sub = tk.Text(self.subject_frame,width=50,height=10,
             yscrollcommand=self.scroll_bar_sub.set,wrap=tk.CHAR)
        self.scroll_bar_sub.config(command=self.context_sub.yview)
        self.scroll_bar_sub.pack(side=tk.RIGHT,fill=tk.Y) 
        self.context_sub.pack()
        self.subject_frame.grid(padx=10,pady=10,row=3,column=1,columnspan=4)
        #######################################################################

    def pause(self):
        self.pauseBtn.grid_forget()
        self.my_play.pause()
        self.playBtn.grid(padx=10,pady=10,row=1,column=1)

    def finish(self):
        self.my_record.stop()
        self.canBtn.grid_forget()
        self.finishBtn.grid_forget()
        self.playBtn.grid(padx=10,pady=10,row=1,column=1)
        self.canBtn.grid(padx=10,pady=10,row=1,column=2)
        self.file_ = 'voice.wav'
        f = open(self.file_,'rb')
        self.music_data = f.read()
        f.close()


    def cancel(self):
        self.playBtn.grid_forget()
        self.pauseBtn.grid_forget()
        self.canBtn.grid_forget()
        self.finishBtn.grid_forget()
        self.recBtn.grid(padx=10,pady=10,row=1,column=1)
        self.loadBtn.grid(padx=10,pady=10,row=1,column=2)
        self.file_ = ''

    def load(self):
        self.file_ = askopenfilename(title="音频",filetypes=[("文件",'*.wav')])
        if self.file_ != '':
            self.loadBtn.grid_forget()
            self.finishBtn.grid_forget()
            self.recBtn.grid_forget()
            self.playBtn.grid(padx=10,pady=10,row=1,column=1)
            self.canBtn.grid(padx=10,pady=10,row=1,column=2)
            f = open(self.file_,'rb')
            self.music_data = f.read()
            f.close()

    def record(self):
        self.my_record.resume()
        self.file_ = 'voice.wav'
        self.loadBtn.grid_forget()
        self.recBtn.grid_forget()
        self.finishBtn.grid(padx=10,pady=10,row=1,column=1)
        self.canBtn.grid(padx=10,pady=10,row=1,column=1)

    def run(self):
        self.param()
        websocket.enableTrace(False)
        self.create_url()
        self.ws = websocket.WebSocketApp(self.url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def param(self):
        self.APPID = '551d49a3'
        self.APIKey = 'f21fabd340ae92bc84ef964fe371ccdf'
        self.APISecret = 'ZmU4NDg1MmRkMWI1NGI0MWM5ZGZkZTQ2'

        # 设置测试音频文件
        self.AudioFile = self.file_
        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"ent": "igr", "aue": "raw", "rate": 16000}

    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/igr'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/igr " + "HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        self.url = url + '?' + urlencode(v)
        print("date: ",date)
        print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        print('websocket url :', self.url)

    # 收到websocket消息的处理
    def on_message(self,ws, message):
        try:    
            print(message)
            code = json.loads(message)["code"]
            if code == 0:
                data_dict = json.loads(message)['data']
                age = data_dict['result']['age']

                if age.get('age_type') == '0':

                    age_type = u'12-40岁'
                elif age.get('age_type') == '1':
                    age_type = u'0-12岁'

                elif age.get('age_type') == '2':
                    age_type = u'40岁以上'

                gender = data_dict['result']['gender']

                if gender['gender_type'] == '0':
                    print('gender0')
                    gender_type = u'女性'
                elif gender['gender_type'] == '1':
                    gender_type = u'男性'
                    print('gender1')
                text = u'识别结果\n' + u'说话人性别为：' + gender_type + u'\n' + u"说话人年龄段为：" + age_type
                self.context_sub.delete(1.0, "end")
                self.context_sub.insert("end",text)
        except Exception as e:
            print("receive msg,but parse exception:", e)
        ws.close()

    # 收到websocket错误的处理
    def on_error(self,ws, error):
        print("### error:", error)

    # 收到websocket关闭的处理
    def on_close(self,ws):
        print("### closed ###")

    # 收到websocket连接建立的处理
    def on_open(self,ws):
        def run(*args):
            frameSize = 5000  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

            with open(self.file_, "rb") as fp:
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = STATUS_LAST_FRAME
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == STATUS_FIRST_FRAME:

                        d = {"common": self.CommonArgs,
                            "business": self.BusinessArgs,
                            "data": {"status": 0, "format": "audio/L16;rate=16000",
                                    "audio": str(base64.b64encode(buf)).decode('utf-8'),
                                    "encoding": "raw"}}
                        d = json.dumps(d)
                        ws.send(d)
                        status = STATUS_CONTINUE_FRAME
                    # 中间帧处理
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                    "audio": str(base64.b64encode(buf)).decode('utf-8'),
                                    "encoding": "raw"}}
                        ws.send(json.dumps(d))
                    # 最后一帧处理
                    elif status == STATUS_LAST_FRAME:
                        d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                    "audio": str(base64.b64encode(buf)).decode('utf-8'),
                                    "encoding": "raw"}}
                        ws.send(json.dumps(d))
                        time.sleep(1)
                        break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
            

        thread.start_new_thread(run, ())

    def play(self):         #播放
        self.my_play.resume(self.file_)
        self.playBtn.grid_forget()
        self.pauseBtn.grid(padx=10,pady=10,row=1,column=1)

    def shutdown(self):
        exit()

    def on_closing(self):
        if askokcancel("Quit", "Do you want to quit?"):
            self.shutdown()

if __name__ == "__main__":
    Igr_Gui()


