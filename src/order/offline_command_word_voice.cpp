/*
* 语音听写(iFly Auto Transform)技术能够实时地将语音转换成对应的文字。
*/
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>

#include "qisr.h"
#include "msp_cmn.h"
#include "msp_errors.h"
#include "speech_recognizer.h"

#include "ros/ros.h"
#include "std_msgs/Int32.h"
#include "std_msgs/String.h"
#include <typeinfo> 
#include <iostream>

#include "ros/package.h"

using namespace std;

#define FRAME_LEN	640 
#define	BUFFER_SIZE	4096
#define SAMPLE_RATE_48K     (48000)
#define SAMPLE_RATE_16K     (16000)
#define SAMPLE_RATE_8K      (8000)
#define MAX_GRAMMARID_LEN   (32)
#define MAX_PARAMS_LEN      (1024)

bool record_flag = false; //VAD末尾端点检测标志
bool order_flag = false;
string result = "";
#define ASRCMD 1

//	new add
string appid;    //用于获取launch传递函数
string FILE_path;    //用于获取launch传递函数
string RES_path;    //用于获取launch传递函数
string BUILD_path;    //用于获取launch传递函数
string xml_path;    //用于获取launch传递函数

string voice1_path;    // 去中转台
string voice2_path;    // 回原点
string voice3_path;    // 去立体仓库
string voice4_path;    // 去中转台抓取物料
string voice5_path;    // 去立体仓库放置物料
string voice6_path;    // 去装配台放置物料
string voice7_path;    // 去装配台

string temp_path;
string pkg_path = ros::package::getPath("castlex_voice_system");
string fo_("fo|");

const char * LEX_NAME            = "contact"; //更新离线识别语法的contact槽（语法文件为此示例中使用的call.bnf）

typedef struct _UserData {
	int     build_fini; //标识语法构建是否完成
	int     update_fini; //标识更新词典是否完成
	int     errcode; //记录语法构建或更新词典回调错误码
	char    grammar_id[MAX_GRAMMARID_LEN]; //保存语法构建返回的语法ID
}UserData;

int get_audio_file(); //选择进行离线语法识别的语音文件

int build_grammar(UserData *udata); //构建离线识别语法网络
int run_asr(UserData *udata); //进行离线语法识别

// 音频选择函数
int get_audio_file()
{
	int key = 0;
	while (~key)
	{
		key = getchar();
		switch(key)
		{
			case 49:
				// printf("\n1.去物料台/中转台\n");
				return 49;
			case 50:
				// printf("\n2.回原点\n");
				return 50;
			case 51:
				// printf("\n3.去立体仓库\n");
				return 51;
			case 52:
				// printf("\n4.去中转台放置物料\n");
				return 52;
			case 53:
				// printf("\n5.去立体仓库放置物料\n");
				return 53;
			case 54:
				// printf("\n6.去装配台放置物料\n");
				return 54;
			case 55:
				// printf("\n7.去装配台\n");
				return 55;
			default:
				break;
		}
	}
}


//将识别结果写入XML文件
void write_data_to_file(const char *path, char *str)
{
	FILE *fd = fopen(path, "a+");
	if (fd == NULL) 
	{
		printf("fd is NULL and open file fail\n");
		return;
	}
/*	printf("fd != NULL\n");
*/	if (str && str[0] != 0) 
	{
		fwrite(str, strlen(str), 1, fd);
		char *next = "\n";
		fwrite(next, strlen(next), 1, fd);
	}
	fclose(fd);
}

//清空XML文件内容
void clear_file_data(const char *path)
{
	FILE *fd = fopen(path, "w");//用写方式打开，然后关闭文件即可。
	fclose(fd);
}

