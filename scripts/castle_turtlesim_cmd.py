#!/usr/bin/python
# -*- coding: UTF-8 -*-

from xml.dom.minidom import parse
import xml.dom.minidom
import rospy
from random import random

from math import sin, cos, pi, sqrt
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32, Float32, String, Int32MultiArray
from turtlesim.srv import Spawn,Kill 

#from aip import AipSpeech
from playsound import playsound
import os

class XML_Analysis():
    def __init__(self):
        rospy.init_node('XML_Analysis', log_level=rospy.INFO)
        #在launch文件中获取参数
        self.i = 1
        self.j = 0

        self.topic = rospy.get_param("~topic", "/turtle1/cmd_vel")
        self.file_path = rospy.get_param("~file_path", "/params/castle_turtlesim_cmd.xml")
        self.time = rospy.get_param("~time", "2")
        speed = rospy.get_param("~speed", "0.5")
        turn = rospy.get_param("~turn", "0.5")
        self.Conf = rospy.get_param("~Confidence", "30")
        self.x,self.y,self.th = speed,speed,turn
        self.sub = rospy.Subscriber('/voice/castle_order_topic', String , self.cmd_callback)
        self.cmd_vel_pub = rospy.Publisher(self.topic, Twist, queue_size = 1)     #发布速度话题
        rospy.wait_for_service('spawn')
        rospy.wait_for_service('kill')

        self.spawn_srv = rospy.ServiceProxy('spawn',Spawn)
        self.kill_srv = rospy.ServiceProxy('kill',Kill)

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

        self.moveBindings = {
            '0': (1, 0, 0),
            '1': (-1, 0, 0),
            '2': (0, 0, 1),
            '3': (0, 0, -1),
            '4': (0, 0, 0),
            '5': (0,0,0),
            '6': (0,0,0),
            '7':(0,0,0),
            '8':(0,0,0),
        }

        self.speedBindings = {
            '5': (0.5, 0.5),
            '6': (1.5, 1.5)
        }

        self.cmd_flag = False

        self.voice1 = rospy.get_param("~failed_file_path", "/params/voice/failed.mp3")
        self.voice2 = rospy.get_param("~Received_file_path", "/params/voice/Received.mp3")
        self.voice3 = rospy.get_param("~ReEnterAuido_file_path", "/params/voice/ReEnterAuido.mp3")

        self.r = rospy.Rate(10)
        print("唤醒机器人后，可以说‘前进’、‘后退’、‘左转’、‘右转’以控制小海龟")
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
            if self.result_confidence_data[self.focus_data.index('commands')]>self.Conf:
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
        cmd_vel = Twist()
        self.turtles=['turtle1','turtle2','turtle3','turtle4','turtle5','turtle6','turtle7','turtle8','turtle9','turtle10']
        rate = rospy.Rate(10)
        key = str(self.command_id)
        if key in self.moveBindings.keys():
            x = self.x * self.moveBindings[key][0]
            y = self.y * self.moveBindings[key][1]
            th = self.th * self.moveBindings[key][2]

        if key in self.speedBindings.keys():
            self.x = self.x * self.speedBindings[key][0]
            self.y = self.x
            self.th = self.th * self.speedBindings[key][1]
        if key == '7':
            if self.i >10:
                print("已达最大数量")
            else:
                print(10*random(),10*random(),10*random(),str(self.turtles[self.i]))
                res = self.spawn_srv(10*random(),10*random(),10*random(),str(self.turtles[self.i]))
                print('新增一只小海龟%s' % self.turtles[self.i])
                self.i +=1

        if key == '8':
            if self.j >= self.i:
                print("没有小海龟啦！")
            else:
                res = self.kill_srv(str(self.turtles[self.j]))
                print('杀死一只小海龟%s' % self.turtles[self.j])
                self.j += 1

        cmd_vel.linear.x = x
        cmd_vel.linear.y = y
        cmd_vel.angular.z = th
        print("x:{},y={},th={}".format(self.x,self.y,self.th))
        print("cmd_vel.linear.x:{},cmd_vel.linear.y={},cmd_vel.angular.z={}".format(cmd_vel.linear.x,cmd_vel.linear.y,cmd_vel.angular.z))
        print("time = {}s".format(self.time))
        time = self.time * 10
        while time > 0 :
            self.cmd_vel_pub.publish(cmd_vel)
            time -= 1
            rate.sleep()
        time = self.time * 10

if __name__ == '__main__':
    my_XML_Analysis = XML_Analysis()
        
