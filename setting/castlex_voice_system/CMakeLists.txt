cmake_minimum_required(VERSION 2.8.3)
project(castlex_voice_system)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  roslib
)

## System dependencies are found with CMake's conventions
# find_package(Boost REQUIRED COMPONENTS system)


## Uncomment this if the package has a setup.py. This macro ensures
## modules and global scripts declared therein get installed
## See http://ros.org/doc/api/catkin/html/user_guide/setup_dot_py.html
# catkin_python_setup()

################################################
## Declare ROS messages, services and actions ##
################################################

## To declare and build messages, services or actions from within this
## package, follow these steps:
## * Let MSG_DEP_SET be the set of packages whose message types you use in
##   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
## * In the file package.xml:
##   * add a build_depend tag for "message_generation"
##   * add a build_depend and a exec_depend tag for each package in MSG_DEP_SET
##   * If MSG_DEP_SET isn't empty the following dependency has been pulled in
##     but can be declared for certainty nonetheless:
##     * add a exec_depend tag for "message_runtime"
## * In this file (CMakeLists.txt):
##   * add "message_generation" and every package in MSG_DEP_SET to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * add "message_runtime" and every package in MSG_DEP_SET to
##     catkin_package(CATKIN_DEPENDS ...)
##   * uncomment the add_*_files sections below as needed
##     and list every .msg/.srv/.action file to be processed
##   * uncomment the generate_messages entry below
##   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)

## Generate messages in the 'msg' folder
# add_message_files(
#   FILES
#   Message1.msg
#   Message2.msg
# )

## Generate services in the 'srv' folder
# add_service_files(
#   FILES
#   Service1.srv
#   Service2.srv
# )

## Generate actions in the 'action' folder
# add_action_files(
#   FILES
#   Action1.action
#   Action2.action
# )

## Generate added messages and services with any dependencies listed here
# generate_messages(
#   DEPENDENCIES
#   std_msgs
# )

################################################
## Declare ROS dynamic reconfigure parameters ##
################################################

## To declare and build dynamic reconfigure parameters within this
## package, follow these steps:
## * In the file package.xml:
##   * add a build_depend and a exec_depend tag for "dynamic_reconfigure"
## * In this file (CMakeLists.txt):
##   * add "dynamic_reconfigure" to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * uncomment the "generate_dynamic_reconfigure_options" section below
##     and list every .cfg file to be processed

## Generate dynamic reconfigure parameters in the 'cfg' folder
# generate_dynamic_reconfigure_options(
#   cfg/DynReconf1.cfg
#   cfg/DynReconf2.cfg
# )

###################################
## catkin specific configuration ##
###################################
## The catkin_package macro generates cmake config files for your package
## Declare things to be passed to dependent projects
## INCLUDE_DIRS: uncomment this if your package contains header files
## LIBRARIES: libraries you create in this project that dependent projects also need
## CATKIN_DEPENDS: catkin_packages dependent projects also need
## DEPENDS: system dependencies of this project that dependent projects also need
catkin_package(
#  INCLUDE_DIRS include
#  LIBRARIES castlex_voice_system
#  CATKIN_DEPENDS roscpp rospy std_msgs
#  DEPENDS system_lib
)

###########
## Build ##
###########
link_directories(
  lib
  ${catkin_LIB_DIRS}
)

## Specify additional locations of header files
## Your package locations should be listed before other locations
include_directories(
 include
  ${catkin_INCLUDE_DIRS}
)

## Declare a C++ library
# add_library(${PROJECT_NAME}
#   src/${PROJECT_NAME}/castlex_voice_system.cpp
# )

## Add cmake target dependencies of the library
## as an example, code may need to be generated before libraries
## either from message generation or dynamic reconfigure
# add_dependencies(${PROJECT_NAME} ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Declare a C++ executable
## With catkin_make all packages are built within a single CMake context
## The recommended prefix ensures that target names across packages don't collide
# add_executable(${PROJECT_NAME}_node src/castlex_voice_system_node.cpp)

## Rename C++ executable without prefix
## The above recommended prefix causes long target names, the following renames the
## target back to the shorter version for ease of user use
## e.g. "rosrun someones_pkg node" instead of "rosrun someones_pkg someones_pkg_node"
# set_target_properties(${PROJECT_NAME}_node PROPERTIES OUTPUT_NAME node PREFIX "")

## Add cmake target dependencies of the executable
## same as for the library above
# add_dependencies(${PROJECT_NAME}_node ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Specify libraries to link a library or executable target against
# target_link_libraries(${PROJECT_NAME}_node
#   ${catkin_LIBRARIES}
# )

#############
## Install ##
#############

# all install targets should use catkin DESTINATION variables
# See http://ros.org/doc/api/catkin/html/adv_user_guide/variables.html

