#!/usr/bin/python
# -*- coding: UTF-8 -*-
import rospy
from playsound import playsound
import os

from std_msgs.msg import Int32MultiArray, Int32, String

class XML_Analysis():
    def __init__(self):
        self.result, self.action_id, self.grade_id, self.result_confidence_data = None, 0, 0, None
        self.cmd_flag = False
        self.position_id = None
        self.goal_point_msg = None

        #   初始化ROS节点
        rospy.init_node('XML_Analysis', log_level=rospy.INFO)

        #   语音提示文件
        self.voice1 = rospy.get_param("~failed_file_path", "/params/voice/failed.wav")
        self.voice2 = rospy.get_param("~Received_file_path", "/params/voice/Received.mp3")
        self.voice3 = rospy.get_param("~ReEnterAuido_file_path", "/params/voice/ReEnterAuido.mp3")

        #在launch文件中获取参数
        self.sub = rospy.Subscriber('/voice/castle_order_topic', String , self.cmd_callback)  #   订阅离线命令词识别结果话题
        self.pub = rospy.Publisher('/xdu_flag', Int32MultiArray, queue_size = 1)  #   发布离线命令词识别的命令词话题

        # self.r = rospy.Rate(10)
        #   主函数
        while not rospy.is_shutdown():
            rospy.spin()

                
    #   对离线命令词结果进行处理
    def id_data(self, star_data, end_data):
        #   获取识别结果
        str = self.result
        #   对识别结果进行处理
        swap = str[str.rfind(star_data) + 1:str.rfind(end_data)]
        swap = swap[swap.rfind("id=") + 3:swap.rfind(">")]
        #   将字符串转换成整型
        id_data = int(swap.replace('"',''))

        #   对命令词置信度结果进行处理
        swap = str[str.rfind("<confidence>") + 12:str.rfind("</confidence>")]
        #   对结果进行处理
        swap_confidence = swap.replace('|',',')
        swap_confidence = swap_confidence.split(',')
        #   将字符串转换成整型
        if len(swap_confidence) == 3:
            self.result_confidence_data = int(swap_confidence[1])
        else:
            pass
        return id_data

    #   对离线命令词结果进行处理
    def focus_data(self, star_data, end_data):
        #   获取识别结果
        str = self.result
        #   对识别结果进行处理
        swap = str[str.rfind(star_data) + 1:str.rfind(end_data)]
        swap = len(swap)
        return swap

    def cmd_callback(self, data):

        self.result = data.data
        flag = self.focus_data("<focus>", "</focus>")
        # print(flag)
        if flag == 28:
            #   识别消毒等级
            self.grade_id = self.id_data("<grade", "</grade>")
            #   识别是否打开还是关闭消毒功能
            self.action_id = self.id_data("<action", "</action>")
            self.Process_Speech_cmd_to_Speed()
            self.cmd_flag = False
        else:
            pass

    def Process_Speech_cmd_to_Speed(self):
        if (self.position_id == 306):
            print('您输入的信息不完整，请重新输入！')
            playsound(self.voice3)
        else:
            #   判断语音识别的置信度是否达到要求
            if self.result_confidence_data > 40:
                self.goal_point_msg = Int32MultiArray()
                self.goal_point_msg.data = [self.grade_id, self.action_id]
                #   发布命令词识别结果
                self.pub.publish(self.goal_point_msg)
                print('小谷：好的，收到!')
                playsound(self.voice2)
                self.result_confidence_data = 0               
            else:
                print('语音识别未通过，请重新输入！')
                playsound(self.voice1)    

if __name__ == '__main__':
    XML_Analysis()
        
