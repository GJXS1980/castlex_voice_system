#!/usr/bin/env python
# -*- coding:utf-8 -*-
#作者：邱定南
#修改日期：2021年4月10日
#  本demo测试时运行的环境为：LINUX + python2.7
#
#  语音评测流式 WebAPI 接口调用示例 接口文档（必看）：https://www.xfyun.cn/doc/Ise/IseAPI.html
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import Tkinter as tk
from tkMessageBox import *
from tkFileDialog import *
import ttk
from pyaudio import *
import wave
import commands
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
import threading
import random
import os
import lxml 
from lxml import etree

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
        
        self.chunk = 256   #数据块大小
        self.rate = 16000  #采样率
        self.NUM_SAMPLES = 256   #帧大小
        self.channels = 1   #声道
        self.sampwidth = 2  #数据位数2B=16bit

    def run(self):
        count = 0
        while 1:
            while self.__running.isSet(): #停止
                if count == 0:
                    try: 
                        pa=PyAudio()
                    except:
                        pa=PyAudio()
                    stream=pa.open(format = paInt16,channels=self.channels,
                    rate=self.rate,input=True,
                    frames_per_buffer=self.NUM_SAMPLES)
                    
                    my_buf=[]
                    count = 1
		    print('录音开始')
                self.__flag.wait()  #暂停
                string_audio_data = stream.read(self.NUM_SAMPLES)
                my_buf.append(string_audio_data)
            
            time.sleep(1)
            if count != 0:
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
        
    def run(self):
        count = 0
        while 1:
            while self.__running.isSet(): #停止
                if count == 0:
                    try: 
                        pa=PyAudio()
                    except:
                        pa=PyAudio()
                    filepath = self.filepath
                    f = wave.open(filepath,'rb')
                    pns = f.getparams()
                    nchannels, sampwidth, framerate, nframes = pns[:4]
                    stream=pa.open(format = pa.get_format_from_width(sampwidth),channels=nchannels,
                    rate=framerate,output=True)
                    count = 1
                self.__flag.wait()  #暂停
                data = f.readframes(1024)
                stream.write(data)
                if data == '':
                    self.__running.clear()
            
            time.sleep(1)
            if count != 0:
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

