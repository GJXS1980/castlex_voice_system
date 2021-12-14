/*
* 语音听写(iFly Auto Transform)技术能够实时地将语音转换成对应的文字。
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "qisr.h"
#include "msp_cmn.h"
#include "msp_errors.h"
#include "speech_recognizer.h"

#include "ros/ros.h"
#include "std_msgs/Int32.h"
#include "std_msgs/String.h"

#include <sys/time.h>

using namespace std;

#define FRAME_LEN	640 
#define	BUFFER_SIZE	4096
#define ASRCMD 1
bool asr_flag = false;
bool record_flag = true;
bool awake_flag = false;
bool tts_fininsh_flag = true;
string result = "";
string appid;    //用于获取launch传递函数
string speech_param;

//该函数功能是当asr有文本返回时，将文本打印出来，因此适合作为asr动作的标志
static void show_result(char *str, char is_over)
{
	printf("\rResult: [ %s ]", str);
	if(is_over)
		putchar('\n');
	string s(str);
	result = s;
	asr_flag = true;
}

static char *g_result = NULL;
static unsigned int g_buffersize = BUFFER_SIZE;

void on_result(const char *result, char is_last)
{
	if (result) {
		size_t left = g_buffersize - 1 - strlen(g_result);
		size_t size = strlen(result);
		if (left < size) {
			g_result = (char*)realloc(g_result, g_buffersize + BUFFER_SIZE);
			if (g_result)
				g_buffersize += BUFFER_SIZE;
			else {
				printf("mem alloc failed\n");
				return;
			}
		}
		strncat(g_result, result, size);
		show_result(g_result, is_last);
	}
}
void on_speech_begin()
{
	if (g_result)
	{
		free(g_result);
	}
	g_result = (char*)malloc(BUFFER_SIZE);
	g_buffersize = BUFFER_SIZE;
	memset(g_result, 0, g_buffersize);

	printf("Start Listening...\n");
}
void on_speech_end(int reason)
{
	if (reason == END_REASON_VAD_DETECT)
	{
		printf("\nSpeaking done \n");
		record_flag = false; //检测到VAD
	}
	else
		printf("\nRecognizer error %d\n", reason);
}

/* demo recognize the audio from microphone */
static void demo_mic(const char* session_begin_params)
{
	int errcode;
	int i = 0;

	struct speech_rec iat;

	struct speech_rec_notifier recnotifier = {
		on_result,
		on_speech_begin,
		on_speech_end
	};

	errcode = sr_init(&iat, session_begin_params, SR_MIC, &recnotifier);
	if (errcode) {
		printf("speech recognizer init failed\n");
		return;
	}
	errcode = sr_start_listening(&iat);
	if (errcode) {
		printf("start listen failed %d\n", errcode);
	}
	/* demo 15 seconds recording */
	while(record_flag && i<=15)
	{
		sleep(1);
		i++;
	}
	record_flag = true; //复位VAD标志位，否则下次不能打开录音
	errcode = sr_stop_listening(&iat);
	if (errcode) {
		printf("stop listening failed %d\n", errcode);
	}

	sr_uninit(&iat);
}

//语音识别主功能函数
void asr_Process()
{
	int ret = MSP_SUCCESS;
	//int upload_on =	1; /* whether upload the user word */
	/* login params, please do keep the appid correct */
	//const char* appid;
	//ros:params::get("~appid", appid);
	const char* login_params = appid.data();//"appid = 5b6d44ed, work_dir = .";
	//int aud_src = 0; /* from mic or file */

	/*
	* See "iFlytek MSC Reference Manual"
	*/
	const char* session_begin_params = speech_param.data();
	/*
		"sub = iat, domain = iat, language = zh_cn, "
		"accent = mandarin, sample_rate = 16000, "
		"result_type = plain, result_encoding = utf8";
	*/

	/* Login first. the 1st arg is username, the 2nd arg is password
	 * just set them as NULL. the 3rd arg is login paramertes 
	 * */
	ret = MSPLogin(NULL, NULL, login_params);    //登录
	if (MSP_SUCCESS != ret)	{
		printf("MSPLogin failed , Error code %d.\n",ret);
		goto exit; // login fail, exit the program
	}

		demo_mic(session_begin_params);

exit:
	MSPLogout(); // Logout...

}

void asrCallback(const std_msgs::Int32::ConstPtr& msg)
{
	ROS_INFO_STREAM("you are speaking...");
	if(msg->data == ASRCMD)
	{
		awake_flag = true;
		//asr_Process();
	}
}

//用于确认tts是否在播放音频，避免录音与播放冲突
void ttsCallback(const std_msgs::Int32::ConstPtr& msg)
{
	//ROS_INFO_STREAM("you can speaking...");
	if(msg->data == 1)
	{
		tts_fininsh_flag = true; //开放语音识别功能
		printf("hello1\n");
	}
	else if(msg->data == 0)
	{
		tts_fininsh_flag = false; //关闭语音识别功能
		printf("hi0\n");
	}
}


/* main thread: start/stop record ; query the result of recgonization.
 * record thread: record callback(data write)
 * helper thread: ui(keystroke detection)
 */
int main(int argc, char** argv)
{

	ros::init(argc, argv, "castlex_asr_node");    //初始化节点，向节点管理器注册
	ros::NodeHandle n;
	ros::Subscriber sub = n.subscribe("/voice/castlex_awake_topic", 1, asrCallback);	//	订阅语音唤醒话题
	//ros::Subscriber sub_tts = n.subscribe("/voice/castlex_xiaogu_tts_topic", 1, ttsCallback);	//	订阅语音合成话题

	ros::NodeHandle nh("~");    //用于launch文件传递参数
	nh.param("appid", appid, std::string("appid = 551d49a3, work_dir = ."));    //从launch文件获取参数
	nh.param("speech_param", speech_param, std::string("sub = iat, domain = iat, language = zh_cn, accent = mandarin, sample_rate = 16000, result_type = plain, result_encoding = utf8"));
	//printf("%s\n", appid);    //不支持UTF-8，因此终端打印出来是乱码

	ros::Publisher pub = n.advertise<std_msgs::String>("/voice/castlex_asr_topic", 3);	//	发布语音识别话题

	ros::Rate loop_rate(10);    //10Hz循环周期
	while(ros::ok())
	{
		if(awake_flag)
		{
			asr_Process();
			awake_flag = false;
			if(asr_flag)
			{
				std_msgs::String msg;
				msg.data = result;    //将asr返回文本写入消息，发布到topic上
				pub.publish(msg);
				asr_flag = false;
				record_flag = true;
			}
			//tts_fininsh_flag = false; //关闭语音识别标志，等待音频播放结束
			//while(!tts_fininsh_flag); //等待TTS传输播放完成的指令，如果没有东西播放怎么办？意味着没有语音识别结果返回
		}
		loop_rate.sleep();
		ros::spinOnce();
	}

	return 0;
}


