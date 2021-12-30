#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from castlex_iot_python import IOT_XML_Analysis

if __name__ == '__main__':
  try:
    IOT_XML_Analysis()
  except rospy.ROSInterruptException:
    rospy.loginfo("iot failed.")
