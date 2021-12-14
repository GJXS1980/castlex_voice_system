#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <typeinfo>
#include <errno.h> 
#include "qisr.h"
#include "msp_cmn.h"
#include "msp_errors.h"
#include "linuxrec.h"
#include "speech_recognizer.h"

#include "msp_cmn.h"
#include "qivw.h"
#include "msp_errors.h"

#include "ros/ros.h"
#include "std_msgs/Int32.h"

#include "ros/package.h"

using namespace std;

// #define IVW_AUDIO_FILE_NAME "./bin/audio/awake.wav"
#define FRAME_LEN	640 //16k采样率的16bit音频，一帧的大小为640B, 时长20ms

#define E_SR_NOACTIVEDEVICE		1
#define E_SR_NOMEM				2
#define E_SR_INVAL				3
#define E_SR_RECORDFAIL			4
#define E_SR_ALREADY			5

#define DEFAULT_FORMAT		\
{\
	WAVE_FORMAT_PCM,	\
	1,			\
	16000,			\
	32000,			\
	2,			\
	16,			\
	sizeof(WAVEFORMATEX)	\
}

static int record_state = MSP_AUDIO_SAMPLE_CONTINUE;
struct recorder *recorder;
static bool g_is_awaken_succeed = false;
static bool normal_state_flag = true;

string my_lgi_param;
string my_ssb_param;
string my_response;
string response;
string audio_file_path;
string ssb_param_path;

void sleep_ms(int ms)
{
	usleep(ms * 1000);
}
ros::Publisher score_pub;
/* 录音的回调函数 */
static void iat_cb(char *data, unsigned long len, void *user_para)
{
	if(!ros::ok())
	{
		normal_state_flag = false;
	}
	int errcode;
	const char *session_id = (const char *)user_para;

	if(len == 0 || data == NULL)
		return;
	//如果录音成功，则写入语音唤醒缓冲区
	if(!g_is_awaken_succeed){
		errcode = QIVWAudioWrite(session_id, (const void *)data, len, record_state);
	}
	//写入语音唤醒缓冲区成功，否则将关闭录音
	if (MSP_SUCCESS != errcode)
	{
		printf("QIVWAudioWrite failed! error code:%d\n",errcode);
		int ret = stop_record(recorder);
		if (ret != 0) {
			printf("Stop failed! \n");
			//return -E_SR_RECORDFAIL;
		}
		//等待录音结束
		wait_for_rec_stop(recorder, (unsigned int)-1);
		QIVWAudioWrite(session_id, NULL, 0, MSP_AUDIO_SAMPLE_LAST);//写入最后一块音频
		record_state = MSP_AUDIO_SAMPLE_LAST;
		g_is_awaken_succeed = false;
	}
	//如果写入音频为第一块，则改变标志位
	if(record_state == MSP_AUDIO_SAMPLE_FIRST){
		record_state = MSP_AUDIO_SAMPLE_CONTINUE;
	}
}

//语音唤醒回调函数，当检测到关键词时进入该函数
int cb_ivw_msg_proc( const char *sessionID, int msg, int param1, int param2, const void *info, void *userData )
{
	if(!ros::ok())
	{
		normal_state_flag = false;
	}
	if (MSP_IVW_MSG_ERROR == msg) //唤醒出错消息
	{
		printf("\n\nMSP_IVW_MSG_ERROR errCode = %d\n\n", param1);
		g_is_awaken_succeed = false;
    	record_state = MSP_AUDIO_SAMPLE_LAST;
	}
	else if (MSP_IVW_MSG_WAKEUP == msg) //唤醒成功消息
	{
		printf("\n\nMSP_IVW_MSG_WAKEUP result = %s\n\n", info);
		
		short i = 0;
		char buff[200]={0};
		strcpy(buff,(char*)info);
		char *p=NULL;
		p = strtok(buff,",");

		while(p != NULL)
		{
			i++;
			p = strtok(NULL,",");

			if(i==2) 
			{   p = strtok(p,":");
			 p = strtok(NULL,",");
				break;}

		}
			printf("\n\p result = %s\n\n", p);
        int ia= atoi(p);
		std_msgs::Int32 score;
		score.data = ia;
		score_pub.publish(score);
		
		// p =	strstr(buff,"\"score");
		// printf("\n\p result = %s\n\n", p);
	    // p = strtok(buff,",");
		// printf("\n\p result = %s\n\n", p);

		//printf("\n %s\n", typeid(info).name());
		g_is_awaken_succeed = true;
    	record_state = MSP_AUDIO_SAMPLE_LAST;  //检测成功后，将该段设为唤醒音频结尾块
	}
	int ret = stop_record(recorder);  //唤醒成功后暂时关闭录音
	if (ret != 0) {
		printf("Stop failed! \n");
	}else{
		printf("stop success\n");
	}
	return 0;
}

