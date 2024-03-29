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

#include "ros/package.h"

using namespace std;

#define FRAME_LEN	640 
#define	BUFFER_SIZE	4096
#define SAMPLE_RATE_16K     (16000)
#define SAMPLE_RATE_8K      (8000)
#define MAX_GRAMMARID_LEN   (32)
#define MAX_PARAMS_LEN      (1024)

bool record_flag = false; //VAD末尾端点检测标志
bool order_flag = false;
string result = "";
#define ASRCMD 1

const char ack[]={"play /home/castlex/castlex_ws/src/castlex_voice_system/res/music/haode.wav"};
const char notack[]={"play /home/castlex/castlex_ws/src/castlex_voice_system/res/music/haode.wav"};

string temp_path;
string pkg_path = ros::package::getPath("castlex_voice_system");
string fo_("fo|");
string RES_path("/home/castlex/.ws/castlex_voice_system/bin/msc/res/asr/common.jet");
string path1 = fo_+RES_path;
const char * ASR_RES_PATH        = path1.data(); //离线语法识别资源路径
string BUILD_path("/home/castlex/.ws/castlex_voice_system/bin/msc/res/asr/GrmBuilld");
string path2 = BUILD_path;
const char * GRM_BUILD_PATH      = path2.data(); //构建离线语法识别网络生成数据保存路径
string FILE_path("/home/castlex/.ws/castlex_voice_system/bin/bnf/robot_iot.bnf");
string path3 = FILE_path;
const char * GRM_FILE = path3.data(); //构建离线识别语法网络所用的语法文件
const char * LEX_NAME            = "contact"; //更新离线识别语法的contact槽（语法文件为此示例中使用的call.bnf）

typedef struct _UserData {
	int     build_fini; //标识语法构建是否完成
	int     update_fini; //标识更新词典是否完成
	int     errcode; //记录语法构建或更新词典回调错误码
	char    grammar_id[MAX_GRAMMARID_LEN]; //保存语法构建返回的语法ID
}UserData;

int build_grammar(UserData *udata); //构建离线识别语法网络
int run_asr(UserData *udata); //进行离线语法识别


ros::Publisher light_pub;
ros::Publisher trashcan_pub;
ros::Publisher cmd_pub;
ros::Publisher door_pub;
ros::Publisher trashcan_reset_pub;


struct order_id_t
{
	int confidence;
	int action;
	int iot;

}order_id;

static int led_state = 0x00;

