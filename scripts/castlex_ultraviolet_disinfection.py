#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from castlex_ultraviolet_disinfection_python import ULTRAVIOLET_XML_Analysis

if __name__ == '__main__':
  try:
    ULTRAVIOLET_XML_Analysis()
  except rospy.ROSInterruptException:
    rospy.loginfo("ultraviolet failed.")