class Ws_Gui():
    def __init__(self):
        path1 = commands.getoutput("rospack find castle_voice_system")
        path2 = '/scripts/evaluating/'
        self.path = path1 + path2
        self.filename = 'evalauting.wav'
        self.Text = ''
        self.load_test()
        self.my_record = my_record()
        self.my_record.setDaemon(True)
        self.my_record.start()

        self.my_play = my_play()
        self.my_play.setDaemon(True)
        self.my_play.start()

        self.root_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def load_test(self):
        files = os.listdir('./test_pool')
        self.test_dict = {}
        for f in files:
            self.test_dict[f[:-4]] = open('./test_pool/'+f,'rb').read().split('\n')

    def root_window(self):
        self.root = tk.Tk()
        self.root.title("语音测评")
        self.root.geometry("470x800")
        #self.root.resizable(width=False,height=False)

        ##############     加载图片    ###################
        self.recimg = tk.PhotoImage(file=self.path + 'images/rec.png')
        self.recingimg = tk.PhotoImage(file=self.path + 'images/recing.png')
        self.loadimg = tk.PhotoImage(file=self.path + 'images/load.png')
        self.canimg = tk.PhotoImage(file=self.path + 'images/del.png')
        self.playimg = tk.PhotoImage(file=self.path + 'images/play.png')
        self.pauseimg = tk.PhotoImage(file=self.path + 'images/pause.png')

        self.top_frame = tk.Frame(self.root)

        self.title_lab = tk.Label(self.top_frame,text="语音测评平台",font=("Arial",20),padx=10,pady=10)
        self.title_lab.grid(padx=10,pady=10,row=0,column=1,columnspan=4)

        ######################  模式选择   ############################
        self.lua_lab = tk.Label(self.top_frame,text='语言选择:')
        self.lua_lab.grid(padx=10,pady=5,row=1,column=1)
        self.lua_var = tk.IntVar()
        self.lua_var.set(1)

        tk.Radiobutton(self.top_frame,text='中文',variable=self.lua_var,value=1,command=self.language).grid(padx=10,pady=10,row=1,column=2)
        tk.Radiobutton(self.top_frame,text='英文',variable=self.lua_var,value=2,command=self.language).grid(padx=10,pady=10,row=1,column=3)

        self.mode_lab = tk.Label(self.top_frame,text='模式选择:')
        self.mode_lab.grid(padx=10,pady=5,row=2,column=1)
        
        self.mode_cn_var = tk.StringVar()
        self.mode_cn_var.set('单字朗读')
        self.mode_cn_com = ttk.Combobox(self.top_frame,textvariable=self.mode_cn_var)
        self.mode_cn_com.grid(padx=10,pady=5,row=2,column=2,columnspan=2)
        self.mode_cn_com['value'] = ("单字朗读","词语朗读","句子朗读","篇章朗读")
        self.mode_cn_com.bind("<<ComboboxSelected>>", self.mode_cn_selet)

        self.mode_en_var = tk.StringVar()
        self.mode_en_var.set('词语朗读',)
        self.mode_en_com = ttk.Combobox(self.top_frame,textvariable=self.mode_en_var)
        self.mode_en_com['value'] = ("句子朗读","篇章朗读")
        self.mode_en_com.bind("<<ComboboxSelected>>", self.mode_en_selet)

        self.random_btn = tk.Button(self.top_frame,text="随机题目",command=self.random_subject).grid(padx=10,pady=5,row=2,column=4)
        ##############################################################

        self.top_frame.grid(padx=10,pady=10,row=1,column=1,columnspan=4)

        self.recBtn = tk.Button(self.root,image=self.recimg,command=self.record)
        self.recBtn.grid(padx=10,pady=10,row=4,column=1)

        self.loadBtn = tk.Button(self.root,image=self.loadimg,command=self.load)
        self.loadBtn.grid(padx=10,pady=10,row=4,column=2)

        self.run_Btn = tk.Button(self.root,text='开始测评',command=self.run)
        self.run_Btn.grid(padx=10,pady=10,row=4,column=4)

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

        self.result_frame = tk.Frame(self.root)
        self.scroll_bar_res = tk.Scrollbar(self.result_frame,orient=tk.VERTICAL)
        self.context_res = tk.Text(self.result_frame,width=50,height=10,
             yscrollcommand=self.scroll_bar_res.set,wrap=tk.CHAR)
        self.scroll_bar_res.config(command=self.context_res.yview)
        self.scroll_bar_res.pack(side=tk.RIGHT,fill=tk.Y) 
        self.context_res.pack()
        self.result_frame.grid(padx=10,pady=10,row=5,column=1,columnspan=4)
        self.language()
        #######################################################################

    ####################################################################
    #                                               修改语言时重新获取模式                                                          #
    def language(self): 
        if self.lua_var.get() == 1:
            self.language_ = 'cn'
            self.mode_en_com.grid_forget()
            self.mode_cn_com.grid(padx=10,pady=5,row=2,column=2,columnspan=2)
            self.mode_cn_selet()
        else:
            self.language_ = 'en'
            self.mode_cn_com.grid_forget()
            self.mode_en_com.grid(padx=10,pady=5,row=2,column=2,columnspan=2)
            self.mode_en_selet()

    def mode_cn_selet(self,*args):
        mode_cn_dict = {'单字朗读':'read_syllable',
                                             '词语朗读':'read_word',
                                             '句子朗读':'read_sentence',
                                             '篇章朗读':'read_chapter'}
        self.mode_ = mode_cn_dict.get(self.mode_cn_var.get().encode('utf-8'))
        
    def mode_en_selet(self,*args):
        mode_en_dict = {'词语朗读':'read_word',
                                             '句子朗读':'read_chapter',
                                             '篇章朗读':'read_chapter',
                                             '英文情景反应':'simple_expression',
                                             '英文选择题':'read_choice',
                                             '英文自由题':'topic',
                                             '英文复述题':'retell',
                                             '英文看图说话':'picture_talk',
                                             '英文口头翻译':'oral_translation'}
        self.mode_ = mode_en_dict.get(self.mode_en_var.get().encode('utf-8'))
    #                                                                                                                                                                   #
    ####################################################################

    def param(self):
        self.APPID='551d49a3'
        self.APISecret='ZmU4NDg1MmRkMWI1NGI0MWM5ZGZkZTQ2'
        self.APIKey='f21fabd340ae92bc84ef964fe371ccdf'
        Sub = "ise"
        self.Ent = ent =  self.language_ + '_vip'
        TEXT = u'\uFEFF'+ self.Text.decode("utf-8")
        self.CommonArgs = {"app_id": self.APPID}
        print(self.CommonArgs)
        self.BusinessArgs = {"category": self.mode_, "sub": Sub, "ent": self.Ent, "cmd": "ssb", "auf": "audio/L16;rate=16000",
                             "aue": "raw", "text": TEXT, "ttp_skip": True, "aus": 1}
        print(self.BusinessArgs)

    def create_url(self):

        STATUS_FIRST_FRAME = 0  # 第一帧的标识
        STATUS_CONTINUE_FRAME = 1  # 中间帧标识
        STATUS_LAST_FRAME = 2  # 最后一帧的标识
        # wws请求对Python版本有要求，py3.7可以正常访问，如果py版本请求wss不通，可以换成ws请求，或者更换py版本
        url = 'ws://ise-api.xfyun.cn/v2/open-ise'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ise-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/open-ise " + "HTTP/1.1"
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
            "host": "ise-api.xfyun.cn"
        }
        print("date: ", date)
        print("v: ", v)
        
        # 拼接鉴权参数，生成url
        self.url = url + '?' + urlencode(v)
        print('websocket url :', self.url)

    # 收到websocket消息的处理
    def on_message(self,ws, message):
        try:
            code = json.loads(message)["code"]
            sid = json.loads(message)["sid"]
            if code != 0:
                errMsg = json.loads(message)["message"]
                print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

            else:
                data = json.loads(message)["data"]
                status = data["status"]
                result = data["data"]
                if (status == 2):
                    xml = base64.b64decode(result)
                    f = open('result.xml','w')
                    f.write(xml)
                    f.close()
                    #python在windows上默认用gbk编码，print时需要做编码转换，mac等其他系统自行调整编码

        except Exception as e:
            print("receive msg,but parse exception:", e)


    # 收到websocket错误的处理
    def on_error(self,ws, error):
        print("### error:", error)

    # 收到websocket关闭的处理
    def on_close(self,ws):
        print("### closed ###")

    # 收到websocket连接建立的处理
    def on_open(self,ws):
        def run(*args):
            frameSize = 1280  # 每一帧的音频大小
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
                            "data": {"status": 0}}
                        d = json.dumps(d)
                        ws.send(d)
                        status = STATUS_CONTINUE_FRAME
                    # 中间帧处理
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {"business": {"cmd": "auw", "aus": 2, "aue": "raw"},
                            "data": {"status": 1, "data": str(base64.b64encode(buf).decode())}}
                        ws.send(json.dumps(d))
                    # 最后一帧处理
                    elif status == STATUS_LAST_FRAME:
                        d = {"business": {"cmd": "auw", "aus": 4, "aue": "raw"},
                            "data": {"status": 2, "data": str(base64.b64encode(buf).decode())}}
                        ws.send(json.dumps(d))
                        time.sleep(1)
                        break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
            ws.close()

        thread.start_new_thread(run, ())



    def run(self):
        # '''
        # #  BusinessArgs参数常量
        # SUB = "ise"
        # ENT = "cn_vip"
        # CATEGORY = "read_sentence"
        # #待评测文本 utf8 编码，需要加utf8bom 头
        # TEXT ="今天天气怎么样"
        # #直接从文件读取的方式
        # #TEXT = '\uFEFF'+ open("cn/read_sentence_cn.txt","r",encoding='utf-8').read()'''
        #APPID、APISecret、APIKey信息在控制台——语音评测了（流式版）——服务接口认证信息处即可获取
        if self.Text == '':
            self.context_res.delete(1.0, "end")
            self.context_res.insert('end',"未设置题目")
        else:
            self.param()
            self.create_url()
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(self.url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
            self.ws.on_open = self.on_open
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            self.xml_analysis()


    def pause(self):
        self.pauseBtn.grid_forget()
        self.my_play.pause()
        self.playBtn.grid(padx=10,pady=10,row=4,column=1)

    def finish(self):
        self.my_record.stop()
        self.canBtn.grid_forget()
        self.finishBtn.grid_forget()
        self.playBtn.grid(padx=10,pady=10,row=4,column=1)
        self.canBtn.grid(padx=10,pady=10,row=4,column=2)
        self.file_ = 'voice.wav'

    def cancel(self):
        self.playBtn.grid_forget()
        self.pauseBtn.grid_forget()
        self.canBtn.grid_forget()
        self.finishBtn.grid_forget()
        self.recBtn.grid(padx=10,pady=10,row=4,column=1)
        self.loadBtn.grid(padx=10,pady=10,row=4,column=2)
        self.file_ = ''

    def load(self):
        self.file_ = askopenfilename(title="音频",filetypes=[("文件",'*.wav')])
        if self.file_ != '':
            self.loadBtn.grid_forget()
            self.finishBtn.grid_forget()
            self.recBtn.grid_forget()
            self.playBtn.grid(padx=10,pady=10,row=4,column=1)
            self.canBtn.grid(padx=10,pady=10,row=4,column=2)

    def record(self):
        self.my_record.resume()
        self.file_ = 'voice.wav'
        self.loadBtn.grid_forget()
        self.recBtn.grid_forget()
        self.finishBtn.grid(padx=10,pady=10,row=4,column=1)
        self.canBtn.grid(padx=10,pady=10,row=4,column=1)

    def on_closing(self):
        if askokcancel("Quit", "Do you want to quit?"):
            self.shutdown()

    ##################    随机选择题目    ########################
    def random_subject(self):
        if self.language_ == 'cn':
            self.context_sub.delete(1.0, "end")
            self.Text = random.choice(self.test_dict.get('cn_'+self.mode_))
            self.context_sub.insert("end",self.Text)

            
        elif self.language_ == 'en':   
            self.context_sub.delete(1.0, "end")
            self.Text = random.choice(self.test_dict.get('en_'+self.mode_))
            self.context_sub.insert("end",self.Text)
###############################################################

    def play(self):         #播放
        self.my_play.resume(self.file_)
        self.playBtn.grid_forget()
        self.pauseBtn.grid(padx=10,pady=10,row=4,column=1)

    def shutdown(self):
        exit()

     # TODO 解析xml文件
    def xml_analysis(self):
        
        f = open('result.xml','r')
        data = f.read()
        xml = etree.HTML(data)
        self.context_res.delete(1.0, "end")

        if self.language_ == 'cn':
            #content_ =  xml.xpath('//read_syllable/@content')[0]
            except_info_ = str(xml.xpath('//'+self.mode_+'/@except_info')[0])
            fluency_score_ = str(xml.xpath('//'+self.mode_+'/@fluency_score')[0])
            integrity_score_ = str(xml.xpath('//'+self.mode_+'/@integrity_score')[0])
            phone_score_ = str(xml.xpath('//'+self.mode_+'/@phone_score')[0])
            tone_score_ = str(xml.xpath('//'+self.mode_+'/@tone_score')[0])
            total_score_ = str(xml.xpath('//'+self.mode_+'/@total_score')[0])
            text = u'声调分：'+phone_score_+'\n'+u'完整性分：'+integrity_score_+ '\n'+u'流畅度分：'+fluency_score_+'\n'+u'调型分：'+tone_score_+'\n'+u'总分：'+total_score_

        if self.language_ == 'en':
            #content_ =  xml.xpath('//read_syllable/@content')[0]
            except_info_ = str(xml.xpath('//'+self.mode_+'/@except_info')[0])
            fluency_score_ = str(xml.xpath('//'+self.mode_+'/@fluency_score')[0])
            integrity_score_ = str(xml.xpath('//'+self.mode_+'/@integrity_score')[0])
            standard_score_ = str(xml.xpath('//'+self.mode_+'/@standard_score')[0])
            word_count_ = str(xml.xpath('//'+self.mode_+'/@word_count')[0])
            total_score_ = str(xml.xpath('//'+self.mode_+'/@total_score')[0])

        
        #text = '试题文本:'+content_.decode('utf_8')+'\n声韵分:'+phone_score_.decode('utf_8')+'\n流畅度分:'+fluency_score_.decode('utf_8')+'\n调型分:'+tone_score_.decode('utf_8')+'\n总分:'+total_score_.decode('utf_8')
        #text = '\n声韵分:'+phone_score_+'\n流畅度分:'+fluency_score_+'\n调型分:'+tone_score_+'\n总分:'+total_score_
            text = u'标准型分：'+standard_score_+'\n'+u'完整性分'+integrity_score_+ '\n'+u'流畅度分：'+fluency_score_+'\n'+u'词语总数：'+word_count_+'\n'+u'总分：'+total_score_


        self.context_res.insert('end',text)


STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识







if __name__ == "__main__":
    # 测试时候在此处正确填写相关信息即可运行
    Ws_Gui()

