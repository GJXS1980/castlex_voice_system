#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import rospy
from std_msgs.msg import String
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
class get_data():
    def __init__(self):
        self.pub_data=rospy.Publisher('voice_data',String,queue_size=1000)
        rospy.init_node('listener', anonymous=True)
        rospy.Subscriber("voice/castlex_asr_topic", String, self.callback)
        rospy.spin()
    def callback(self,data):
        if data.data:
            rospy.loginfo(rospy.get_caller_id() + "I heard %s", data.data)
            p1=data.data
            rospy.loginfo("data:%s",p1)

            #   截取input=后面所有字符
            swap =  re.findall('(?<=input=).*$', p1)
            #   从截取字符list中提取内容
            swap = swap[0]
            s=swap.encode("utf-8").decode("utf-8")
            rospy.loginfo(s)
            output = String()
	    output.data = s
            self.pub_data.publish(output)
    
if __name__ == '__main__':
    while True:
        get_data()
