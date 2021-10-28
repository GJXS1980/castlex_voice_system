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
import threading


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
                
        self.url = "http://webqbh.xfyun.cn/v1/service/v1/qbh"
        self.appid = "551d49a3"
        self.apikey = "f21fabd340ae92bc84ef964fe371ccdf"

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
        self.title_lab = tk.Label(self.top_frame,text="歌曲识别",font=("Arial",20),padx=10,pady=10)
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

        curtime = str(int(time.time()))
        print(curtime)

        param = {
        'engine_type':"afs",
        'aue': "raw",
        "sample_rate":"16000"
        }

        base64_param = base64.urlsafe_b64encode(json.dumps(param).encode('utf-8'))
        tt = base64_param.encode('utf-8')
        print(tt)
        print(type(tt))
        m2 = hashlib.md5()
        m2.update((self.apikey+ curtime+ tt).encode('utf-8'))
        checksum = m2.hexdigest()

        header = {
        "X-CurTime": curtime,
        "X-Param": base64_param,
        "X-Appid": self.appid,
        "X-CheckSum":checksum,
        }
        data = {'data':self.music_data}
        res = requests.post(self.url,headers= header,data = data)
        #res = requests.post(self.url,headers= header,data = json.dumps(self.music_data) )
        result = res.content
        print(result)

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
    Qbh_Gui()