int build_grm_cb(int ecode, const char *info, void *udata)
{
	UserData *grm_data = (UserData *)udata;

	if (NULL != grm_data) 
	{
		grm_data->build_fini = 1;
		grm_data->errcode = ecode;
	}

	if (MSP_SUCCESS == ecode && NULL != info) 
	{
		printf("构建语法成功！ 语法ID:%s\n", info);
		if (NULL != grm_data)
			// snprintf(grm_data->grammar_id, MAX_GRAMMARID_LEN - 1, info);
			snprintf(grm_data->grammar_id, MAX_GRAMMARID_LEN - 1, "%s", info);

	}
	else
		printf("构建语法失败！%d\n", ecode);

	return 0;
}

int build_grammar(UserData *udata)
{
	FILE *grm_file                           = NULL;
	char *grm_content                        = NULL;
	unsigned int grm_cnt_len                 = 0;
	char grm_build_params[MAX_PARAMS_LEN]    = {NULL};
	int ret                                  = 0;

	// new add
	string path3 = FILE_path;
	const char * GRM_FILE = path3.data(); //构建离线识别语法网络所用的语法文件
	string path1 = fo_+RES_path;
	const char * ASR_RES_PATH    = path1.data(); //离线语法识别资源路径
	string path2 = BUILD_path;
	const char * GRM_BUILD_PATH      = path2.data(); //构建离线语法识别网络生成数据保存路径

	grm_file = fopen(GRM_FILE, "rb");	
	if(NULL == grm_file) 
	{
		printf("打开\"%s\"文件失败！[%s]\n", GRM_FILE, strerror(errno));
		return -1; 
	}

	fseek(grm_file, 0, SEEK_END);
	grm_cnt_len = ftell(grm_file);
	fseek(grm_file, 0, SEEK_SET);

	grm_content = (char *)malloc(grm_cnt_len + 1);
	if (NULL == grm_content)
	{
		printf("内存分配失败!\n");
		fclose(grm_file);
		grm_file = NULL;
		return -1;
	}
	fread((void*)grm_content, 1, grm_cnt_len, grm_file);
	grm_content[grm_cnt_len] = '\0';
	fclose(grm_file);
	grm_file = NULL;

	snprintf(grm_build_params, MAX_PARAMS_LEN - 1, 
		"engine_type = local, \
		asr_res_path = %s, sample_rate = %d, \
		grm_build_path = %s, ",
		ASR_RES_PATH,
		SAMPLE_RATE_16K,
		GRM_BUILD_PATH
		);
	ret = QISRBuildGrammar("bnf", grm_content, grm_cnt_len, grm_build_params, build_grm_cb, udata);

	free(grm_content);
	grm_content = NULL;

	return ret;
}

static void show_result(char *str, char is_over)
{
/*	printf("\rResult: [ \n%s ]", str);
*/
	// new add
	string path4 = xml_path;
	const char *path = path4.data(); //XML文件地址

	clear_file_data(path);
	write_data_to_file(path, str);  //将识别结果写入XML
	string s(str);
	result = s;
	if(is_over)
		putchar('\n');
	order_flag = true;
}

static char *g_result = NULL;
static unsigned int g_buffersize = BUFFER_SIZE;

