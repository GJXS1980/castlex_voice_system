#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import rospy, time
from std_msgs.msg import String
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
import threading
from hgChatGPTpy3_6.V1 import Chatbot

# sudo apt-get install espeak python3-tk
# sudo pip3 install pyttsx3 prompt_toolkit httpx==0.14.0

class ChatGPT_ROS():
    def __init__(self):
        rospy.init_node('chatgpt_node', log_level=rospy.INFO)
        self.result, self.tts_response = None, None
        self.chatbot = Chatbot(config={
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJoY2E5YXJubnduY2hvc3ZycnFAMTY4ODhtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7InVzZXJfaWQiOiJ1c2VyLU50UjZhRFB1a1BLc2VlQk9SWk03ZG5ZZSJ9LCJpc3MiOiJodHRwczovL2F1dGgwLm9wZW5haS5jb20vIiwic3ViIjoiYXV0aDB8NjQzODEyNDFmMjJlYzUyZDczMTdkMTExIiwiYXVkIjpbImh0dHBzOi8vYXBpLm9wZW5haS5jb20vdjEiLCJodHRwczovL29wZW5haS5vcGVuYWkuYXV0aDBhcHAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTY4MTk2OTY1OCwiZXhwIjoxNjgzMTc5MjU4LCJhenAiOiJUZEpJY2JlMTZXb1RIdE45NW55eXdoNUU0eU9vNkl0RyIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgbW9kZWwucmVhZCBtb2RlbC5yZXF1ZXN0IG9yZ2FuaXphdGlvbi5yZWFkIG9mZmxpbmVfYWNjZXNzIn0.rBBZJ6wvqPOCcCGXC4OI1fHlUKcl-7UTwhaxbUIpJWQLOlPVNoX4-L6Hu5XqTjHH4fZBWvg39VZnuimSZwYE4dnJQPzwXPJIbC4eNXkgqL2kDBoRIxYhM36vlgWeFxu-4oIK10pUbupbWGNMxWuKmYublfurFJuC-4q6y7TFarNF3pOAFpa-zOsvbUWLgrcugrBivweIKLEUxA65DtIQZy5SlTIthJ5WjfcFT-SZdQd5eowp6QsIq0cBNhCxUv8QeeZgCbX2me0069AlojptjZ4EEvCze9r3JP7IgnCrnZzLHwLo3-TvuTlleBjl5WTQK7FlEElNEa4J4wUk__oizQ",
        "proxy": "http://78.141.236.201:8080/conversation"
        })

        rospy.Subscriber('/voice/castlex_asr_topic', String , self.voice_callback)
        self.pub = rospy.Publisher('/voice/castlex_nlu_topic', String, queue_size = 1)
        self.count_a, self.count_q = 0, 0

        msFont = '微软雅黑' #字体
        fontSize = 14 #字体大小

        mainWindow = tk.Tk()
        mainWindow.title("hgChatGPT")
        mainWindow.minsize(1000,1000)
        self.show_msg = scrolledtext.ScrolledText(mainWindow, font=(msFont,fontSize))
        self.show_msg.place(width=1000,height=1000,x=0,y=0)

        t = threading.Thread(target=self.msg_recv)
        t.start()
        while not rospy.is_shutdown():
            tk.mainloop()
        
    def voice_callback(self, data):
        self.result = data.data
        prev_text = ""
        for data in self.chatbot.ask(self.result,):
            message = data["message"][len(prev_text) :]
            # print(message,  end="",  flush=True)
            prev_text = data["message"]
        self.tts_response = prev_text

    def msg_recv(self):
        while not rospy.is_shutdown():
            if self.result != None:
                self.count_q += 1
                self.show_msg.insert(tk.END, "Q" + str(self.count_q) + ":" + self.result + "\n")
                self.show_msg.see(tk.INSERT)
                self.result = None
            if self.tts_response != None:
                self.show_msg.insert(tk.END, "A" + str(self.count_q) + ":" + self.tts_response + "\n")
                self.show_msg.see(tk.INSERT)
                self.pub.publish(self.tts_response)
                self.tts_response = None

    def show_info(self, str):
        now = datetime.now()
        s_time = now.strftime("%Y-%m-%d %H:%M:%S")
        str = str.rstrip()
        if len(str) == 0:
            return -1
        temp = s_time + "\n    " + str + "\n"
        self.show_msg.insert(tk.INSERT, "%s" % temp)

if __name__ == '__main__':
    ChatGPT_ROS()