## Mark executable scripts (Python etc.) for installation
## in contrast to setup.py, you can choose the destination
# install(PROGRAMS
#   scripts/my_python_script
#   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark executables for installation
## See http://docs.ros.org/melodic/api/catkin/html/howto/format1/building_executables.html
# install(TARGETS ${PROJECT_NAME}_node
#   RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark libraries for installation
## See http://docs.ros.org/melodic/api/catkin/html/howto/format1/building_libraries.html
# install(TARGETS ${PROJECT_NAME}
#   ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   RUNTIME DESTINATION ${CATKIN_GLOBAL_BIN_DESTINATION}
# )

## Mark cpp header files for installation
# install(DIRECTORY include/${PROJECT_NAME}/
#   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
#   FILES_MATCHING PATTERN "*.h"
#   PATTERN ".svn" EXCLUDE
# )

## Mark other files for installation (e.g. launch and bag files, etc.)
# install(FILES
#   # myfile1
#   # myfile2
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
# )

#############
## Testing ##
#############

## Add gtest based cpp test target and link libraries
# catkin_add_gtest(${PROJECT_NAME}-test test/test_castlex_voice_system.cpp)
# if(TARGET ${PROJECT_NAME}-test)
#   target_link_libraries(${PROJECT_NAME}-test ${PROJECT_NAME})
# endif()

## Add folders to be run by python nosetests
# catkin_add_nosetests(test)


add_executable(castle_tts_node src/tts/castle_tts_node.cpp)
target_link_libraries(castle_tts_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lmsc)

add_executable(castle_nlu_node src/nlu/castle_nlu_node.cpp)
target_link_libraries(castle_nlu_node ${catkin_LIBRARIES} -ljsoncpp -lcurl)

add_executable(castle_asr_node src/asr/castle_asr_node.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
target_link_libraries(castle_asr_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)

#add_executable(castle_object_order_node src/order/object_order.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castle_object_order_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)

##################  voice_order   ########################
#add_executable(castle_order_node src/order/castle_order.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castle_order_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)


##################  voice_nav   ########################
#add_executable(voice_nav_order_node src/order/voice_nav_order.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(voice_nav_order_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)


##################  castle_auto   ########################
#add_executable(castlex_auto_order_node src/order/castlex_auto_order.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castlex_auto_order_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)


##################  castle_cmd   ########################
#add_executable(castle_cmd_node src/order/castle_cmd.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castle_cmd_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)
##################  castle_turtlesim_cmd   ########################
#add_executable(castle_turtlesim_cmd_node src/order/castle_turtlesim_cmd.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castle_turtlesim_cmd_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)
##################  castle_mic_cmd   ########################
#add_executable(castle_mic_cmd_node src/order/castle_mic_cmd.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castle_mic_cmd_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)

##################  robot_xdu   ########################
#add_executable(castlex_xdu_node src/order/castlex_xdu_oder.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castlex_xdu_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)

##################  ultraviolet_order   ########################
#add_executable(castlex_zwai_node src/order/castlex_zwai_oder.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(castlex_zwai_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)

##################  castlex_iot_order   ########################
#add_executable(iot_order_node src/order/voice_iot_order.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(iot_order_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)

##################  commen_order_order   ########################
#add_executable(commen_order_node src/order/castlex_com.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
#target_link_libraries(commen_order_node ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)


##################  castle_awake   ########################
add_executable(castle_awake_node src/awake/castle_awake_node.cpp src/linuxrec.cpp src/speech_recognizer.cpp)
target_link_libraries(castle_awake_node ${catkin_LIBRARIES} -lmsc -lrt -ldl -lpthread -lasound)

add_executable(offline_command_word src/order/offline_command_word.cpp src/speech_recognizer.cpp src/linuxrec.cpp)
target_link_libraries(offline_command_word ${catkin_LIBRARIES} -lrt -ldl -lpthread -lasound -lmsc)



install(DIRECTORY include/${PROJECT_NAME}/
    DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
)

install(TARGETS castle_tts_node castle_nlu_node castle_asr_node castle_awake_node   offline_command_word
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

 install(FILES
 launch/castlex_asr.launch
 launch/castlex_awake.launch
 launch/castlex_nlu.launch
 launch/castlex_tts.launch
 launch/castlex_voice_system.launch
 launch/offline_command.launch
   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
 )

install(PROGRAMS
  scripts/castle_cmd.py
  scripts/castle_mic_cmd.py
  scripts/castle_turtlesim_cmd.py
  scripts/castlex_auto.py
  scripts/castlex_auto_cmd.py
  scripts/castlex_multiword.py
  scripts/mic_awake.py
  scripts/mic_light_control.py
  scripts/nlu_kb_gui.py
  scripts/nlu_md.py
  scripts/object_detect.py
  scripts/robot_xdu.py
  scripts/voice_cmd_word_understanding.py
  scripts/voice_nav.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION} )