void on_result(const char *result, char is_last)
{
	if (result) {
		size_t left = g_buffersize - 1 - strlen(g_result);
		size_t size = strlen(result);
		if (left < size) 
		{
			g_result = (char*)realloc(g_result, g_buffersize + BUFFER_SIZE);
			if (g_result)
				g_buffersize += BUFFER_SIZE;
			else 
			{
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
		record_flag = true; //标志位置1,检测到VAD
	}
	else
		printf("\nRecognizer error %d\n", reason);
}

/* demo send audio data from a file */
static void demo_file(const char* audio_file, const char* session_begin_params)
{
	int	errcode = 0;
	FILE*	f_pcm = NULL;
	char*	p_pcm = NULL;
	unsigned long	pcm_count = 0;
	unsigned long	pcm_size = 0;
	unsigned long	read_size = 0;
	struct speech_rec iat;
	struct speech_rec_notifier recnotifier = {
		on_result,
		on_speech_begin,
		on_speech_end
	};

	// printf("\nRecognizer error %s\n", audio_file);

	if (NULL == audio_file)
		goto iat_exit;

	f_pcm = fopen(audio_file, "rb");
	if (NULL == f_pcm)
	{
		printf("\nopen [%s] failed! \n", audio_file);
		goto iat_exit;
	}

	fseek(f_pcm, 0, SEEK_END);
	pcm_size = ftell(f_pcm);
	fseek(f_pcm, 0, SEEK_SET);

	p_pcm = (char *)malloc(pcm_size);
	if (NULL == p_pcm)
	{
		printf("\nout of memory! \n");
		goto iat_exit;
	}

	read_size = fread((void *)p_pcm, 1, pcm_size, f_pcm);
	if (read_size != pcm_size)
	{
		printf("\nread [%s] error!\n", audio_file);
		goto iat_exit;
	}

	errcode = sr_init(&iat, session_begin_params, SR_USER, &recnotifier);
	if (errcode) 
	{
		printf("speech recognizer init failed : %d\n", errcode);
		goto iat_exit;
	}

	errcode = sr_start_listening(&iat);
	if (errcode) 
	{
		printf("\nsr_start_listening failed! error code:%d\n", errcode);
		goto iat_exit;
	}

	while (1)
	{
		unsigned int len = 10 * FRAME_LEN; /* 200ms audio */
		int ret = 0;

		if (pcm_size < 2 * len)
			len = pcm_size;
		if (len <= 0)
			break;

		ret = sr_write_audio_data(&iat, &p_pcm[pcm_count], len);

		if (0 != ret)
		{
			printf("\nwrite audio data failed! error code:%d\n", ret);
			goto iat_exit;
		}

		pcm_count += (long)len;
		pcm_size -= (long)len;		
	}

	errcode = sr_stop_listening(&iat);
	if (errcode) 
	{
		printf("\nsr_stop_listening failed! error code:%d \n", errcode);
		goto iat_exit;
	}

iat_exit:
	if (NULL != f_pcm)
	{
		fclose(f_pcm);
		f_pcm = NULL;
	}
	if (NULL != p_pcm)
	{
		free(p_pcm);
		p_pcm = NULL;
	}

	sr_stop_listening(&iat);
	sr_uninit(&iat);
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
	if (errcode) 
	{
		printf("speech recognizer init failed\n");
		return;
	}
	errcode = sr_start_listening(&iat);
	if (errcode) 
	{
		printf("start listen failed %d\n", errcode);
	}
	/* demo 15 seconds recording */
	while(!record_flag && i++ < 15)  //检测到VAD或录音超过15秒则跳出循环
	{
		sleep(1);
		i++;
	}
	record_flag = false; //复位VAD检测标志位
	errcode = sr_stop_listening(&iat);
	if (errcode) 
	{
		printf("stop listening failed %d\n", errcode);
	}
	sr_uninit(&iat);
}

int run_asr(UserData *udata)
{
	char asr_params[MAX_PARAMS_LEN]    = {NULL};
	const char *rec_rslt               = NULL;
	const char *session_id             = NULL;
	int asr_audiof = -1;
	FILE *f_pcm                        = NULL;
	char *pcm_data                     = NULL;
	long pcm_count                     = 0;
	long pcm_size                      = 0;
	int last_audio                     = 0;

	int aud_stat                       = MSP_AUDIO_SAMPLE_CONTINUE;
	int ep_status                      = MSP_EP_LOOKING_FOR_SPEECH;
	int rec_status                     = MSP_REC_STATUS_INCOMPLETE;
	int rss_status                     = MSP_REC_STATUS_INCOMPLETE;
	int errcode                        = -1;
	int aud_src                        = 10;

	// 离线命令词资源
	string path1 = fo_+ RES_path;
	const char * ASR_RES_PATH        = path1.data(); //离线语法识别资源路径
	string path2 = BUILD_path;
	const char * GRM_BUILD_PATH      = path2.data(); //构建离线语法识别网络生成数据保存路径

	// 从launch文件获取识别音频文件
	string nav1_path = voice1_path;
	const char * nav1_data = nav1_path.data(); // 去中转台音频
	string nav2_path = voice2_path;
	const char * nav2_data = nav2_path.data(); // 回原点音频
	string nav3_path = voice3_path;
	const char * nav3_data = nav3_path.data(); // 去立体仓库音频
	string nav4_path = voice4_path;
	const char * nav4_data = nav4_path.data(); // 去中转台抓取物料音频
	string nav5_path = voice5_path;
	const char * nav5_data = nav5_path.data(); // 去立体仓库放置物料音频
	string nav6_path = voice6_path;
	const char * nav6_data = nav6_path.data(); // 去装配台放置物料音频
	string nav7_path = voice7_path;
	const char * nav7_data = nav7_path.data(); // 去装配台音频

	//离线语法识别参数设置
	snprintf(asr_params, MAX_PARAMS_LEN - 1, 
		"engine_type = local, \
		asr_res_path = %s, sample_rate = %d, \
		grm_build_path = %s, local_grammar = %s, \
		result_type = xml, result_encoding = UTF-8, ",
		ASR_RES_PATH,
		SAMPLE_RATE_16K,
		GRM_BUILD_PATH,
		udata->grammar_id
		);

		printf("音频数据在哪? \n0: 从文件读入\n1:从MIC说话\n");
		while(aud_src == 10)
		{
			// 获取键盘输入
			aud_src = getchar();

			if (aud_src == 48)
			{
				printf("请选择音频文件：\n");
				printf("1.去物料台/中转台\n");
				printf("2.回原点\n");
				printf("3.去立体仓库\n");
				printf("4.去中转台抓取物料\n");
				printf("5.去立体仓库放置物料\n");
				printf("6.去装配台放置物料\n");
				printf("7.去装配台\n");

				// 选择音频
				asr_audiof = get_audio_file();
				switch(asr_audiof)
				{
					case 49:
						// 播放去装配台音频
						demo_file(nav1_data, asr_params); 
						break;
					case 50:
						// 播放回原点音频
						demo_file(nav2_data, asr_params); 
						break;
					case 51:
						// 播放去立体仓库音频
						demo_file(nav3_data, asr_params); 
						break;		
					case 52:
						// 播放去中转台抓取物料音频
						demo_file(nav4_data, asr_params); 
						break;
					case 53:
						// 播放去立体仓库放置物料音频
						demo_file(nav5_data, asr_params); 
						break;
					case 54:
						// 播放去装配台放置物料音频
						demo_file(nav6_data, asr_params); 
						break;
					case 55:
						// 播放去装配台音频
						demo_file(nav7_data, asr_params); 
						break;

					default:
						break;				
				}
			}

			else if (aud_src == 49)
			{
				demo_mic(asr_params);	
			}
		}
	return 0;
}

int iatalk()
{
	// const char *login_config    = "appid = 551d49a3"; //登录参数
	const char *login_config    =  appid.data(); //"appid = 5ddb3b02"; //登录参数

	UserData asr_data; 
	int ret                     = 0 ;
	char c;
	ret = MSPLogin(NULL, NULL, login_config); //第一个参数为用户名，第二个参数为密码，传NULL即可，第三个参数是登录参数
	if (MSP_SUCCESS != ret) 
	{
		printf("登录失败：%d\n", ret);
		goto exit_0;
	}
	memset(&asr_data, 0, sizeof(UserData));
	printf("构建离线识别语法网络...\n");
	ret = build_grammar(&asr_data);  //第一次使用某语法进行识别，需要先构建语法网络，获取语法ID，之后使用此语法进行识别，无需再次构建
	if (MSP_SUCCESS != ret) 
	{
		printf("构建语法调用失败！\n");
		goto exit_0;
	}
	while (1 != asr_data.build_fini)
		usleep(300 * 1000);
	if (MSP_SUCCESS != asr_data.errcode)
		goto exit_0;
	printf("离线识别语法网络构建完成，开始识别...\n");	
	ret = run_asr(&asr_data);
	if (MSP_SUCCESS != ret) 
	{
		printf("离线语法识别出错: %d \n", ret);
		goto exit_0;
	}
	else{
		goto exit_1;
	}
exit_0:
	MSPLogout();
	printf("命令词识别失败...\n");
	return 0;
exit_1:
	MSPLogout();
	printf("命令词识别成功...\n");
	return 1;
}

void orderCallback(const std_msgs::Int32::ConstPtr& msg)
{
	ROS_INFO_STREAM("you are speaking...");
	if(msg->data == ASRCMD)
	{
		// iatalk();
	}
}

int main(int argc, char* argv[])
{
	// printf(path1.data());
	ros::init(argc, argv, "castlex_offline_command_voice_node");    //初始化节点，向节点管理器注册
	ros::NodeHandle n;
	ros::Subscriber sub = n.subscribe("/voice/castlex_awake_topic", 1, orderCallback);

	ros::NodeHandle nh("~");    //用于launch文件传递参数

	// new add
	nh.param("appid", appid, std::string("appid = 5b6d44e, work_dir = ."));    //从launch文件获取appid参数
	nh.param("FILE_path", FILE_path, std::string("/bin/bnf/voice_nav.bnf"));    //从launch文件获取参数
	nh.param("RES_path", RES_path, std::string("/bin/msc/res/asr/common.jet"));    //从launch文件获取参数
	nh.param("BUILD_path", BUILD_path, std::string("/bin/msc/res/asr/GrmBuilld"));    //从launch文件获取参数
	nh.param("xml_path", xml_path, std::string("/params/voiceNav.xml"));    //从launch文件获取参数

	nh.param("voice1_path", voice1_path, std::string("/bin/bnf/wav/zzt.wav"));    // 去中转台
	nh.param("voice2_path", voice2_path, std::string("/bin/bnf/wav/yd.wav"));    // 回原点
	nh.param("voice3_path", voice3_path, std::string("/bin/bnf/wav/ltck.wav"));    // 去立体仓库
	nh.param("voice4_path", voice4_path, std::string("/bin/bnf/wav/ltck.wav"));    // 去中转台抓取物料
	nh.param("voice5_path", voice5_path, std::string("/bin/bnf/wav/ltck.wav"));    // 去立体仓库放置物料
	nh.param("voice6_path", voice6_path, std::string("/bin/bnf/wav/ltck.wav"));    // 去装配台放置物料
	nh.param("voice7_path", voice7_path, std::string("/bin/bnf/wav/ltck.wav"));    // 去装配台


	ros::Publisher pub = n.advertise<std_msgs::String>("/voice/castlex_order_topic", 3);	// 发布离线命令词识别结果话题
	ros::Publisher cmd_pub = n.advertise<std_msgs::Int32>("/voice/castlex_cmd_topic", 1);	//	识别离线命令词成功的flag话题

	ros::Rate loop_rate(10);    //10Hz循环周期
	// iatalk();
	while(ros::ok())
	{
		if(order_flag)
		{
			std_msgs::String msg;
			msg.data = result;    //将asr返回文本写入消息，发布到topic上
			pub.publish(msg);	//	发布话题
			order_flag = false; 
			record_flag = false; //录音完成
			std_msgs::Int32 cmd_msg;
			cmd_msg.data = 1;
			cmd_pub.publish(cmd_msg);
			// order_flag = false;
		}
		else
		{
			iatalk();
		}
		loop_rate.sleep();
		ros::spinOnce();
	}

	return 0;
}
