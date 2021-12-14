#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import rospy
from pixel_ring import pixel_ring
from std_msgs.msg import Int32,String

class mic_light_control():
    def __init__(self):
        self.awake_flag, self.asr_flag, self.nlu_flag, self.tts_flag = 0,0,0,0
        self.time = 0
        rospy.init_node('mic_light_control')
        rospy.Subscriber('/voice/castle_awake_topic', Int32 , self.awake_callback)
        rospy.Subscriber('/voice/castle_asr_topic', String , self.asr_callback)
        rospy.Subscriber('/voice/castle_order_topic', String , self.asr_callback)
        rospy.Subscriber('/voice/castle_nlu_topic', String , self.nlu_callback)
        rospy.Subscriber('/voice/castle_tts_topic', Int32 , self.tts_callback)
        pixel_ring.off()

        while not rospy.is_shutdown():
            if self.time >= 0 :
                self.time -= 1
                if self.time <= 0:
                    pixel_ring.off()
                time.sleep(1)
            else:
                time.sleep(1)

    def awake_callback(self,data):
        self.awake_flag = 1
        self.time = 5
        pixel_ring.wakeup()
        time.sleep(1)
        pixel_ring.speak()
        time.sleep(1)
        self.awake_flag = -1

    def asr_callback(self,data):
        self.asr_flag = 1
        self.time = 5
        pixel_ring.think()
        self.asr_flag = -1

    def nlu_callback(self,data):
        self.nlu_flag = 1
        self.time = 5
        self.nlu_flag = -1
        

    def tts_callback(self,data):
        self.tts_flag = 1
        self.time = 15
        pixel_ring.speak()
        time.sleep(1)
        self.tts_flag = -1

mic_light_control()

