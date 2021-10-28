#!/usr/bin/python
# -*- coding: UTF-8 -*-
import rospy
from playsound import playsound
import os

from std_msgs.msg import Int32MultiArray, Int32, String

class XML_Analysis():
    def __init__(self):
        self.result, self.start_id, self.block_id, self.terminal_id = None, None, None, None
        self.cmd_flag = False
        self.position_id = None
        self.goal_point_msg = None
        self.start_confidence_data, self.start_confidence_data, self.start_confidence_data = None, None, None

        #   初始化ROS节点
        rospy.init_node('XML_Analysis', log_level=rospy.INFO)

        #   语音提示文件
        self.voice1 = rospy.get_param("~failed_file_path", "/params/voice/failed.mp3")
        self.voice2 = rospy.get_param("~Received_file_path", "/params/voice/Received.mp3")
        self.voice3 = rospy.get_param("~ReEnterAuido_file_path", "/params/voice/ReEnterAuido.mp3")

        #在launch文件中获取参数
        self.sub = rospy.Subscriber('/voice/castlex_xiaogu_ocw_topic', String , self.cmd_callback)  #   订阅离线命令词识别结果话题
        self.pub = rospy.Publisher('/voice/goal_point', Int32MultiArray, queue_size = 1)  #   发布离线命令词识别的命令词话题

        # self.r = rospy.Rate(10)
        #   主函数
        while not rospy.is_shutdown():
            rospy.spin()
            
            # self.r.sleep()

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
        if len(swap_confidence) == 6:
            self.start_confidence_data = int(swap_confidence[1])
            self.block_confidence_data = int(swap_confidence[3])
            self.terminal_confidence_data = int(swap_confidence[5])
        else:
            pass
        return id_data

    def cmd_callback(self, data):
        self.result = data.data
        print(self.result)
        #   识别地点
        self.start_id = self.id_data("<start", "</start>")
        #   识别颜色物体
        self.block_id = self.id_data("<block", "</block>")
        #   识别目标地点
        self.terminal_id = self.id_data("<terminal", "</terminal>")

        # self.analysis_confidence()
        self.Process_Speech_cmd_to_Speed()


    def Process_Speech_cmd_to_Speed(self):
        if (self.position_id == 306):
            print '您输入的信息不完整，请重新输入！'
            playsound(self.voice3)
        else:
            #   判断语音识别的置信度是否达到要求
            if (self.start_confidence_data > 40) and (self.start_confidence_data > 40) and (self.start_confidence_data > 40):
                self.goal_point_msg = Int32MultiArray()
                self.goal_point_msg.data = [self.start_id, self.block_id, self.terminal_id]
                #   发布命令词识别结果
                self.pub.publish(self.goal_point_msg)
                print '小谷：好的，收到!'
                playsound(self.voice2)
                self.start_confidence_data, self.start_confidence_data, self.start_confidence_data = 0, 0, 0         
            else:
                print '语音识别未通过，请重新输入！'
                playsound(self.voice1)    

if __name__ == '__main__':
    XML_Analysis()
        
