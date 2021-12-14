#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
作者:赵家俊
最后修改日期:2019.05.18
'''
 
from xml.dom.minidom import parse
import xml.dom.minidom

import rospy

from math import sin, cos, pi, sqrt
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32, Float32, String

class XML_Analysis():
    def __init__(self):
        rospy.init_node('XML_Analysis', log_level=rospy.INFO)
        #在launch文件中获取参数
        self.file_path = rospy.get_param("~file_path", "/params/c.xml")
        self.speed = rospy.get_param("~speed", 0.5)
        self.pub = rospy.Publisher('/robot0/cmd_vel', Twist, queue_size = 1)
        self.sub = rospy.Subscriber('/voice/castle_xf_cmd_topic', Int32 , self.cmd_callback)
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
        self.want = None
        self.want_id = None
        self.dialpre = None
        self.dialpre_id = None
        self.contact = None
        self.contact_id = None
        self.dialsuf = None
        self.dialsuf_id = None

        self.cmd_flag = False
        self.key_word = None
        self.line_x = 0
        self.line_y = 0
        self.line_z = 0
        self.rotation_z = 0
        self.line_speed_factor = 0.1
        self.rotation_speed_factor = 0.1

        self.moveBindings = {
            'Forward':(1,0,0,0), #前进
            'Backward':(-1,0,0,0), #后退
            'Clockwise':(0,0,0,-1), #顺时针旋转
            'Anticlockwise':(0,0,0,1), #逆时针旋转
            'Left_shift':(0,1,0,0), #左平移
            'Right_shift':(0,-1,0,0), #右平移
            'Stop':(0,0,0,0), #停止
            }
        self.Line_motion = ['Forward','Backward','Left_shift','Right_shift']
        self.Rotational_motion = ['Clockwise','Anticlockwise']

        self.r = rospy.Rate(10)
        try:
            while not rospy.is_shutdown():
                if self.cmd_flag is True:
                    self.analysis_file()
                    self.Process_Speech_cmd_to_Speed()
                    self.cmd_flag = False
                self.r.sleep()
        #except Exception as e:
        #    print(e)
        finally:
            self.twist = Twist()
            self.twist.linear.x = 0
            self.twist.linear.y = 0
            self.twist.linear.z = 0
            self.twist.angular.x = 0
            self.twist.angular.y = 0
            self.twist.angular.z = 0
            self.pub.publish(self.twist)


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
            '''
            try:
                print "focus: ", map(str,focus_data).index('dialpre')
            except ValueError:
                print 'None'
            '''

            self.result_confidence = self.result.getElementsByTagName('confidence')[0]
            self.result_confidence_data = map(int,self.result_confidence.childNodes[0].data.split('|'))
            print "confidence:", self.result_confidence_data

            self.object = self.nlp.getElementsByTagName("object")[0] #获取object节点

            try:
                self.want = self.object.getElementsByTagName('want')[0]
                print "want: %s" % self.want.childNodes[0].data
                if self.want.hasAttribute("id"):
                    self.want_id = int(self.want.getAttribute("id"))
                    print "want id: %s" % self.want.getAttribute("id")
            except IndexError:
                self.want = None
                self.want_id = None
                print 'No want'

            try:
                self.dialpre = self.object.getElementsByTagName('dialpre')[0]
                print "dialpre: %s" % self.dialpre.childNodes[0].data
                if self.dialpre.hasAttribute("id"):
                    self.dialpre_id = int(self.dialpre.getAttribute("id"))
                    print "dialpre id: %s" %  self.dialpre.getAttribute("id")
            except IndexError:
                self.dialpre = None
                self.dialpre_id = None
                print 'No dialpre'

            try:
                self.contact = self.object.getElementsByTagName('contact')[0]
                print "contact: %s" % self.contact.childNodes[0].data
                if self.contact.hasAttribute("id"):
                    self.contact_id = int(self.contact.getAttribute("id"))
                    print "contact id: %s" %  self.contact.getAttribute("id")
            except IndexError:
                print 'No contact'

            try:
                self.dialsuf = self.object.getElementsByTagName('dialsuf')[0]
                print "dialsuf: %s" % self.dialsuf.childNodes[0].data
                if self.dialsuf.hasAttribute("id"):
                    self.dialsuf_id = int(self.dialsuf.getAttribute("id"))
                    print "dialsuf id: %s" %  self.dialsuf.getAttribute("id")
            except IndexError:
                self.dialsuf = None
                self.dialsuf_id = None
                print 'No dialsuf'

            print "解析完成.....\n"

        else:
            print "No XML"

    def cmd_callback(self, req):
        print "命令词识别成功，正在解析命令词结果..."
        self.cmd_flag = True

    def Process_Speech_cmd_to_Speed(self):
        print "文本： ", self.rawtext_data #打印会话结果
        print "可信度： ", self.confidence_data #打印可信度
        if self.confidence_data>=30:
            if self.result_confidence_data[self.focus_data.index('dialpre')]>10 and self.result_confidence_data[self.focus_data.index('contact')]>10:
                print "pass!"
                if self.dialpre_id==4 and self.contact_id==2:
                    self.key_word = 'Stop'
                elif self.contact_id==0:
                    self.key_word = self.Line_motion[self.dialpre_id]
                elif self.contact_id==1:
                    self.key_word = self.Rotational_motion[self.dialpre_id-2]
                else:
                    self.key_word = 'Stop'
                print self.key_word
                self.line_x = self.moveBindings[self.key_word][0] * self.line_speed_factor
                self.line_y = self.moveBindings[self.key_word][1] * self.line_speed_factor
                self.line_z = self.moveBindings[self.key_word][2] * self.line_speed_factor
                self.rotation_z = self.moveBindings[self.key_word][3] * self.rotation_speed_factor
                self.twist = Twist()
                self.twist.linear.x = self.line_x
                self.twist.linear.y = self.line_y
                self.twist.linear.z = self.line_z
                self.twist.angular.x = 0
                self.twist.angular.y = 0
                self.twist.angular.z = self.rotation_z
                self.pub.publish(self.twist)

if __name__ == '__main__':
    my_XML_Analysis = XML_Analysis()
        