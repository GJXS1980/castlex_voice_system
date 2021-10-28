#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import json 
import commands
import hashlib
import time
import Tkinter as tk
import ttk
from tkMessageBox import *
from tkFileDialog import *
import os

class Nlu_Kb_Gui():
    def __init__(self):
        #图灵WEB_API接口
        self.ask_url = 'http://openapi.tuling123.com/openapi/api/v2'
        self.add_url = "http://www.tuling123.com/v1/kb/import"
        self.match_url = "http://www.tuling123.com/v1/kb/match"
        self.check_url = "http://www.tuling123.com/v1/kb/select"
        self.del_url = "http://www.tuling123.com/v1/kb/delete"

        self.select_key  = ""

        #图灵apiKey
        #TODO 将apiKey通过Pyc隐藏
        self.apiKey = '552c0addb08d4c73ab85868c2e68b22d'
        self.userId = "HGcastle"
        #定义一个字典用于保存新增语料的信息，用于显示和删除
        self.db_dict = {} 
        self.l =[]
        self.root_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        #token = self.encryption(time.time())

    def set_new_frame(self):
        #定义新增语料界面的组件
        self.logo_2 = tk.Label(self.new_frame,image = self.img)
        self.logo_2.grid(padx=10,pady=20,row=0,column=1,columnspan=4)
        self.back_Btn = tk.Button(self.new_frame,text='取消',command=self.back,padx=20,pady=5,font=("Arial",20))
        self.con_Btn = tk.Button(self.new_frame,text='确定',command=lambda: self.add(self.Q_ent.get(),self.A_ent.get()),padx=20,pady=5,font=("Arial",20))
        self.Q_ent = tk.Entry(self.new_frame,width=24,font=("Arial",20))
        self.A_ent = tk.Entry(self.new_frame,width=24,font=("Arial",20))
        self.Q_label = tk.Label(self.new_frame, text='问题',font=("Arial",20))
        self.A_label = tk.Label(self.new_frame, text='回答',font=("Arial",20))
        
        #设置组件的位置
        self.back_Btn.grid(padx=10,pady=20,row=5,column=1,columnspan=2)
        self.con_Btn.grid(padx=10,pady=20,row=5,column=3,columnspan=2)
        self.Q_label.grid(padx=10,pady=30,row=1,column=1)
        self.A_label.grid(padx=10,pady=30,row=2,column=1)
        self.Q_ent.grid(padx=10,pady=10,row=1,column=2,columnspan=2)
        self.A_ent.grid(padx=10,pady=10,row=2,column=2,columnspan=2)

    def set_base_frame(self):
        #定义根目录界面的组件
        self.str_var = tk.StringVar()
        self.msg_var = tk.StringVar()
        path1 = commands.getoutput("rospack find castle_voice_system")
        self.img = tk.PhotoImage(file=path1 + "/res/HG.png")
        self.logo_1 = tk.Label(self.base_frame,image = self.img)
        self.logo_1.grid(padx=10,pady=20,row=0,column=1,columnspan=4)

        self.new_Btn = tk.Button(self.base_frame,text='新增语料',command=self.new,padx=20,pady=5)
        self.delete_Btn = tk.Button(self.base_frame,text='删除语料',command=lambda: self.delete(self.select_key) ,padx=20,pady=5)
        #self.refresh_Btn = tk.Button(self.base_frame,text='刷新',command=self.check,padx=20,pady=5)
        self.save_Btn = tk.Button(self.base_frame,text='删除所有语料',command=lambda: self.delete("all"),padx=20,pady=5)
        self.exit_Btn = tk.Button(self.base_frame,text='退出',command=self.shutdown,padx=20,pady=5)
        self.sent_Btn = tk.Button(self.base_frame,text='发送',command=lambda: self.ask(self.data_ent.get()),padx=20,pady=5)
        self.data_ent = tk.Entry(self.base_frame,width=40)
        self.msg = tk.Message(self.base_frame,textvariable=self.msg_var,width=300,borderwidth=2,relief="ridge",anchor="w",justify="left")

        #self.match_ent = tk.Entry(self.base_frame,width=10)
        #self.match_label = tk.Label(self.base_frame, text='问答匹配度')
        columns = ('序号','问题','答案')
        self.treeview = ttk.Treeview(self.base_frame,height=10,show="headings",columns=columns)
        for i in range(len(columns)):      #做表头
            if i:
                self.treeview.column(columns[i],width=200,anchor='center')
            else:
                self.treeview.column(columns[i],width=50,anchor='center')
            self.treeview.heading(columns[i], text=columns[i])
            i +=1        

        #设置组件的位置
        self.new_Btn.grid(padx=10,pady=10,row=2,column=1)
        self.delete_Btn.grid(padx=10,pady=10,row=2,column=2)
        #self.refresh_Btn.grid(padx=10,pady=10,row=2,column=3)
        self.exit_Btn.grid(padx=10,pady=10,row=2,column=4)
        self.save_Btn.grid(padx=10,pady=10,row=2,column=3)
        self.sent_Btn.grid(padx=10,pady=10,row=5,column=4)
        self.data_ent.grid(padx=10,pady=10,row=5,column=1,columnspan=3)
        #self.match_label.grid(padx=10,pady=10,row=1,column=1)
        #self.match_ent.grid(padx=10,pady=10,row=1,column=2)
        self.treeview.grid(padx=10,pady=10,row=3,column=1,columnspan=4)
        self.msg.grid(padx=10,pady=10,row=6,column=1,columnspan=3)

        self.treeview.bind('<ButtonRelease-1>', self.select)  #左键单击
        
    def shutdown(self):
        self.delete("all")
        exit()

    
    def select(self, event):                                            
        column = self.treeview.identify_column(event.x)
        row = self.treeview.identify_row(event.y)

        try:
            cn = int(str(column).replace('#',''),16)
            rn = int(str(row).replace('I',""),16)
            self.rn = rn - 1
            self.item = self.treeview.selection()
            self.item_data = list(self.treeview.item(self.item,"values"))
            self.select_key = self.item_data[1]
            print(self.select_key)
        except : pass

    def on_closing(self):
        if askokcancel("Quit", "Do you want to quit?"):
            self.shutdown()

    def root_window(self):
        self.root = tk.Tk()
        self.root.title("慧谷语音教学语料库")
        self.root.geometry("470x800")
        self.root.resizable(width=False,height=False)
        self.new_frame = tk.Frame(self.root)
        self.base_frame = tk.Frame(self.root)
        self.set_base_frame()
        self.set_new_frame()
        self.base_frame.grid()


    def new(self):
        self.base_frame.grid_forget()
        self.new_frame.grid()

    def back(self):
        self.new_frame.grid_forget()
        self.base_frame.grid()

    def encryption(self, data):
        md5 = hashlib.md5()
        md5.update(self.apiKey + str(data))
        results = md5.hexdigest()
        return results

    def ask(self,data):
        data = {"perception": {"inputText": {"text": data},"inputImage": {"url": "imageUrl"},"selfInfo": {"location": {"city": "","province": "","street": ""}}},"userInfo": {"apiKey": self.apiKey,"userId": self.userId},"reqType":0}
        response = requests.post(self.ask_url, data = json.dumps(data))
        results = response.json(encoding="UTF-8")["results"][0]
        values = results["values"]
        text = values["text"].encode("UTF-8")
        self.msg_var.set(text)

    def match(self,data):
        data = {"apikey": self.apiKey ,"data":{"match":data},"timestamp": str(time.time()), "token":self.encryption(time.time())}
        headers = {'Content-Type': "application/json"}
        response = requests.post(self.match_url, data = json.dumps(data),headers = headers)

    def add(self,Q,A):
        response = {}
        #data = {"apikey":self.apiKey, "data":{"list":[{"question":Q, "answer":A}]},"timestamp": str(time.time()) ,"token":self.encryption(time.time())}
        data = {"apikey":self.apiKey, "data":{"list":[{"question":Q, "answer":A}]}	,"timestamp": str(time.time()), "token":self.encryption(time.time())}
        headers = {'Content-Type': "application/json"}
        try:
            response = requests.post(self.add_url, data = json.dumps(data),headers = headers)
            if response.json()["code"] == 0:      #返回代码0，表示成功
                showinfo("成功",'语料添加成功')
                ID = response.json()["data"]["knowledgeList"][0]["id"]
                #self.db_dict[ID] = [Q,A]    #{id:{Q:A}}
                self.db_dict[Q] = [ID,A]
                self.back()
                self.check()
            elif response.json()["code"] == '501':
                showerror("错误",'网络错误')
            elif response.json()["code"] == '401':
                showerror("错误",'权限错误')
        except :
            showerror("错误",'请检查网络是否连接')

    def check(self):
        key_list = []
        value_list = []
        x=self.treeview.get_children()
        for item in x:
            self.treeview.delete(item)
        
        key_list = list(self.db_dict.keys())
        for i in key_list:
            value = self.db_dict.get(i)
            value_list.append(value[1])

        for i in range(len(key_list)):
            self.treeview.insert('',i,value=[i+1,key_list[i],value_list[i]])
            self.l.append([i+1,key_list[i],value_list[i]])

    def delete(self,key):
        id_list = []
        response = {}
        headers = {'Content-Type': "application/json"}
        if key =="all":
            key_list = self.db_dict.keys()
            for i in key_list:
                id_list.append(self.db_dict.get(i)[0])
            data = {"apikey": self.apiKey,"data": {"clear": "false","isclear":"true","ids": id_list},"timestamp": str(time.time()), "token":self.encryption(time.time())}  
            try:
                response = requests.post(self.del_url, data = json.dumps(data),headers = headers)
                self.db_dict = {}
                self.check()
            except :
                showerror("错误",'请检查网络是否连接')
        
        else:  
            data = {"apikey": self.apiKey,"data": {"clear": "false","isclear":"true","ids": [self.db_dict[key][0]]},"timestamp": str(time.time()), "token":self.encryption(time.time())}  

            try:
                response = requests.post(self.del_url, data = json.dumps(data),headers = headers)
                self.db_dict.pop(key)
                self.check()
            except :
                showerror("错误",'请检查网络是否连接')

    #TODO 捕捉退出信号，清除添加的语料


Nlu_Kb_Gui()



