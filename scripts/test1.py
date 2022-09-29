#!/usr/bin/env python
# -*- coding:utf-8 -*-
import rospy
from std_msgs.msg import String
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

 
def callback(data):

    s=data.data.encode("utf-8").decode("utf-8")
    print(s)

 
def listener():
 
    rospy.init_node('listener', anonymous=True)
    rospy.Subscriber("voice_data", String, callback)
    rospy.spin()
if __name__ == '__main__':
    listener()