int build_grm_cb(int ecode, const char *info, void *udata)
{
	UserData *grm_data = (UserData *)udata;

	if (NULL != grm_data) {
		grm_data->build_fini = 1;
		grm_data->errcode = ecode;
	}

	if (MSP_SUCCESS == ecode && NULL != info) {
		printf("构建语法成功！ 语法ID:%s\n", info);
		if (NULL != grm_data)
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

	grm_file = fopen(GRM_FILE, "rb");	
	if(NULL == grm_file) {
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

int my_atoi(char *src)
{
	char *p = src;
	int num = 0;
	int index = 0;

	if(src == NULL)
		return -1;

	while(*p++ != '\0')
	{
		if(*p<'0' || *p>'9')
		if(index)	break;
		else		continue;
		
		index = 1;
		num = num*10 + (*p - '0');
	
	}	


	return num;

}


static void show_result(char *str, char is_over)
{
	char *pos = NULL;
	std_msgs::Int32 cmd_msg;	

	if(is_over)
	{
		//printf("result-text:%s\n",str);

		pos = strstr(str,"<confidence>");
		if(pos != NULL)
			order_id.confidence = my_atoi(pos);	
		
		if(order_id.confidence<40) return;

		pos = strstr(str,"action id="); 
		
		if(pos != NULL)
			order_id.action = my_atoi(pos);		
		
		//printf("action-text:%s\n",pos);
		pos = strstr(str,"iot id"); 
	
		if(pos != NULL)
			order_id.iot = my_atoi(pos);
		//printf("grade-text:%s\n",pos);

		//printf("action:%d iot:%d\n",order_id.action,order_id.iot);

		if(order_id.action==0 && order_id.iot == 0)
		{
	                led_state &= ~(1<<0); 		
      			cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：关卧室灯***********\n");
		}
		else if(order_id.action==0 && order_id.iot == 1)
		{
			cmd_msg.data = 0;		
			trashcan_pub.publish(cmd_msg);
			printf("***********收到命令：关窗帘***********\n");


		}
		else if(order_id.action==1 && order_id.iot == 0)
		{
			led_state |= (1<<0); 			
			cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：开卧室灯***********\n");
		}
		else if(order_id.action==1 && order_id.iot == 1)
		{
			cmd_msg.data = 1;		
			trashcan_pub.publish(cmd_msg);
			printf("***********收到命令：开窗帘***********\n");

		}
//
		else if(order_id.action==0 && order_id.iot == 2)
		{
			led_state &= ~(1<<1);
                        cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：关走廊灯***********\n");

		}
		else if(order_id.action==1 && order_id.iot == 2)
		{
                        led_state |= (1<<1);
			cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：开走廊灯***********\n");

		}
		else if(order_id.action==0 && order_id.iot == 3)
		{
			led_state &= ~(1<<2);		
			cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：关房门灯***********\n");

		}
		else if(order_id.action==1 && order_id.iot == 3)
		{
			led_state |= (1<<2);
			cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：开房门灯***********\n");

		}

		else if(order_id.action==2 && order_id.iot == 4)
		{
			cmd_msg.data = 1;		
			door_pub.publish(cmd_msg);
			printf("***********收到命令：一号客房门铃***********\n");

		}
		else if(order_id.action==2 && order_id.iot == 5)
		{
			cmd_msg.data = 2;
			door_pub.publish(cmd_msg);		
			printf("***********收到命令：二号客房门铃***********\n");

		}
		else if(order_id.action==0 && order_id.iot == 6)
		{
			led_state = 0;
			cmd_msg.data = led_state;		
			light_pub.publish(cmd_msg);
			printf("***********收到命令：关所有灯***********\n");

		}
		else if(order_id.action==1 && order_id.iot == 6)
		{
			led_state = 7;
			cmd_msg.data = led_state;		//开所有灯
			light_pub.publish(cmd_msg);
			printf("***********收到命令：开所有灯***********\n");

		}
		else{
			printf("***********我没听清楚哦***********\n");
		return;
               } 
			
		system(ack);
		result = string(str);
		
		order_flag = true;
	
	}
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
	if (reason == END_REASON_VAD_DETECT){
		printf("\nSpeaking done \n");
		record_flag = true; //标志位置1,检测到VAD
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
	while(!record_flag && i++ < 15)  //检测到VAD或录音超过15秒则跳出循环
	{
		sleep(1);
		i++;
	}
	record_flag = false; //复位VAD检测标志位
	errcode = sr_stop_listening(&iat);
	if (errcode) {
		printf("stop listening failed %d\n", errcode);
	}
	sr_uninit(&iat);
}

int run_asr(UserData *udata)
{
	char asr_params[MAX_PARAMS_LEN]    = {NULL};
	const char *rec_rslt               = NULL;
	const char *session_id             = NULL;
	const char *asr_audiof             = NULL;
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
	demo_mic(asr_params);
	return 0;
}

int iatalk()
{
	const char *login_config    = "appid = 551d49a3"; //登录参数
	UserData asr_data; 
	int ret                     = 0 ;
	char c;
	ret = MSPLogin(NULL, NULL, login_config); //第一个参数为用户名，第二个参数为密码，传NULL即可，第三个参数是登录参数
	if (MSP_SUCCESS != ret) {
		printf("登录失败：%d\n", ret);
		goto exit_0;
	}
	memset(&asr_data, 0, sizeof(UserData));
	printf("构建离线识别语法网络...\n");
	ret = build_grammar(&asr_data);  //第一次使用某语法进行识别，需要先构建语法网络，获取语法ID，之后使用此语法进行识别，无需再次构建
	if (MSP_SUCCESS != ret) {
		printf("构建语法调用失败！\n");
		goto exit_0;
	}
	while (1 != asr_data.build_fini)
		usleep(300 * 1000);
	if (MSP_SUCCESS != asr_data.errcode)
		goto exit_0;
	printf("离线识别语法网络构建完成，开始识别...\n");	
	ret = run_asr(&asr_data);
	if (MSP_SUCCESS != ret) {
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
		iatalk();
	}
}



int main(int argc, char* argv[])
{
	//printf(path1.data());
	ros::init(argc, argv, "iot_order_node");    //初始化节点，向节点管理器注册
	ros::NodeHandle n;
	ros::Subscriber sub = n.subscribe("/voice/castlex_awake_topic", 1, orderCallback);

	ros::NodeHandle nh("~");    //用于launch文件传递参数
	//nh.param<int>("trashcan_state", trashcan_state, 0);    //从launch文件获取参数
	//nh.param("speech_param", speech_param, std::string("sub = iat, domain = iat, language = zh_cn, accent = mandarin, sample_rate = 16000, result_type = plain, result_encoding = utf8"));
	//printf("%s\n", appid);    //不支持UTF-8，因此终端打印出来是乱码

	 light_pub = n.advertise<std_msgs::Int32>("/Lighting_CMD_Topic", 1);		// 发布离线命令词识别结果话题
	 trashcan_pub = n.advertise<std_msgs::Int32>("/Trashcan_CMD_Topic", 1);		// 发布离线命令词识别结果话题

	 cmd_pub = n.advertise<std_msgs::Int32>("/voice/iot_state_topic", 1);	//识别离线命令词成功的flag话题
	 trashcan_reset_pub = n.advertise<std_msgs::Int32>("/Trashcan_RESET_Topic", 1);
         door_pub = n.advertise<std_msgs::Int32>("/Door_CMD_Topic", 1);

	std_msgs::Int32 reset;
	reset.data = 1;
	trashcan_reset_pub.publish(reset);
	ros::Rate loop_rate(10);    //10Hz循环周期
	while(ros::ok())
	{
		if(order_flag)
		{
			std_msgs::Int32 cmd_msg;
			cmd_msg.data = 1;
			cmd_pub.publish(cmd_msg);
			record_flag = false; 	//录音完成
			order_flag = false;
		}
		loop_rate.sleep();
		ros::spinOnce();
	}

	return 0;
}
