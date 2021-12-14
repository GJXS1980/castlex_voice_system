#!/usr/bin/python
# -*- coding: UTF-8 -*-
import rospy

class XML_Analysis():
    def __init__(self):
        # 十进制转成二进制
        self.result = bin(7)
        # 二进制转成十进制
        self.int_data = int(self.result, 2)
        data = self.result.split()
        

    def stc_replace_(self, data, ):
        # 十进制转成二进制
        self.result = bin(7)
        # 二进制转成十进制
        self.int_data = int(self.result, 2)
        print(self.result, self.int_data)
        

if __name__ == '__main__':
    XML_Analysis()
        