//语音唤醒主要功能函数
void run_ivw(const char *grammar_list, const char* audio_filename ,  const char* session_begin_params)
{
	const char *session_id = NULL;
	int err_code = MSP_SUCCESS;
	char sse_hints[128];
	long len = 10*FRAME_LEN; //16k音频，10帧 （时长200ms）
	WAVEFORMATEX wavfmt = DEFAULT_FORMAT;
	//开始注册语音唤醒服务
	session_id=QIVWSessionBegin(grammar_list, session_begin_params, &err_code);
	if (err_code != MSP_SUCCESS)
	{
		printf("QIVWSessionBegin failed! error code:%d\n",err_code);
		goto exit;
	}
	//注册回调函数cb_ivw_msg_proc，唤醒结果将在此回调中返回
	err_code = QIVWRegisterNotify(session_id, cb_ivw_msg_proc,NULL);
	if (err_code != MSP_SUCCESS)
	{
		snprintf(sse_hints, sizeof(sse_hints), "QIVWRegisterNotify errorCode=%d", err_code);
		printf("QIVWRegisterNotify failed! error code:%d\n",err_code);
		goto exit;
	}
	//创建一个音频流，设置回调函数为iat_cb
	err_code = create_recorder(&recorder, iat_cb, (void*)session_id);
	if (recorder == NULL || err_code != 0) {
			printf("create recorder failed: %d\n", err_code);
			err_code = -E_SR_RECORDFAIL;
			goto exit;
	}

	//打开录音
	err_code = open_recorder(recorder, get_default_input_dev(), &wavfmt);
	if (err_code != 0) {
		printf("recorder open failed: %d\n", err_code);
		err_code = -E_SR_RECORDFAIL;
		goto exit;
	}
	//启动录音
	err_code = start_record(recorder);
	if (err_code != 0) {
		printf("start record failed: %d\n", err_code);
		err_code = -E_SR_RECORDFAIL;
		goto exit;
	}
	record_state = MSP_AUDIO_SAMPLE_FIRST;  //准备开始语音唤醒
	//等待说话，循环进入录音回调函数
	while(record_state != MSP_AUDIO_SAMPLE_LAST)
	{
		if(!normal_state_flag)
		{
			goto exit;
		}
		sleep_ms(200); //模拟人说话时间间隙，10帧的音频时长为200ms
		//printf("waiting for awaken%d\n", record_state);
	}
	snprintf(sse_hints, sizeof(sse_hints), "success");

exit:
	if (recorder) {
		if(!is_record_stopped(recorder))
			stop_record(recorder);
		close_recorder(recorder);
		destroy_recorder(recorder);
		recorder = NULL;
	}
	if (NULL != session_id)
	{
		QIVWSessionEnd(session_id, sse_hints);
	}
}


int main(int argc, char* argv[])
{
	int         ret       = MSP_SUCCESS;
	ros::init(argc, argv, "castlex_awake_node");    //初始化节点，向节点管理器注册
	ros::NodeHandle n;
	ros::Publisher pub = n.advertise<std_msgs::Int32>("/voice/castlex_awake_topic", 1);
	 score_pub = n.advertise<std_msgs::Int32>("/voice/awake_score", 1);

	/*
	下面时使用ros::package::getPath函数获取功能包的绝对路径
	使用方法及注意：
	1.#include"ros/package.h"
	2.string path = ros::package::getPath("xf_awake");
	3.在package那里加上：<depend>roslib</depend>
	4.在CmakeLists里的依赖里加上：roslib
	*/
	ros::NodeHandle nh("~");    //用于launch文件传递参数

	nh.param("response", response, std::string("./res/music/wozai.wav"));    //从launch文件获取参数
	nh.param("ssb_param_path", ssb_param_path, std::string("./res/ivw/wakeupresource.jet"));    //从launch文件获取参数

	//ros::NodeHandle nh("~");    //用于launch文件传递参数
	nh.param("lgi_param", my_lgi_param, std::string("appid = 551d49a3,work_dir = ."));    //从launch文件获取参数
	nh.param("audio_file_path", audio_file_path, std::string("./bin/audio/awake.wav"));    //从launch文件获取参数

	// string bingo_music_path = "/res/music/" + my_response;
	string bingo_music_path = string("play ") + response;

	//下面将获取ssb_param中唤醒模型文件的路径
	string path1 = "ivw_threshold=0:1450,sst=wakeup,ivw_res_path =fo|";
	// string path2 = ros::package::getPath("castlex_voice_system");

	//printf(path.data());
	// string path3 = "/res/ivw/wakeupresource.jet";
	string my_ssb_param = path1 + ssb_param_path;

	string path4 = audio_file_path;
	const char *IVW_AUDIO_FILE_NAME = path4.data(); //XML文件地址

	const char *lgi_param = my_lgi_param.data();
	const char *ssb_param = my_ssb_param.data();

	ret = MSPLogin(NULL, NULL, lgi_param);
	if (MSP_SUCCESS != ret)
	{
		printf("MSPLogin failed, error code: %d.\n", ret);
		goto exit ;//登录失败，退出登录
	}
	
	while(ros::ok())
	{
		run_ivw(NULL, IVW_AUDIO_FILE_NAME, ssb_param); 
		if(g_is_awaken_succeed)
		{
			g_is_awaken_succeed = false;
			std_msgs::Int32 msg;
			system(bingo_music_path.data());
			msg.data = 1;    //将返回文本写入消息，发布到topic上
			pub.publish(msg);
		}
		sleep_ms(1000);
	}
exit:
	MSPLogout(); //退出登录
	printf("---------------------------------------------------------------\n");
	printf("Turn off CastleX's voice wakeup feature.....\n");
	printf("---------------------------------------------------------------\n");
	return 0;
}
