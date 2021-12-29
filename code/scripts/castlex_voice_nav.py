#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from castlex_voice_nav_python import NAV_XML_Analysis

if __name__ == '__main__':
  try:
    NAV_XML_Analysis()
  except SerialException:
    rospy.logerr("Serial exception trying to open port.")
    os._exit(0)
