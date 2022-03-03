#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from castlex_iot_code import IOT_XML_Analysis

if __name__ == '__main__':
  try:
    IOT_XML_Analysis()
  except SerialException:
    os._exit(0)
