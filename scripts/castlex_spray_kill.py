#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from castlex_spray_kill_python import SPRAY_XML_Analysis

if __name__ == '__main__':
  try:
    SPRAY_XML_Analysis()
  except SerialException:
    os._exit(0)
