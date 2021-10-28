#!/usr/bin/python
# -*- coding: UTF-8 -*-

from xml.dom.minidom import parse
import xml.dom.minidom
import rospy
from pixel_ring import pixel_ring
from math import sin, cos, pi, sqrt
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32, Float32, String, Int32MultiArray


#from aip import AipSpeech
from playsound import playsound
import os

class XML_Analysis():
    def __init__(self):
        rospy.init_node('XML_Analysis', log_level=rospy.INFO)
        #在launch文件中获取参数

        self.topic = rospy.get_param("~topic", "/cmd_vel")
        self.file_path = rospy.get_param("~file_path", "/params/castle_mic_cmd.xml")
        self.Conf = rospy.get_param("~Confidence", "50")

        self.sub = rospy.Subscriber('/voice/castle_order_topic', String , self.cmd_callback)
        self.cmd_vel_pub = rospy.Publisher(self.topic, Twist, queue_size = 1)     #发布速度话题
        #self.order_pub = rospy.Publisher('voice/castle_order_topic', Int32, queue_size = 1)   #发布命令词识别失败信息，通知语音交互模块工作
        self.DOMTree = None
        self.nlp = None
        self.version = None
        self.rawtext = None
        self.rawtext_data = None
        self.confidence = None
        self.confidence_data = None
        self.engine = None
        self.focus = None
        self.result_confidence = None
        self.result_confidence_data = None

        self.command = None
        self.command_id = None

        self.color_dict = {'0':[255,0,0],
                                            '1':[255,140,0],
                                            '2':[255,255,0],
                                            '3':[0,255,0],
                                            '4':[0,255,255],
                                            "5":[0,0,255],
                                            '6':[138,43,226]}

        self.cmd_flag = False

        self.voice1 = rospy.get_param("~failed_file_path", "/params/voice/failed.mp3")
        self.voice2 = rospy.get_param("~Received_file_path", "/params/voice/Received.mp3")
        self.voice3 = rospy.get_param("~ReEnterAuido_file_path", "/params/voice/ReEnterAuido.mp3")
        self.brightness = int(rospy.get_param("~brightness",'255'))

        self.r = rospy.Rate(10)
        while not rospy.is_shutdown():
            if self.cmd_flag is True:
                self.analysis_file()
                self.Process_Speech_cmd_to_Speed()
                self.cmd_flag = False
            self.r.sleep()

    # 使用minidom解析器打开 XML 文档
    def open_xml_file(self):
        self.DOMTree = xml.dom.minidom.parse(self.file_path)
        self.nlp = self.DOMTree.documentElement #获取nlp节点

    def analysis_file(self):
        self.open_xml_file()
        if self.nlp.hasChildNodes():
            self.version = self.nlp.getElementsByTagName('version')[0]
            #print "version: %s" % version.childNodes[0].data
            self.rawtext = self.nlp.getElementsByTagName('rawtext')[0]
            self.rawtext_data = self.rawtext.childNodes[0].data
            #print "rawtext: %s" % self.rawtext.childNodes[0].data
            self.confidence = self.nlp.getElementsByTagName('confidence')[0]
            self.confidence_data = self.confidence.childNodes[0].data
            #print "confidence: %s" % self.confidence.childNodes[0].data
            self.engine = self.nlp.getElementsByTagName('engine')[0]
            #print "engine: %s" % self.engine.childNodes[0].data

            self.result = self.nlp.getElementsByTagName("result")[0] #获取result节点

            self.focus = self.result.getElementsByTagName('focus')[0]
            self.focus_data = map(str,self.focus.childNodes[0].data.split('|'))

            self.result_confidence = self.result.getElementsByTagName('confidence')[0]
            self.result_confidence_data = map(int,self.result_confidence.childNodes[0].data.split('|'))
            # print "confidence:", self.result_confidence_data
            self.object = self.nlp.getElementsByTagName("object")[0] #获取object节点

            try:
                self.command = self.object.getElementsByTagName('commands')[0]
                # print "start: %s" % self.start.childNodes[0].data
                if self.command.hasAttribute("id"):
                    self.command_id = int(self.command.getAttribute("id"))
                    # print "start id: %s" %  self.start.getAttribute("id")
            except IndexError:
                self.command = None
                self.command_id = 306
                print 'No start'

            print "解析完成.....\n"
        
        else:
            print "No XML"

    def cmd_callback(self, req):
        print "命令词识别成功，正在解析命令词结果..."
        self.cmd_flag = True

    def Process_Speech_cmd_to_Speed(self):
        # print "文本： ", self.rawtext_data #打印会话果
        if (self.command_id==306):
        
            #self.order_pub.publish(1)
            print '您输入的信息不完整，请重新输入！'
            playsound(self.voice3)
        else:
            print self.result_confidence_data[self.focus_data.index('commands')]
            if self.result_confidence_data[self.focus_data.index('commands')]> 0:
                self.goal_point_msg = Int32MultiArray()
                self.goal_point_msg.data = [self.command_id, 0, 0]
                print "命令词解析得到命令ＩＤ：", self.command_id
                print '小谷：好的，收到!'
                playsound(self.voice2)
                self.execute()
                #self.pub.publish(self.goal_point_msg)
            else:
                print '语音识别未通过，请重新输入！'
                playsound(self.voice1)

    def execute(self):
        key = str(self.command_id)
        print(key)
        print(type(key))
        if key in self.color_dict:
            print("灯光颜色")
            color = self.color_dict.get(key)
            print(color)
            pixel_ring.set_color(r=color[0],g=color[1],b=color[2])
        if key == "7":
            pixel_ring.off()
        if key == "8":
            pixel_ring.spin()
        if key == '9':
            pixel_ring.speak()
        if key == '10':
            pixel_ring.think()
        if key == '11':
            self.brightness += 50
            if self.brightness >= 254:
                self.brightness == 254
            pixel_ring.set_brightness(self.brightness)
        if key == '12':
            self.brightness -= 50
            if self.brightness <= 0:
                self.brightness == 0
            pixel_ring.set_brightness(self.brightness)

if __name__ == '__main__':
    my_XML_Analysis = XML_Analysis()
        
