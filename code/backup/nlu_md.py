#! /usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import roslaunch 
import threading
import os
import sys
import actionlib
from Tkinter import *
from tkFileDialog import *
from tkMessageBox import *
from tkSimpleDialog import *
import ttk
from actionlib import *
from geometry_msgs.msg import Pose, Point, Quaternion, Twist, PoseStamped
from move_base_msgs.msg import MoveBaseGoal, MoveBaseAction



class SaveWayPoint:
    def __init__(self):
        self.root = Tk()
        
        self.root.title("waypoint setting")
        self.root.geometry('800x470')
        self.waypoints = []
        self.seq_1 = "A"
        self.seq_2 = 1
        self.i = 0
        self.modify_flag = 0
        self.name_flag = 0
        self.seq_list = []
        init_filepath = str(os.popen('rospack find castlex_navigation').read())[:-1]
        filepath = init_filepath + '/waypoints'

        self.save_node()
        
        if os.path.exists(filepath):       #如果filepath存在，路径改为filepath；否则创建一个waypoint文件夹
            os.chdir(filepath)
        else: 
            os.mkdir(filepath)
            os.chdir(filepath)

        try:                               #如果设置了环境变量‘NEW_MAP’，文件名改为‘NEW_MAP'-waypoints,否则为default-waypoints
            name = os.environ['NEW_MAP']
            self.filename = name + '.waypoint'
        except KeyError:
            self.name_flag = 1

        columns = ('number','linear_x','linear_y','linear_z','orientation_x','orientation_y','orientation_z','orientation_w')
        self.treeview = ttk.Treeview(self.root,height=18,show="headings",columns=columns)
        
        for i in range(len(columns)):      #做表头
            if i:
                self.treeview.column(columns[i],width=100,anchor='center')
            else:
                self.treeview.column(columns[i],width=50,anchor='center')
            self.treeview.heading(columns[i], text=columns[i])
            i +=1
        self.treeview.pack()      

       

        # 定义按钮
        Button(self.root,text='保存',command=self.save_point).pack(side='left',anchor='nw',fill='both')   
    
        Button(self.root,text='退出',command=self.shutdown).pack(side='right',anchor='e',fill='both')
        Button(self.root,text='打开文件',command=self.open).pack(side='left',anchor='n',fill="both")
        Button(self.root,text='路点测试',command=self.sent_point).pack(side='top',anchor='n',fill="both")
        Button(self.root,text='删除',command=self.delete).pack(side='top',anchor='s',fill="both")
        Button(self.root,text='清空条目',command=self.del_all).pack(side='top',anchor='s',fill='both')

        self.treeview.bind('<ButtonRelease-1>', self.select)  #左键单击
        self.treeview.bind('<Double-1>', self.edit)  #左键双击
        self.treeview.bind('<Control-s>',self.save_point_event)   #ctrl+s
        self.treeview.bind('<Control-d>',self.del_all_event)    #ctrl+d
        self.treeview.bind('<BackSpace>',self.delete_event)   #backspace

        self.root.mainloop()


                          #########     修改表格数据     ###########
    
    def edit(self,event):
        self.modify_flag = 1
        self.item = self.treeview.selection()
        column = self.treeview.identify_column(event.x)
        row =  self.treeview.identify_row(event.y)
        cn = int(str(column).replace('#',''),16)
        rn = int(str(row).replace('I',""),16)
        self.rn = rn - 1 
        self.entryedit = Text(self.root,width=15,height=1)              #在鼠标坐标位置生成一个输入框
        self.entryedit.place(x=event.x, y=event.y)
        
        def saveedit():                                                 #点击输入框旁边的OK保存你的输入，并关闭输入框
            get_text = self.entryedit.get(0.0,END).encode('utf-8')
            self.treeview.set(self.item,column=column,value=get_text[0:-1])
            self.waypoint = list(self.treeview.item(self.item,"values"))
            print(self.waypoint)
            self.entryedit.destroy()
            self.ok_button.destroy()
        self.ok_button = Button(self.root,text='OK',width=4,command=saveedit)
        self.ok_button.place(x=event.x + 100,y=event.y)        
 
                           #########     选中条目     ###########

    def select(self, event):                                            
        column = self.treeview.identify_column(event.x)
        row = self.treeview.identify_row(event.y)
        try:
            cn = int(str(column).replace('#',''),16)
            rn = int(str(row).replace('I',""),16)
            self.rn = rn - 1

            childrens = self.treeview.get_children()
            self.select_item = childrens[self.rn]
            self.item = self.treeview.selection()
            self.waypoint = list(self.treeview.item(self.item,"values"))
            print(self.waypoint)
        except :
            try:                                                              #点击空白区域自动删除输入框和OK键
                get_text = self.entryedit.get(0.0,END).encode('utf-8')
                self.treeview.set(self.item,column=column,value=get_text[0:-2])
                self.entryedit.destroy()
                self.ok_button.destroy()
            except: pass

                        #########     快捷键保存     ###########

    def save_point_event(self,event):
        self.save_point()
    
                        #########     快捷键删除     ###########
   
    def delete_event(self,event):
        self.delete()

                        #########     快捷键删除全部     ###########
   
    def del_all_event(self,event):
        self.del_all()


                          #########     启动节点     ###########

    def save_node(self):                  #启动节点，订阅move_base_simple/goal话题
        rospy.init_node("save_waypoint", anonymous=False)
        rospy.loginfo("Node is created!")
        rospy.Subscriber("/move_base_simple/goal", PoseStamped, self.goal_callback, queue_size=1)



                          #########     发布目标点     ###########

    def sent_point(self):
        self.goalpoint = []
        self.goalpoint.append(Pose(Point(float(self.waypoint[1]),float(self.waypoint[2]),float(self.waypoint[3])),Quaternion(float(self.waypoint[4]),float(self.waypoint[5]),float(self.waypoint[6]),float(self.waypoint[7]))))
        self.move_base = actionlib.SimpleActionClient("move_base",MoveBaseAction)
        self.move_base.wait_for_server(rospy.Duration(5))
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = 'map'
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose = self.goalpoint[0]
        self.move_base.send_goal(goal)                       #不等待move_base的返回值，否则会卡住
        
                          #########     回调函数     ###########

    def goal_callback(self, data):        #接收到目标点后执行回调函数
        #try:                              #取消机器人导航
        #    self.move_base.cancel_goal()
        #except:
        #    pass
        self.seq = self.seq_1 + str(self.seq_2)                    #编号由字母+数字组成
        self.modify_flag = 1
        t_root = Tk()
        t_root.withdraw()
        if askyesno('Verify', '是否保存该目标点?'):              #询问是否保存
            while not rospy.is_shutdown():
                self.seq = askstring(parent=t_root,title="waypoint", prompt="请输入目标点编号:",initialvalue=self.seq)
                if self.seq[0] != self.seq_1:                     #统一为大写
                    self.seq_1 = self.seq[0].upper()
                    self.seq_2 = 1
                    self.seq = self.seq_1 + str(self.seq_2)
                else: pass
                if self.seq in self.seq_list:
                    showerror('错误','编号重复！！！')
                    
                    self.seq_1 = self.seq_list[-1][0]                          #编号的字母不变，数字增加
                    self.seq_2 = int(self.seq_list[-1][1]) + 1
                    self.seq = self.seq_1 + str(self.seq_2)
                else:
                    self.seq_list.append(self.seq)
                    point = [str(self.seq),data.pose.position.x,data.pose.position.y,
                        data.pose.position.z, data.pose.orientation.x, data.pose.orientation.y, data.pose.orientation.z, data.pose.orientation.w]
                    self.seq_1 = self.seq[0]                          #编号的字母不变，数字增加
                    self.seq_2 += 1
                    self.waypoints.append(point)
                    self.treeview.insert('',self.i,values=point)      #新数据插入到列表中
                    self.i += 1    

                    break
            t_root.destroy()
                


                           #########     保存     ###########

    def save_point(self):
        if self.name_flag:  #如果没有设置'NEW_MAP',则询问是否修改名称
            filename = asksaveasfilename(title="保存文件",filetypes=[("文件",'*.waypoint')],initialdir="default")
            self.filename = filename
            self.name_flag = 0
        else:
            pass 
        f = open(self.filename, 'w')
        self.waypoints = []
        for item in self.treeview.get_children():
            item_data = self.treeview.item(item,"values")
            self.waypoints.append(item_data)
        for i in range(len(self.waypoints)):
            for j in range(len(self.waypoints[i])):
                f.write(str(self.waypoints[i][j]) + ' ')
            f.write('\n')
        f.close()
        self.modify_flag = 0
        print(self.filename + ' ' + 'has been created!')  



                          #########     打开文件     ###########

    def open(self):                      #打开waypoint文件
        point_file = askopenfilename(title="选择waypoint文件",filetypes=[("文件",'*.waypoint')])
        self.filename = point_file
        self.del_all()                   #删除
        self.waypoints = []
        f = open(point_file,'r')
        waypoints = f.readlines()
        for i in range(len(waypoints)):
            waypoint = waypoints[i].split(' ')[:-1]
            self.treeview.insert('',i,values=waypoint)
            self.waypoints.append(waypoint)


                          #########     安全退出     ###########

    def shutdown(self):                #安全退出
        rospy.loginfo("Stopping the program...")
        try:                           #取消机器人导航
            self.move_base.cancel_goal()
        except:
            pass
        if self.modify_flag:           #如果执行过修改，则询问是否进行保存
            if askyesno('Verify','文件未保存，是否保存？'):
                self.save_point()
            else:
                pass
        else:
            pass
        rospy.sleep(0.5)
        os._exit(99)
        

                          #########     删除单个条目     ###########

    def delete(self):                      #删除按钮
        self.modify_flag = 1
        childrens = self.treeview.get_children()
        self.treeview.delete(childrens[self.rn])

                          #########     清空条目     ###########

    def del_all(self):                 #清空条目
        self.modify_flag = 1
        x = self.treeview.get_children()
        for item in x:
            self.treeview.delete(item)



if __name__ == '__main__':
    newpid = os.fork()
    def launch_rosmaster():
        try:                             #检测是否有启动rosmaster，未启动则自动启动rosmaster
            sorted(rospy.get_master())
        except:
            roslaunch.main(['roscore','--core'] + sys.argv[1:])
    if newpid:
        SaveWayPoint()
    else:
        launch_rosmaster()
    
    