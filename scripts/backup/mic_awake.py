#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import rospy
from pixel_ring import pixel_ring
from std_msgs.msg import Int32,String

def awake_callback(data):
    if light_effect !="None":
        
        if light_effect == 'speak':
            pixel_ring.speak()
        elif light_effect == "listen":
            pixel_ring.listen()
        elif light_effect == 'think':
            pixel_ring.think()
        elif light_effect == 'spin':
            pixel_ring.spin()
    else:
        pixel_ring.set_color(r=r,g=g,b=b)


effect_dict = {'None':'off','speak':'pixel_ring.speak','listen':'pixel_ring.listen','think':'pixel_ring.think','spin':'pixel_ring.spin'}

rospy.init_node('mic_light_control')
rospy.Subscriber('/voice/castle_awake_topic', Int32 , awake_callback)
light_effect = rospy.get_param("~/light_effect","speak")
r = int(rospy.get_param("~/color_r","0"))
g = int(rospy.get_param("~/color_g","0"))
b = int(rospy.get_param("~/color_b","200"))
brightness = int(rospy.get_param("~/brightness",'255'))
pixel_ring.set_brightness(brightness)
pixel_ring.off()

rospy.spin()


